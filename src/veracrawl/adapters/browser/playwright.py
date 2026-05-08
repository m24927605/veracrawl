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
import json
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
from veracrawl.ports.evidence_artifact_store import (
    ArtifactKind,
    EvidenceArtifactStorePort,
    NoopEvidenceArtifactStore,
)
from veracrawl.runtime_support.har_redaction import (
    HarRedactionError,
    redact_har_payload,
)
from veracrawl.runtime_support.logging import get_logger
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_DEFAULT_CHROME_UA: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

_RUN_REF_SAFE_RE: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9_.-]+")
_STORAGE_STATE_FILE_MODE: Final[int] = 0o600  # owner read/write only
# Cap the human-readable prefix so the resulting filename stays well
# inside POSIX ``NAME_MAX`` (255) and Windows ``MAX_PATH`` margins
# regardless of how long the caller's run_ref happens to be (codex
# iter-3 minor). The 16-hex-char SHA-256 digest is the collision-
# resistant key; the prefix is purely cosmetic.
_RUN_REF_PREFIX_MAX: Final[int] = 64

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
    for human readability. The prefix is truncated to
    ``_RUN_REF_PREFIX_MAX`` characters so externally-supplied long
    refs cannot push the filename past the filesystem's
    ``NAME_MAX`` limit (codex iter-3 minor — silent persistence
    failure at session close otherwise). Two distinct refs hash to
    distinct suffixes; the file lookup keys on the digest, so
    cross-run contamination at the filename layer is impossible.
    """
    sanitized = _RUN_REF_SAFE_RE.sub("_", run_ref).strip("_") or "run"
    if len(sanitized) > _RUN_REF_PREFIX_MAX:
        sanitized = sanitized[:_RUN_REF_PREFIX_MAX]
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

    # NOTE: the playwright BrowserContext is intentionally NOT exposed
    # as a public attribute (codex iter-4 important: a public escape
    # hatch lets callers mutate routing / cookies / pages / lifecycle
    # outside VeraCrawl's typed browser/session contract). Tests that
    # need to assert reuse use the fake's bookkeeping (number of
    # ``new_context`` calls on the fake browser) rather than peeking
    # at this object directly.

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
        evidence_artifact_store: EvidenceArtifactStorePort | None = None,
        har_capture_dir: Path | None = None,
        har_canary_tokens: Sequence[str] = (),
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
        # Phase 1 step 1.4: HAR capture + EvidenceArtifactStorePort.
        # ``evidence_artifact_store`` defaults to :class:`NoopEvidenceArtifactStore`
        # so existing fixture tests pass without configuration; the
        # production-mode gate refuses the no-op default. ``har_capture_dir``
        # is the working directory where Playwright writes the raw HAR
        # before redaction; required when HAR capture is active. The
        # ``har_canary_tokens`` list lets tests / authorized callers
        # declare strings that must be scrubbed from the persisted HAR
        # (e.g. test inputs the caller wants to verify never leak).
        self.evidence_artifact_store: EvidenceArtifactStorePort = (
            evidence_artifact_store
            if evidence_artifact_store is not None
            else NoopEvidenceArtifactStore()
        )
        self.har_capture_dir = har_capture_dir
        self.har_canary_tokens: tuple[str, ...] = tuple(har_canary_tokens)
        # Production-mode evidence-store gate: a no-op evidence store
        # in production silently drops HAR / DOM / header artifacts, so
        # mis-configured deployments lose evidence required for replay
        # / audit. Fail closed at construction (same pattern as the
        # robots / rate-limiter gates).
        if current_mode() == RuntimeMode.PRODUCTION and isinstance(
            self.evidence_artifact_store, NoopEvidenceArtifactStore
        ):
            raise ProductionRuntimeNotImplemented(
                backend="evidence_artifact_store",
                gate="PlaywrightBrowserObservationAdapter",
            )
        # Tests override the playwright entry point with a mock that
        # does not require a real Chromium install.
        self._playwright_factory: Callable[[], Any] = (
            playwright_factory if playwright_factory is not None else _load_sync_playwright
        )
        self._last_result: BrowserObservationResult | None = None
        # Most recently persisted HAR artifact_ref (per session). Read
        # via :attr:`last_har_artifact_ref` for tests / replay records.
        self._last_har_artifact_ref: str | None = None

    @property
    def last_result(self) -> BrowserObservationResult | None:
        return self._last_result

    @property
    def last_har_artifact_ref(self) -> str | None:
        """Most recently persisted HAR ``artifact_ref`` (or ``None``).

        Populated by :meth:`_open_session_internal` after the session's
        ``BrowserContext`` closes, the HAR file is read, redacted via
        :func:`redact_har_payload`, and persisted to
        :attr:`evidence_artifact_store`. Phase 1 step 1.5 will fold
        this into the per-attempt ``NetworkAttemptEvidence``; until
        then callers can read it directly off the adapter.
        """
        return self._last_har_artifact_ref

    def _storage_state_path(self, run_ref: Ref) -> Path | None:
        """Resolve the per-run ``storage_state.json`` path or ``None``.

        Returns ``None`` when persistence is disabled (no
        ``storage_state_dir`` configured); callers treat ``None`` as
        "do not load and do not save".
        """
        if self.storage_state_dir is None:
            return None
        return self.storage_state_dir / _storage_state_filename(run_ref)

    def _new_context(
        self,
        browser: Any,
        *,
        storage_state_path: Path | None,
        har_path: Path | None = None,
    ) -> Any:
        """Construct a ``BrowserContext`` with the rendering-stability
        config, optionally re-hydrated from a prior run's
        ``storage_state.json``.

        Read-path privacy boundary (codex iter-5 important): the
        ``storage_state_dir`` may be on shared / less-trusted storage
        across runs. Before passing a prior file to Playwright, the
        adapter validates that the path is a regular file (not a
        symlink — defends against an attacker planting a link to a
        cookie jar they control) and on POSIX that the mode is
        ``0o600`` (owner-only — refuses to ingest a file the writer
        already exposed to other users). Files that fail these checks
        are quarantined to ``<path>.untrusted-{ts}`` and the session
        falls through to a fresh context without prior state.

        Corrupt-state recovery (codex iter-5 important): persisted
        storage_state is a cache, not canonical state. If
        ``new_context(storage_state=...)`` raises (truncated JSON,
        Playwright schema mismatch, etc.), the session quarantines
        the file and retries ``new_context()`` without prior state
        rather than aborting the whole run. The fresh context is
        what session callers want when the cache is bad — they can
        always re-authenticate.
        """
        base_kwargs: dict[str, Any] = {
            "java_script_enabled": True,
            "ignore_https_errors": False,
            "user_agent": self.user_agent,
            "locale": "en-US",
            "extra_http_headers": {"Accept-Language": "en-US,en;q=0.9"},
        }
        # Phase 1 step 1.4: when an evidence store is configured (i.e.
        # not the no-op default), pass ``record_har_path`` so Playwright
        # captures the network log. The file is post-processed (read +
        # redacted + persisted to the evidence store + deleted) on
        # session exit. ``record_har_content="embed"`` is the Playwright
        # default; we keep it implicit so smaller engines (e.g. the
        # mock playwright in tests) don't have to honor extra flags.
        if har_path is not None:
            base_kwargs["record_har_path"] = str(har_path)
        validated_path: Path | None = None
        if storage_state_path is not None and storage_state_path.exists():
            if self._storage_state_path_is_trusted(storage_state_path):
                validated_path = storage_state_path
            else:
                self._quarantine_storage_state(
                    storage_state_path, reason="untrusted_permissions_or_symlink"
                )
        if validated_path is not None:
            try:
                return browser.new_context(**base_kwargs, storage_state=str(validated_path))
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "browser_storage_state_hydrate_failed",
                    storage_state_path=str(validated_path),
                )
                self._quarantine_storage_state(validated_path, reason="hydrate_failed")
                # Fall through to fresh-context retry below.
        return browser.new_context(**base_kwargs)

    @staticmethod
    def _storage_state_path_is_trusted(path: Path) -> bool:
        """Return True iff ``path`` is a regular file with owner-only
        permissions (POSIX) — safe to hand to Playwright as
        ``storage_state``.

        Uses ``lstat`` so a symlink is detected and rejected without
        following it. On non-POSIX systems the mode check is skipped
        (Windows ACLs are not portably introspectable) but the
        regular-file requirement still applies.
        """
        try:
            info = path.lstat()
        except OSError:
            return False
        # Regular file, not a symlink: ``lstat`` returns the link's own
        # stat, so a symlink shows up as ``S_IFLNK`` rather than
        # ``S_IFREG``. Anything that is not a regular file is refused.
        import stat as _stat_module

        if not _stat_module.S_ISREG(info.st_mode):
            return False
        if os.name == "posix":
            mode = info.st_mode & 0o777
            if mode != _STORAGE_STATE_FILE_MODE:
                return False
        return True

    @staticmethod
    def _quarantine_storage_state(path: Path, *, reason: str) -> None:
        """Rename a storage_state file out of the active directory.

        Used both for paths that fail the privacy check and for
        paths Playwright failed to hydrate from. Quarantining
        instead of deleting preserves the artifact for the
        operator to inspect; a timestamp suffix prevents
        successive failures from clobbering each other. Failure to
        rename (e.g., read-only filesystem) is logged but does not
        propagate — the caller is already on a recovery path.
        """
        timestamp = int(time.time())
        dest = path.with_suffix(path.suffix + f".quarantined-{reason}-{timestamp}")
        try:
            os.replace(str(path), str(dest))
            _logger.warning(
                "browser_storage_state_quarantined",
                source=str(path),
                dest=str(dest),
                reason=reason,
            )
        except OSError:
            _logger.exception(
                "browser_storage_state_quarantine_failed",
                path=str(path),
                reason=reason,
            )

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
        with self._open_session_internal(run_ref=run_ref, persist=True) as session:
            yield session

    @contextmanager
    def _open_session_internal(self, *, run_ref: Ref, persist: bool) -> Iterator[BrowserSession]:
        """Common session lifecycle with explicit persistence opt-in.

        ``persist=False`` forces transient behavior regardless of the
        adapter's ``storage_state_dir`` setting — the legacy
        single-call ``observe()`` / ``execute()`` paths use this so
        a one-shot navigation never reads or writes the persisted
        storage_state file (codex iter-2 important: the legacy
        paths must remain transient even when the adapter is
        otherwise configured for session-scoped persistence).
        """
        sync_playwright = self._playwright_factory()
        storage_state_path = self._storage_state_path(run_ref) if persist else None
        # Reset per-session HAR ref so a session that fails to capture
        # / persist HAR cannot leave a previous session's ``artifact_ref``
        # visible. Replay / evidence consumers must never associate a
        # stale ref with the current run.
        self._last_har_artifact_ref = None
        # Phase 1 step 1.4: pre-pick a HAR file path under the configured
        # capture directory. ``None`` disables HAR capture. HAR capture
        # is decoupled from ``persist`` (storage_state persistence) —
        # the two are unrelated concerns; a caller may want HAR
        # evidence without cookie-state persistence (one-shot
        # observe()) and vice-versa.
        har_path = self._pick_har_path(run_ref)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            # Outer try owns the browser; inner try owns the context.
            # If context creation raises, the outer ``finally`` still
            # runs ``browser.close()`` so a launched Chromium process
            # never outlives a failed setup (codex iter-3 important).
            try:
                try:
                    context = self._new_context(
                        browser,
                        storage_state_path=storage_state_path,
                        har_path=har_path,
                    )
                except Exception:
                    _logger.exception("browser_context_create_failed", run_ref=run_ref)
                    raise
                session = BrowserSession(
                    adapter=self,
                    playwright_browser=browser,
                    playwright_context=context,
                    run_ref=run_ref,
                )
                try:
                    yield session
                finally:
                    # Persistence is best-effort: a failure here must
                    # not leak the browser process. Log and proceed.
                    if storage_state_path is not None:
                        try:
                            self._write_storage_state(context, storage_state_path)
                        except Exception:  # noqa: BLE001
                            _logger.exception(
                                "browser_storage_state_persist_failed",
                                run_ref=run_ref,
                            )
                    try:
                        context.close()
                    except Exception:  # noqa: BLE001
                        _logger.exception("browser_context_close_failed", run_ref=run_ref)
                    # HAR post-processing happens *after* context.close()
                    # because Playwright finalizes the file when the
                    # context closes. Best-effort: a failure here must
                    # not leak the browser. The unredacted HAR file is
                    # always deleted (we never leave plaintext on disk).
                    if har_path is not None:
                        self._postprocess_har(
                            har_path=har_path,
                            run_ref=run_ref,
                        )
                    session._closed = True  # noqa: SLF001
            finally:
                try:
                    browser.close()
                except Exception:  # noqa: BLE001
                    _logger.exception("browser_close_failed", run_ref=run_ref)

    def _pick_har_path(self, run_ref: Ref) -> Path | None:
        """Resolve the on-disk path Playwright writes the raw HAR to.

        Returns ``None`` if HAR capture is not configured for this
        adapter (no ``har_capture_dir`` or evidence store is the
        no-op default — there is nowhere to persist the redacted HAR
        anyway, so we skip the on-disk staging too). When configured,
        the path lives under ``har_capture_dir`` with a SHA-256 +
        prefix-safe filename so two runs do not collide.
        """
        if self.har_capture_dir is None:
            return None
        if isinstance(self.evidence_artifact_store, NoopEvidenceArtifactStore):
            # The no-op store would discard the redacted bytes anyway;
            # skip the staging file so we don't write plaintext HAR
            # to disk for nothing.
            return None
        self.har_capture_dir.mkdir(parents=True, exist_ok=True)
        return self.har_capture_dir / f"{_storage_state_filename(run_ref)}.har.json"

    def _postprocess_har(self, *, har_path: Path, run_ref: Ref) -> None:
        """Read the raw HAR, redact, persist, delete the staging file.

        Best-effort — every step is independently guarded so a failure
        in one does not leave plaintext on disk and never propagates
        a HAR-side error to the caller (the browser session itself
        succeeded; HAR is evidence, not result).

        Privacy invariant: the unredacted HAR file is always deleted
        before we return, even if redaction or persistence raises.
        Leaving plaintext HAR on disk would defeat the structured
        redaction the design (§4 Phase 1) requires.
        """
        try:
            try:
                raw = har_path.read_bytes()
            except OSError:
                # Playwright didn't write the file (browser crashed
                # mid-trace, or the context was never navigated). Log
                # and skip — there is nothing to redact.
                _logger.warning(
                    "browser_har_missing_after_close",
                    run_ref=run_ref,
                    har_path=str(har_path),
                )
                return
            try:
                redacted = redact_har_payload(raw, canary_tokens=self.har_canary_tokens)
            except HarRedactionError:
                # Malformed HAR — never persist. Log and drop.
                _logger.exception(
                    "browser_har_redaction_failed",
                    run_ref=run_ref,
                    har_path=str(har_path),
                )
                return
            try:
                result = self.evidence_artifact_store.put(
                    run_ref=str(run_ref),
                    attempt_ref=f"{run_ref}:har",
                    kind=ArtifactKind.HAR,
                    payload=redacted,
                    content_type="application/json",
                    redaction_applied=True,
                )
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "browser_har_evidence_persist_failed",
                    run_ref=run_ref,
                    har_path=str(har_path),
                )
                return
            self._last_har_artifact_ref = result.artifact_ref
            _logger.info(
                "browser_har_persisted",
                run_ref=run_ref,
                artifact_ref=result.artifact_ref,
                size_bytes=result.size_bytes,
            )
        finally:
            # Always delete the staging file — never leave unredacted
            # HAR bytes on disk.
            try:
                har_path.unlink(missing_ok=True)
            except OSError:
                _logger.exception(
                    "browser_har_staging_unlink_failed",
                    har_path=str(har_path),
                )

    @staticmethod
    def _write_storage_state(context: Any, path: Path) -> None:
        """Persist ``context.storage_state`` to ``path`` atomically with
        owner-only permissions.

        ``storage_state`` carries live cookies and origin storage —
        the file is sensitive by definition. The naive sequence
        "write file via playwright; chmod afterward" leaves a window
        controlled by the process umask during which the file is
        readable by group/other (codex iter-3 important).

        Atomic + secure recipe (POSIX):

        1. Ask playwright for the storage_state dict (no ``path=``
           kwarg → the dict comes back without playwright touching
           the filesystem).
        2. Open a sibling temp file with ``O_CREAT | O_EXCL |
           O_WRONLY`` and mode 0o600 — atomic creation refuses to
           clobber an existing file (so a pre-existing broad-mode
           file or a symlink in the directory cannot leak data
           through us), and the mode is set in the create call so
           there is no permission-window race.
        3. ``O_NOFOLLOW`` (where supported) refuses to follow a
           symlink at the temp path — defends against an attacker
           planting a symlink to a file they control.
        4. Write JSON to the temp file, fsync to ensure durability,
           then ``os.replace`` for atomic rename onto the final
           path.
        5. Re-verify the final mode is 0o600 (the rename preserves
           the source mode on POSIX, so the chmod call is belt-
           and-braces; on Windows ACL semantics this is a no-op
           and we accept the filesystem default).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        state = context.storage_state()  # dict, no filesystem touch
        # Encode to bytes so we can write through ``os.write`` on a
        # raw file descriptor with the secure flags below.
        payload = json.dumps(state, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        # Use a sibling temp filename so ``os.replace`` ends up on the
        # same filesystem (atomic rename guarantee).
        temp_path = path.with_suffix(path.suffix + ".tmp")
        # Build the open flags: O_NOFOLLOW where supported (POSIX);
        # silently fall back where it's not defined (Windows).
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        flags |= nofollow
        # If a stale temp file remains from a prior crashed run,
        # remove it so O_EXCL doesn't reject the create.
        if temp_path.exists() or temp_path.is_symlink():
            try:
                temp_path.unlink()
            except OSError:
                _logger.exception("browser_storage_state_temp_unlink_failed", path=str(temp_path))
                raise
        fd = os.open(str(temp_path), flags, _STORAGE_STATE_FILE_MODE)
        try:
            # ``os.write`` can perform a partial write — loop until
            # every byte of the payload reaches the kernel buffer
            # (codex iter-4 important: a partial write would leave
            # a truncated JSON file that later runs would fail to
            # hydrate from).
            written = 0
            while written < len(payload):
                chunk = os.write(fd, payload[written:])
                if chunk <= 0:
                    raise OSError(
                        f"os.write returned {chunk} writing storage_state; "
                        "refusing to spin and risk truncated persistence"
                    )
                written += chunk
            os.fsync(fd)
        finally:
            os.close(fd)
        # Atomic rename. On POSIX this preserves the temp file's
        # mode (0o600). On Windows the mode is filesystem-default,
        # which is acceptable because Windows uses ACLs we cannot
        # set portably.
        os.replace(str(temp_path), str(path))
        try:
            os.chmod(path, _STORAGE_STATE_FILE_MODE)
        except OSError:
            _logger.debug("storage_state_chmod_unsupported", path=str(path))

    def observe(
        self,
        *,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        """One-shot navigation that opens a transient session of length 1.

        Backwards-compatible with the v0 single-call usage: every
        invocation launches a fresh browser, creates a context, runs
        the navigation, and closes everything before returning.
        Persistence is **disabled** for this path even when the
        adapter is configured with ``storage_state_dir`` — a
        transient one-shot must not silently inherit or contribute
        to the per-run storage_state file (codex iter-2 important:
        the legacy path's "transient" claim has to hold regardless
        of how the adapter is otherwise configured). Use
        :meth:`open_session` when multiple navigations should share a
        context AND the run's accumulated state should persist.
        """
        with self._open_session_internal(run_ref=run_ref, persist=False) as session:
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
        """Single navigation against an already-open BrowserContext.

        Per-call resources (route handler, page) are torn down even
        when the navigation raises, so a long-lived session does not
        accumulate stacked route handlers or leaked pages across
        partially-failed observations (codex iter-2 important:
        defensive cleanup must preserve the original exception while
        still running every cleanup step).
        """
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

        page: Any | None = None
        route_registered = False
        try:
            context.route("**/*", route_handler)
            route_registered = True
            page = context.new_page()
            page.on("console", lambda message: console_logs.append(message.text))
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
            # Each cleanup step is independently guarded so a failure
            # in one step does not skip later steps and never masks
            # the original exception (Python re-raises automatically
            # when the finally block completes without raising).
            if page is not None:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    _logger.exception(
                        "browser_page_close_failed",
                        run_ref=run_ref,
                        target_url=target_url,
                    )
            if route_registered:
                try:
                    context.unroute("**/*", route_handler)
                except Exception:  # noqa: BLE001
                    _logger.exception(
                        "browser_unroute_failed",
                        run_ref=run_ref,
                        target_url=target_url,
                    )

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
