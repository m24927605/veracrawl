"""Playwright browser observation adapter.

This adapter does NOT implement WAF evasion, stealth automation, or
ban-avoidance fingerprint patches. Per ``docs/09-target-capability-model.md``
§Safety Boundary, VeraCrawl is an authorized-source crawler; sites that
serve only via human verification, CAPTCHA, or bot-detection challenges
must be reached through their official APIs or authorized sessions, not
by impersonating a human browser. Stealth init-scripts shipped earlier
in this branch (navigator.webdriver / plugins / languages / chrome.runtime
/ Permissions API patches) were removed in the same change that added
this docstring; bringing them back without a charter amendment would
violate the safety boundary.

What this adapter DOES configure for **stable rendering under
authorized access**:

- A real Chrome user-agent (configurable via ``user_agent``) so the
  rendering pipeline matches the same HTML / CSS / JS path a human
  Chrome user gets — required for deterministic DOM snapshots, not
  for bot evasion.
- ``locale="en-US"`` plus ``Accept-Language: en-US,en;q=0.9`` so
  locale-dependent rendering is deterministic across runs.
- Wait strategy: ``wait_until="domcontentloaded"`` (was ``"load"``,
  which on SPA pages sat blocking on tracking pixels that never
  resolved) plus a configurable ``post_load_idle_ms``.

Phase 1 step 1.1 adds session lifecycle so multiple navigations
within a single run reuse one ``BrowserContext`` — cookies / local
storage / session state survive across page-to-page navigation —
and the run's accumulated state persists to disk as
``storage_state.json`` keyed by ``run_ref``. The standalone
``observe()`` and ``execute()`` paths remain backwards-compatible:
each runs in a transient one-shot session that opens, navigates,
and closes the context inline.

Detection of bot-protection challenges (Cloudflare Turnstile,
DataDome, PerimeterX, etc.) is the access-control classifier's job
in a separate phase; this adapter surfaces such pages as a typed
``AccessControlBlocked`` failure rather than evading.

Playwright itself is still optional — it is loaded lazily inside
``_load_sync_playwright`` so the adapter module can be imported
without the ``browser-playwright`` extra installed. Tests inject a
mock factory via ``playwright_factory`` to exercise the adapter
end-to-end without a real Chromium install.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final

from veracrawl.contracts.browser import BrowserInteractionStep, BrowserSandboxPolicy
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    BrowserSideEffectClass,
    BrowserStepStatus,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.fetch.network_acquisition import url_origin
from veracrawl.ports.browser import BrowserObservationResult
from veracrawl.runtime_support.logging import get_logger

_DEFAULT_CHROME_UA: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_RUN_REF_SAFE_RE: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9_.-]+")
_STORAGE_STATE_FILE_MODE: Final[int] = 0o600  # owner read/write only

_logger = get_logger(__name__)


def _storage_state_filename(run_ref: str) -> str:
    """Map ``run_ref`` to a collision-resistant filesystem-safe name.

    Run refs use ``:`` separators (``run:abc-123``) and may carry
    other characters (``/``, ``?``, ``#``) that are filesystem-
    hostile or stream separators on Windows. A naive sanitizer
    (replace ``[^A-Za-z0-9_.-]+`` with ``_``) collides — ``run:a:b``
    and ``run:a/b`` both reduce to ``run_a_b`` — and a collision
    here would let one run hydrate from another run's
    ``storage_state.json`` (codex iter-1 critical).

    Use a SHA-256 digest of the raw ``run_ref`` as the
    collision-resistant suffix and keep the sanitized prefix only
    for human readability. Two distinct refs hash to distinct
    suffixes; the file lookup keys on the suffix, so cross-run
    contamination at the filename layer is impossible.
    """
    sanitized = _RUN_REF_SAFE_RE.sub("_", run_ref).strip("_") or "run"
    digest = hashlib.sha256(run_ref.encode("utf-8")).hexdigest()[:16]
    return f"{sanitized}.{digest}.storage_state.json"


class BrowserSession:
    """Long-lived browser context scoped to one run.

    Yielded by :meth:`PlaywrightBrowserObservationAdapter.open_session`.
    Reuse semantics: every ``observe()`` call within the session uses
    the same ``BrowserContext`` (cookies, local storage, and session
    state survive across navigations), so a multi-page crawl that
    relies on session state — login carry-over, CSRF tokens, OAuth
    refresh-token rotation — works the way the underlying site
    expects without manually re-establishing state per page.

    The session is single-threaded by design: pages are created
    sequentially, never in parallel, so route-handler counters and
    storage-state writes have no interleaving concerns.
    """

    def __init__(
        self,
        *,
        adapter: PlaywrightBrowserObservationAdapter,
        playwright_browser: Any,
        playwright_context: Any,
        run_ref: Ref,
    ) -> None:
        self._adapter = adapter
        self._browser = playwright_browser
        self._context = playwright_context
        self._run_ref = run_ref
        self._closed = False

    @property
    def run_ref(self) -> Ref:
        return self._run_ref

    @property
    def context(self) -> Any:
        """Underlying playwright BrowserContext.

        Exposed for tests that want to assert against the same
        object across multiple ``observe()`` calls (the design's
        BrowserContext-reuse acceptance).
        """
        return self._context

    def observe(
        self,
        *,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        """Navigate the session's existing context to ``target_url``.

        Uses :attr:`context` — does NOT create a new context — so the
        cookies and storage that prior navigations left on the
        context apply to this navigation and any new state this
        navigation produces is visible to subsequent ones.
        """
        if self._closed:
            raise RuntimeError("BrowserSession has been closed")
        return self._adapter._observe_on_context(
            context=self._context,
            run_ref=self._run_ref,
            source_ref=source_ref,
            target_url=target_url,
            sandbox_policy=sandbox_policy,
        )


class PlaywrightBrowserObservationAdapter:
    def __init__(
        self,
        *,
        fixture_id: str,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
        side_effect_class: BrowserSideEffectClass = BrowserSideEffectClass.READ_ONLY,
        wait_for_text_fragments: Sequence[str] = (),
        user_agent: str = _DEFAULT_CHROME_UA,
        wait_until: str = "domcontentloaded",
        post_load_idle_ms: int = 250,
        storage_state_dir: Path | None = None,
        playwright_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.fixture_id = fixture_id
        self.target_url = target_url
        self.sandbox_policy = sandbox_policy
        self.side_effect_class = side_effect_class
        self.wait_for_text_fragments = list(wait_for_text_fragments)
        self.user_agent = user_agent
        self.wait_until = wait_until
        self.post_load_idle_ms = post_load_idle_ms
        # Phase 1 step 1.1: per-run storage_state persistence directory.
        # ``None`` disables persistence (back-compat with one-shot
        # callers that do not declare a run-scoped storage location).
        self.storage_state_dir = storage_state_dir
        # Tests override the playwright entry point with a mock that
        # does not require a real Chromium install.
        self._playwright_factory: Callable[[], Any] = (
            playwright_factory if playwright_factory is not None else _load_sync_playwright
        )
        self._last_result: BrowserObservationResult | None = None

    @property
    def last_result(self) -> BrowserObservationResult | None:
        return self._last_result

    def _storage_state_path(self, run_ref: Ref) -> Path | None:
        """Resolve the per-run ``storage_state.json`` path or ``None``.

        Returns ``None`` when persistence is disabled (no
        ``storage_state_dir`` configured); callers treat ``None`` as
        "do not load and do not save".
        """
        if self.storage_state_dir is None:
            return None
        return self.storage_state_dir / _storage_state_filename(run_ref)

    def _new_context(self, browser: Any, *, storage_state_path: Path | None) -> Any:
        """Construct a ``BrowserContext`` with the rendering-stability
        config, optionally re-hydrated from a prior run's
        ``storage_state.json``.
        """
        context_kwargs: dict[str, Any] = {
            "java_script_enabled": True,
            "ignore_https_errors": False,
            "user_agent": self.user_agent,
            "locale": "en-US",
            "extra_http_headers": {"Accept-Language": "en-US,en;q=0.9"},
        }
        if storage_state_path is not None and storage_state_path.exists():
            context_kwargs["storage_state"] = str(storage_state_path)
        return browser.new_context(**context_kwargs)

    @contextmanager
    def open_session(self, *, run_ref: Ref) -> Iterator[BrowserSession]:
        """Open a long-lived browser session scoped to ``run_ref``.

        On entry: launches Chromium, creates one ``BrowserContext``
        (re-hydrated from a collision-resistant per-run file under
        ``storage_state_dir`` if persistence is enabled and a prior
        run's file exists).

        Yields a :class:`BrowserSession` whose ``observe()`` method
        reuses the same context across calls.

        On exit: persists the context's ``storage_state`` to disk
        (when ``storage_state_dir`` is configured), then closes the
        context and the browser. The persistence step runs inside
        its own ``try`` so a serialization or filesystem failure
        does not strand the open browser process — the cleanup
        block always runs (codex iter-1 important: cleanup must
        be unconditional).

        Per-run isolation is automatic because each run_ref maps
        to its own storage_state file via a SHA-256 digest of the
        ref; two runs with different run_refs will not see each
        other's cookies even if they share a ``storage_state_dir``.

        Privacy contract for the persisted file: ``storage_state``
        contains live cookies and origin storage that are sensitive
        by definition. The file is written with ``chmod 0600``
        (owner read/write only). Retention / cleanup of accumulated
        ``storage_state.json`` files is a Phase 6 ``ArtifactLifecycle``
        gate concern — this adapter writes the file and lets the
        operational lifecycle layer prune it. Callers that do not
        want persistence must pass ``storage_state_dir=None``
        (codex iter-1 important).
        """
        sync_playwright = self._playwright_factory()
        storage_state_path = self._storage_state_path(run_ref)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = self._new_context(browser, storage_state_path=storage_state_path)
            session = BrowserSession(
                adapter=self,
                playwright_browser=browser,
                playwright_context=context,
                run_ref=run_ref,
            )
            try:
                yield session
            finally:
                # Persistence is best-effort: a failure here must not
                # leak the browser process. Log and proceed to close.
                if storage_state_path is not None:
                    try:
                        self._write_storage_state(context, storage_state_path)
                    except Exception:  # noqa: BLE001
                        _logger.exception(
                            "browser_storage_state_persist_failed",
                            run_ref=run_ref,
                        )
                # Cleanup runs unconditionally. Each step is also
                # guarded so a failure in context.close() still gives
                # browser.close() a chance to run.
                try:
                    context.close()
                except Exception:  # noqa: BLE001
                    _logger.exception("browser_context_close_failed", run_ref=run_ref)
                try:
                    browser.close()
                except Exception:  # noqa: BLE001
                    _logger.exception("browser_close_failed", run_ref=run_ref)
                session._closed = True  # noqa: SLF001

    @staticmethod
    def _write_storage_state(context: Any, path: Path) -> None:
        """Persist ``context.storage_state`` to ``path`` with mode 0600.

        ``storage_state`` carries live cookies and origin storage —
        the file is sensitive and must not be world-readable. We
        ask Playwright to write the file (its native serializer is
        what produces the round-trippable JSON shape), then chmod
        the result to owner-only on POSIX. ``os.chmod`` is a no-op
        on systems that do not support POSIX modes, which is
        acceptable: those platforms get the filesystem default.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(path))
        try:
            os.chmod(path, _STORAGE_STATE_FILE_MODE)
        except OSError:
            # Non-POSIX filesystems / Windows ACL semantics: log and
            # accept the platform default rather than fail the whole
            # session over a permissions hardening step.
            _logger.debug("storage_state_chmod_unsupported", path=str(path))

    def observe(
        self,
        *,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        """One-shot navigation that opens a session of length 1.

        Backwards-compatible with the v0 single-call usage: every
        invocation launches a fresh browser, creates a context, runs
        the navigation, and closes everything before returning. Use
        :meth:`open_session` instead when multiple navigations should
        share a context.
        """
        with self.open_session(run_ref=run_ref) as session:
            return session.observe(
                source_ref=source_ref,
                target_url=target_url,
                sandbox_policy=sandbox_policy,
            )

    def _observe_on_context(
        self,
        *,
        context: Any,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        """Single navigation against an already-open BrowserContext."""
        started = time.monotonic()
        network_request_count = 0
        blocked_request_count = 0
        console_logs: list[str] = []

        def route_handler(route: Any) -> None:
            nonlocal network_request_count, blocked_request_count
            request_url = str(route.request.url)
            network_request_count += 1
            request_origin = url_origin(request_url)
            if request_origin not in sandbox_policy.egress_allowlist:
                blocked_request_count += 1
                route.abort()
                return
            route.continue_()

        context.route("**/*", route_handler)
        page = context.new_page()
        page.on("console", lambda message: console_logs.append(message.text))
        try:
            page.goto(
                target_url,
                wait_until=self.wait_until,
                timeout=sandbox_policy.max_runtime_ms,
            )
            for fragment in self.wait_for_text_fragments:
                page.wait_for_function(
                    "(fragment) => document.body && document.body.innerText.includes(fragment)",
                    arg=fragment,
                    timeout=sandbox_policy.max_runtime_ms,
                )
            if self.post_load_idle_ms > 0:
                page.wait_for_timeout(self.post_load_idle_ms)
            dom_html = page.content()
            try:
                dom_text = page.locator("body").inner_text(timeout=1000)
            except Exception:  # noqa: BLE001
                dom_text = dom_html
            screenshot = page.screenshot(full_page=True)
        finally:
            # Pages are session-scoped: closed after each observation
            # so the route handler does not stack across navigations.
            page.close()
            context.unroute("**/*", route_handler)

        wall_time_ms = max(1, int((time.monotonic() - started) * 1000))
        dom_digest = stable_hash({"url": target_url, "dom": dom_html, "text": dom_text})
        screenshot_digest = hashlib.sha256(screenshot).hexdigest()
        network_digest = stable_hash(
            {
                "url": target_url,
                "requests": network_request_count,
                "blocked": blocked_request_count,
            }
        )
        console_digest = stable_hash({"url": target_url, "console": console_logs})
        timing_digest = stable_hash({"url": target_url, "wall_time_ms": wall_time_ms})
        dom_ref = f"artifact:{self.fixture_id}:dom:{dom_digest[:12]}"
        screenshot_ref = f"artifact:{self.fixture_id}:screenshot:{screenshot_digest[:12]}"
        network_ref = f"artifact:{self.fixture_id}:browser-network:{network_digest[:12]}"
        console_ref = f"artifact:{self.fixture_id}:console:{console_digest[:12]}"
        timing_ref = f"artifact:{self.fixture_id}:timing:{timing_digest[:12]}"
        step = BrowserInteractionStep(
            id=f"browser-step:{self.fixture_id}:1",
            run_ref=run_ref,
            source_ref=source_ref,
            target_url=target_url,
            step_number=1,
            action_type="observe",
            side_effect_class=self.side_effect_class,
            sandbox_policy_ref=sandbox_policy.id,
            policy_decision_refs=[f"policy:{self.fixture_id}:browser"],
            dom_artifact_ref=dom_ref,
            screenshot_artifact_ref=screenshot_ref,
            network_log_ref=network_ref,
            status=BrowserStepStatus.EXECUTED,
        )
        return BrowserObservationResult(
            step=step,
            artifact_refs=[dom_ref, screenshot_ref, network_ref, console_ref, timing_ref],
            dom_text=dom_text,
            dom_content_hash=dom_digest,
            screenshot_byte_count=len(screenshot),
            network_request_count=network_request_count,
            blocked_request_count=blocked_request_count,
            console_log_count=len(console_logs),
            wall_time_ms=wall_time_ms,
        )

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        result = self.observe(
            run_ref=f"run:{self.fixture_id}",
            source_ref=command.source_ref,
            target_url=self.target_url,
            sandbox_policy=self.sandbox_policy,
        )
        self._last_result = result
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id=f"run:{self.fixture_id}",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.BROWSER_SNAPSHOT,
            result_type=SourceAdapterResultType.BROWSER_SNAPSHOT,
            output_refs=[result.step.dom_artifact_ref or result.artifact_refs[0]],
            policy_decision_refs=result.step.policy_decision_refs,
            replay_event_refs=[f"event:{command.command_envelope_id}:browser_step_executed"],
            idempotency_key=f"{command.adapter_spec.id}:{self.fixture_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def _load_sync_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for the live browser adapter; install the "
            "browser-playwright extra and run `python -m playwright install chromium`"
        ) from exc
    return sync_playwright
