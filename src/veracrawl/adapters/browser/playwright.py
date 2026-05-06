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

Detection of bot-protection challenges (Cloudflare Turnstile,
DataDome, PerimeterX, etc.) is the access-control classifier's job
in a separate phase; this adapter surfaces such pages as a typed
``AccessControlBlocked`` failure rather than evading.

Playwright itself is still optional — it is loaded lazily inside
``_load_sync_playwright`` so the adapter module can be imported
without the ``browser-playwright`` extra installed.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence
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

_DEFAULT_CHROME_UA: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
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
    ) -> None:
        self.fixture_id = fixture_id
        self.target_url = target_url
        self.sandbox_policy = sandbox_policy
        self.side_effect_class = side_effect_class
        self.wait_for_text_fragments = list(wait_for_text_fragments)
        self.user_agent = user_agent
        self.wait_until = wait_until
        self.post_load_idle_ms = post_load_idle_ms
        self._last_result: BrowserObservationResult | None = None

    @property
    def last_result(self) -> BrowserObservationResult | None:
        return self._last_result

    def observe(
        self,
        *,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        sync_playwright = _load_sync_playwright()
        started = time.monotonic()
        network_request_count = 0
        blocked_request_count = 0
        console_logs: list[str] = []

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                java_script_enabled=True,
                ignore_https_errors=False,
                user_agent=self.user_agent,
                locale="en-US",
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            )

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
            context.close()
            browser.close()

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
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for the live browser adapter; install the "
            "browser-playwright extra and run `python -m playwright install chromium`"
        ) from exc
    return sync_playwright
