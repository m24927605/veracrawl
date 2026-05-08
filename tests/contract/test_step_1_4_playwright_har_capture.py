"""Contract tests for Phase 1 step 1.4 wiring of HAR capture into
``PlaywrightBrowserObservationAdapter``.

design.md §4 Phase 1 deliverables: HAR capture via Playwright
``record_har_path`` (the design also mentions
``context.tracing.start({snapshots, screenshots})`` for snapshots /
screenshots, but step 1.4's acceptance is specifically the parseable
HAR JSON). The captured file is read post-context-close, redacted
through :func:`redact_har_payload`, and persisted to the
:class:`EvidenceArtifactStorePort`. The original on-disk file is
always deleted — no plaintext HAR ever survives the session.

Boundary acceptance: existing tests must keep passing without HAR
configuration. The default :class:`NoopEvidenceArtifactStore`
disables HAR capture entirely (no ``record_har_path`` is passed to
``new_context``).

Production gate: under ``RuntimeMode.PRODUCTION`` with the default
no-op evidence store, adapter construction raises
:class:`ProductionRuntimeNotImplemented`.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from veracrawl.adapters.browser.playwright import PlaywrightBrowserObservationAdapter
from veracrawl.adapters.object_stores.local_fs_evidence_store import (
    LocalFsEvidenceArtifactStore,
)
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.enums import BrowserSideEffectClass
from veracrawl.ports.evidence_artifact_store import (
    ArtifactKind,
    EvidencePutResult,
    NoopEvidenceArtifactStore,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)

# -- Fake Playwright that honors record_har_path ----------------------


class _FakePage:
    def __init__(self, url: str = "https://example.test/") -> None:
        self._url = url

    def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        del wait_until, timeout
        self._url = url

    def wait_for_function(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs

    def wait_for_timeout(self, ms: int) -> None:
        del ms

    def content(self) -> str:
        return f"<html>{self._url}</html>"

    def screenshot(self, *, full_page: bool) -> bytes:
        del full_page
        return b"\x89PNG\r\n\x1a\n-fake"

    def on(self, event: str, handler: Any) -> None:
        del event, handler

    def locator(self, _selector: str) -> _FakePage:
        return self

    def inner_text(self, *, timeout: int) -> str:
        del timeout
        return "fake text"

    def close(self) -> None:
        pass


class _FakeContext:
    """Honors ``record_har_path`` by writing a fixture HAR on close."""

    def __init__(self, kwargs: dict[str, Any], *, har_payload: bytes | None) -> None:
        self.init_kwargs = kwargs
        self.closed = False
        self._har_payload = har_payload

    def route(self, _pattern: str, _handler: Any) -> None:
        pass

    def unroute(self, _pattern: str, _handler: Any) -> None:
        pass

    def new_page(self) -> _FakePage:
        return _FakePage()

    def storage_state(self, *, path: str | None = None) -> dict[str, Any]:
        del path
        return {"cookies": [], "origins": []}

    def close(self) -> None:
        self.closed = True
        # Mimic Playwright finalizing the HAR file on close.
        har_path = self.init_kwargs.get("record_har_path")
        if har_path is not None and self._har_payload is not None:
            Path(har_path).write_bytes(self._har_payload)


class _FakeBrowser:
    def __init__(self, *, har_payload: bytes | None) -> None:
        self.contexts: list[_FakeContext] = []
        self.closed = False
        self._har_payload = har_payload

    def new_context(self, **kwargs: Any) -> _FakeContext:
        ctx = _FakeContext(kwargs, har_payload=self._har_payload)
        self.contexts.append(ctx)
        return ctx

    def close(self) -> None:
        self.closed = True


class _FakeChromium:
    def __init__(self, parent: _FakePlaywright) -> None:
        self._parent = parent

    def launch(self, *, headless: bool) -> _FakeBrowser:
        del headless
        browser = _FakeBrowser(har_payload=self._parent.har_payload)
        self._parent.browsers.append(browser)
        return browser


class _FakePlaywright:
    def __init__(self, *, har_payload: bytes | None) -> None:
        self.chromium = _FakeChromium(self)
        self.browsers: list[_FakeBrowser] = []
        self.har_payload = har_payload


def _fake_factory(*, har_payload: bytes | None = None) -> Any:
    @contextmanager
    def _outer() -> Iterator[_FakePlaywright]:
        yield _FakePlaywright(har_payload=har_payload)

    return lambda: _outer


def _sandbox() -> BrowserSandboxPolicy:
    return BrowserSandboxPolicy(
        id="sandbox:test",
        allowed_origin_refs=["origin:example.test"],
        egress_allowlist=["https://example.test"],
        max_runtime_ms=30000,
        max_dom_bytes=10_000_000,
        max_screenshot_bytes=10_000_000,
        max_network_log_bytes=1_000_000,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
    )


def _make_har_payload(
    *,
    auth_token: str = "Bearer secret-token-xyz",
    canary_url: str = "https://example.test/items?token=CANARY_42",
) -> bytes:
    return json.dumps(
        {
            "log": {
                "version": "1.2",
                "creator": {"name": "fake-playwright", "version": "0"},
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": canary_url,
                            "headers": [
                                {"name": "Authorization", "value": auth_token},
                                {"name": "User-Agent", "value": "TestUA"},
                            ],
                            "queryString": [
                                {"name": "token", "value": "CANARY_42"},
                            ],
                            "cookies": [],
                            "headersSize": -1,
                            "bodySize": 0,
                        },
                        "response": {
                            "status": 200,
                            "statusText": "OK",
                            "headers": [
                                {"name": "Set-Cookie", "value": "session=secret-cookie"},
                            ],
                            "cookies": [],
                            "content": {
                                "size": 50,
                                "mimeType": "text/html",
                                "text": "<html>secret-page-marker</html>",
                            },
                        },
                    }
                ],
            }
        }
    ).encode("utf-8")


# -- Tests ------------------------------------------------------------


def test_default_noop_evidence_store_does_not_pass_record_har_path(
    tmp_path: Path,
) -> None:
    """Boundary acceptance: an adapter constructed without an evidence
    store does not enable HAR capture, so ``record_har_path`` never
    appears in ``new_context`` kwargs and existing tests are
    unaffected."""

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright(har_payload=None)
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-noop",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        playwright_factory=lambda: capturing_factory,
    )
    sandbox = _sandbox()
    with adapter.open_session(run_ref="run:noop") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=sandbox,
        )

    pw: _FakePlaywright = captured["pw"]
    ctx = pw.browsers[0].contexts[0]
    assert "record_har_path" not in ctx.init_kwargs


def test_real_evidence_store_enables_har_capture_with_record_path(
    tmp_path: Path,
) -> None:
    """When a real evidence store + ``har_capture_dir`` are configured,
    the adapter passes ``record_har_path`` so Playwright records the
    HAR for that session."""

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright(har_payload=_make_har_payload())
        captured["pw"] = pw
        yield pw

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-real",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:capture") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    ctx = pw.browsers[0].contexts[0]
    assert "record_har_path" in ctx.init_kwargs


def test_har_persisted_to_evidence_store_after_session_close(
    tmp_path: Path,
) -> None:
    """Round-trip: open session → HAR is read, redacted, persisted →
    ``adapter.last_har_artifact_ref`` points at retrievable bytes."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-persist",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(har_payload=_make_har_payload()),
    )
    with adapter.open_session(run_ref="run:persist") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    ref = adapter.last_har_artifact_ref
    assert ref is not None
    assert ref.startswith("artifact:evidence:har:")
    fetched = store.get(artifact_ref=ref)
    assert fetched is not None
    parsed = json.loads(fetched)
    assert parsed["log"]["entries"][0]["request"]["url"].startswith("https://example.test/items")


def test_har_redaction_strips_authorization_header(tmp_path: Path) -> None:
    """The persisted HAR must have ``Authorization`` redacted — the
    raw token from the fixture must not appear anywhere in the
    persisted bytes."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-redact",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(
            har_payload=_make_har_payload(auth_token="Bearer SECRET_TOK_42")
        ),
    )
    with adapter.open_session(run_ref="run:redact") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    fetched = store.get(artifact_ref=adapter.last_har_artifact_ref or "")
    assert fetched is not None
    assert b"SECRET_TOK_42" not in fetched
    assert b"<redacted>" in fetched


def test_har_canary_token_scrubbed_from_url(tmp_path: Path) -> None:
    """A caller-declared canary token must not appear anywhere in the
    persisted HAR (URL substring scrub)."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-canary",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        har_canary_tokens=["CANARY_42"],
        playwright_factory=_fake_factory(har_payload=_make_har_payload()),
    )
    with adapter.open_session(run_ref="run:canary") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    fetched = store.get(artifact_ref=adapter.last_har_artifact_ref or "")
    assert fetched is not None
    assert b"CANARY_42" not in fetched


def test_har_staging_file_deleted_after_persistence(tmp_path: Path) -> None:
    """Privacy invariant: the unredacted HAR file must always be
    deleted from the staging dir, even on success."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    har_dir = tmp_path / "har"
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-cleanup",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=har_dir,
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(har_payload=_make_har_payload()),
    )
    with adapter.open_session(run_ref="run:cleanup") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    # No leftover HAR files in the staging dir.
    leftovers = list(har_dir.glob("*.har.json"))
    assert leftovers == []


def test_missing_har_file_after_close_does_not_raise(tmp_path: Path) -> None:
    """If Playwright never wrote the HAR (e.g., browser crashed mid-
    trace), post-processing logs and continues — never raises."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-missing",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(har_payload=None),  # never writes HAR
    )
    with adapter.open_session(run_ref="run:missing") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    # No artifact_ref because no HAR was ever read.
    assert adapter.last_har_artifact_ref is None


def test_malformed_har_does_not_persist_plaintext(tmp_path: Path) -> None:
    """A malformed HAR file must trigger fail-closed: the staging file
    is deleted, no redacted payload is persisted, and the original
    bytes never reach the evidence store under ANY artifact kind /
    extension / path (iter-2 #11: scan the whole evidence root, not
    just the HAR glob)."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    har_dir = tmp_path / "har"
    sentinel = "secret-marker-99"
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-malformed",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=har_dir,
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(
            har_payload=f"this is not json at all -- {sentinel}".encode()
        ),
    )
    with adapter.open_session(run_ref="run:malformed") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    assert adapter.last_har_artifact_ref is None
    # Scan EVERY persisted file under the evidence root — not just
    # the HAR glob. A buggy implementation that persisted under
    # another kind / extension / path would still leak the sentinel.
    leaked_files: list[Path] = []
    for path in (tmp_path / "evidence").rglob("*"):
        if path.is_file():
            try:
                if sentinel.encode() in path.read_bytes():
                    leaked_files.append(path)
            except OSError:
                pass
    assert leaked_files == []
    # Staging file deleted.
    assert list(har_dir.glob("*.har.json")) == []


def test_production_mode_with_default_noop_evidence_store_fails_closed(
    tmp_path: Path,
) -> None:
    """``RuntimeMode.PRODUCTION`` + default ``NoopEvidenceArtifactStore``
    → :class:`ProductionRuntimeNotImplemented` at construction. The
    no-op would silently drop HAR / DOM / header artifacts in
    production."""

    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            PlaywrightBrowserObservationAdapter(
                fixture_id="step-1-4-prod-noop",
                target_url="https://example.test/",
                sandbox_policy=_sandbox(),
                storage_state_dir=tmp_path,
                playwright_factory=_fake_factory(),
            )
    assert exc.value.backend == "evidence_artifact_store"


def test_production_mode_with_real_evidence_store_succeeds(tmp_path: Path) -> None:
    """Production mode + real evidence store succeeds: the gate refuses
    only the no-op default, not legitimate wiring."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = PlaywrightBrowserObservationAdapter(
            fixture_id="step-1-4-prod-real",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
            storage_state_dir=tmp_path,
            evidence_artifact_store=store,
            har_capture_dir=tmp_path / "har",
            playwright_factory=_fake_factory(har_payload=_make_har_payload()),
        )
    assert adapter.evidence_artifact_store is store


def test_redaction_required_kind_with_unredacted_payload_raises_at_put(
    tmp_path: Path,
) -> None:
    """Sanity check that the noop store still enforces the redaction
    contract — same shape as production, so callers exercising the
    no-op see the contract failure mode."""

    from veracrawl.ports.evidence_artifact_store import EvidenceRedactionRequired

    store = NoopEvidenceArtifactStore()
    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:r",
            attempt_ref="attempt:1",
            kind=ArtifactKind.HAR,
            payload=b'{"log":{}}',
            content_type="application/json",
            redaction_applied=False,
        )


def test_last_har_artifact_ref_resets_when_subsequent_session_misses(
    tmp_path: Path,
) -> None:
    """A second session that fails to capture HAR (e.g. browser crash
    → no file) must not leave the previous session's
    ``last_har_artifact_ref`` visible. Replay / evidence consumers
    must never associate stale evidence with a new run."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")

    @contextmanager
    def factory_capturing_then_missing() -> Iterator[_FakePlaywright]:
        # First session: HAR present. Second session: no HAR file.
        if not factory_capturing_then_missing.first_done:  # type: ignore[attr-defined]
            factory_capturing_then_missing.first_done = True  # type: ignore[attr-defined]
            yield _FakePlaywright(har_payload=_make_har_payload())
        else:
            yield _FakePlaywright(har_payload=None)

    factory_capturing_then_missing.first_done = False  # type: ignore[attr-defined]

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-reset",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=lambda: factory_capturing_then_missing,
    )
    # First session — captures HAR.
    with adapter.open_session(run_ref="run:first") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    first_ref = adapter.last_har_artifact_ref
    assert first_ref is not None
    # Second session — no HAR. Must reset, not leave stale ref.
    with adapter.open_session(run_ref="run:second") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    assert adapter.last_har_artifact_ref is None


def test_har_capture_works_for_observe_one_shot_path(tmp_path: Path) -> None:
    """``observe()`` is the legacy one-shot path that uses
    ``persist=False``. HAR capture is a separate concern from
    storage_state persistence — a one-shot caller with a real
    evidence store + capture dir must still get HAR persisted."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-4-oneshot",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        # No storage_state_dir → persist=False on observe()
        har_capture_dir=tmp_path / "har",
        evidence_artifact_store=store,
        playwright_factory=_fake_factory(har_payload=_make_har_payload()),
    )
    adapter.observe(
        run_ref="run:oneshot",
        source_ref="source:fixture",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
    )
    # HAR captured even on the legacy one-shot path.
    assert adapter.last_har_artifact_ref is not None
    assert adapter.last_har_artifact_ref.startswith("artifact:evidence:har:")


def test_evidence_put_result_round_trip(tmp_path: Path) -> None:
    """Sanity check the persisted result shape — used by the playwright
    wiring to populate ``last_har_artifact_ref``."""

    store = LocalFsEvidenceArtifactStore(root=tmp_path / "evidence")
    result = store.put(
        run_ref="run:r",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{"entries":[]}}',
        content_type="application/json",
        redaction_applied=True,
    )
    assert isinstance(result, EvidencePutResult)
    assert result.redaction_applied is True
    assert store.get(artifact_ref=result.artifact_ref) == b'{"log":{"entries":[]}}'
