"""Live test #3 (Phase 1 step 1.6c) — ``example.com`` DOM + screenshot.

design.md §6 step 6.4 deliverable #3: ``example.com`` — basic
DOM + screenshot.

Validates that the production browser adapter
(``PlaywrightBrowserObservationAdapter``) actually launches
Chromium, navigates to a real public origin, captures the DOM
HTML, takes a full-page screenshot, and persists a redacted HAR
to the configured ``EvidenceArtifactStorePort``. Runs under
``RuntimeMode.PRODUCTION`` so the production-only gates
(``evidence_artifact_store`` / ``har_capture_dir`` non-noop)
apply.

Skipped when Chromium is not installed (the test project may run
in environments without ``python -m playwright install chromium``;
operators install it explicitly before running the live suite).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.adapters.browser.playwright import PlaywrightBrowserObservationAdapter
from veracrawl.adapters.object_stores.local_fs_evidence_store import (
    LocalFsEvidenceArtifactStore,
)
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.enums import BrowserSideEffectClass
from veracrawl.runtime_support.runtime_mode import RuntimeMode, with_runtime_mode


@pytest.fixture
def chromium_required() -> None:
    """Skip the test when ``playwright install chromium`` has not
    been run.

    Codex iter-1 important: the previous module-level check
    launched Chromium at collection time, slowing every default
    ``-m 'not live'`` invocation that imported this file. The
    fixture defers the launch attempt to the moment the test
    actually runs, so unselected live tests cost nothing.
    """

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Chromium not available: {exc}")


def _sandbox() -> BrowserSandboxPolicy:
    return BrowserSandboxPolicy(
        id="sandbox:live:step-1-6c",
        allowed_origin_refs=["origin:example.com"],
        egress_allowlist=["https://example.com"],
        max_runtime_ms=30_000,
        max_dom_bytes=1_000_000,
        max_screenshot_bytes=10_000_000,
        max_network_log_bytes=1_000_000,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
    )


def _build_adapter(tmp_path: Path) -> PlaywrightBrowserObservationAdapter:
    """Production-shape wiring: real ``LocalFsEvidenceArtifactStore``
    + real ``har_capture_dir`` + storage_state dir. Any production
    gate regression surfaces here at construction time."""

    return PlaywrightBrowserObservationAdapter(
        fixture_id="live-step-1-6c",
        target_url="https://example.com",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path / "storage_state",
        evidence_artifact_store=LocalFsEvidenceArtifactStore(root=tmp_path / "evidence"),
        har_capture_dir=tmp_path / "har",
    )


@pytest.mark.live
def test_example_com_dom_contains_example_domain(chromium_required: None, tmp_path: Path) -> None:
    """Acceptance (design.md §6 step 6.4 #3): the rendered DOM
    contains the well-known stable string ``Example Domain``."""

    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = _build_adapter(tmp_path)
        result = adapter.observe(
            run_ref="run:live:step-1-6c",
            source_ref="source:live:step-1-6c:example",
            target_url="https://example.com",
            sandbox_policy=_sandbox(),
        )
    assert result is not None
    # ``Example Domain`` is the page's H1 across every revision since
    # 2010. Asserting the literal string keeps the test stable
    # across cosmetic markup changes.
    assert "Example Domain" in result.dom_text
    # DOM artifact ref + content hash populated.
    assert result.dom_content_hash
    assert result.step.dom_artifact_ref


@pytest.mark.live
def test_example_com_screenshot_bytes_non_empty(chromium_required: None, tmp_path: Path) -> None:
    """Acceptance (design.md §6 step 6.4 #3): a full-page screenshot
    is captured and reported as non-empty PNG bytes."""

    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = _build_adapter(tmp_path)
        result = adapter.observe(
            run_ref="run:live:step-1-6c",
            source_ref="source:live:step-1-6c:example",
            target_url="https://example.com",
            sandbox_policy=_sandbox(),
        )
    # Screenshot bytes recorded; PNG signature is 8 bytes, the
    # full-page screenshot should be at least a few hundred bytes.
    assert result.screenshot_byte_count > 100
    assert result.step.screenshot_artifact_ref


@pytest.mark.live
def test_example_com_har_persisted_via_evidence_store(
    chromium_required: None, tmp_path: Path
) -> None:
    """The browser adapter's HAR pipeline (Playwright
    ``record_har_path`` → ``redact_har_payload`` →
    ``EvidenceArtifactStorePort.put``) must run end-to-end against a
    real origin under ``RuntimeMode.PRODUCTION``."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    har_dir = tmp_path / "har"
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = PlaywrightBrowserObservationAdapter(
            fixture_id="live-step-1-6c-har",
            target_url="https://example.com",
            sandbox_policy=_sandbox(),
            storage_state_dir=tmp_path / "storage_state",
            evidence_artifact_store=store,
            har_capture_dir=har_dir,
        )
        # Use the explicit ``open_session`` path to exercise the
        # per-run session lifecycle directly (one-shot ``observe``
        # also runs HAR post-processing internally — both surfaces
        # share the same lifecycle code).
        with adapter.open_session(run_ref="run:live:step-1-6c") as session:
            session.observe(
                source_ref="source:live:step-1-6c:example",
                target_url="https://example.com",
                sandbox_policy=_sandbox(),
            )
    # HAR should have been read, redacted, and persisted.
    har_ref = adapter.last_har_artifact_ref
    assert har_ref is not None, "expected HAR artifact_ref after session close"
    assert har_ref.startswith("artifact:evidence:har:")
    # Round-trip through the evidence store.
    fetched = store.get(artifact_ref=har_ref)
    assert fetched is not None
    assert b"<redacted-body>" in fetched, "HAR body redaction did not run"
    # Staging file deleted (privacy invariant: no plaintext HAR on disk).
    assert list(har_dir.glob("*.har.json")) == []
