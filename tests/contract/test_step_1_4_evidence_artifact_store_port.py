"""Contract tests for Phase 1 step 1.4 — ``EvidenceArtifactStorePort``.

design.md §4 Phase 1 deliverables: Playwright-captured HAR (and
related per-attempt artifacts) flow through this port to a default
production impl :class:`LocalFsEvidenceArtifactStore`. The framework
default :class:`NoopEvidenceArtifactStore` lets existing tests pass
without configuration (Phase 1 boundary acceptance).

The ``redaction_applied`` flag is load-bearing: HAR / DOM / header
payloads contain credentials and PII that must not be persisted in
plaintext. Calling ``put`` with ``redaction_applied=False`` for a
redaction-required kind raises :class:`EvidenceRedactionRequired`
even on the no-op default — same contract failure mode in tests as
in production.
"""

from __future__ import annotations

import pytest

from veracrawl.ports.evidence_artifact_store import (
    ArtifactKind,
    EvidenceArtifactStorePort,
    EvidencePutResult,
    EvidenceRedactionRequired,
    NoopEvidenceArtifactStore,
    kind_requires_redaction,
)


def test_artifact_kind_enum_values() -> None:
    assert ArtifactKind.HAR.value == "har"
    assert ArtifactKind.SCREENSHOT.value == "screenshot"
    assert ArtifactKind.DOM.value == "dom"
    assert ArtifactKind.RESPONSE_HEADERS.value == "response_headers"
    assert ArtifactKind.REQUEST_HEADERS.value == "request_headers"
    assert ArtifactKind.TRACE.value == "trace"
    assert ArtifactKind.OTHER.value == "other"


@pytest.mark.parametrize(
    "kind, expected",
    [
        (ArtifactKind.HAR, True),
        (ArtifactKind.DOM, True),
        (ArtifactKind.RESPONSE_HEADERS, True),
        (ArtifactKind.REQUEST_HEADERS, True),
        (ArtifactKind.TRACE, True),
        (ArtifactKind.SCREENSHOT, False),
        (ArtifactKind.OTHER, False),
    ],
)
def test_kind_requires_redaction_table(kind: ArtifactKind, expected: bool) -> None:
    assert kind_requires_redaction(kind) is expected


def test_noop_satisfies_runtime_protocol() -> None:
    store = NoopEvidenceArtifactStore()
    assert isinstance(store, EvidenceArtifactStorePort)


def test_noop_put_returns_deterministic_artifact_ref_for_same_payload() -> None:
    store = NoopEvidenceArtifactStore()
    payload = b'{"log":{"version":"1.2","entries":[]}}'
    a = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    b = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    assert isinstance(a, EvidencePutResult)
    assert a.artifact_ref == b.artifact_ref
    assert a.content_digest_sha256 == b.content_digest_sha256
    assert a.size_bytes == len(payload)
    assert a.redaction_applied is True


def test_noop_put_rejects_unredacted_har() -> None:
    store = NoopEvidenceArtifactStore()
    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:fixture",
            attempt_ref="attempt:1",
            kind=ArtifactKind.HAR,
            payload=b'{"log": {}}',
            content_type="application/json",
            redaction_applied=False,
        )


def test_noop_put_rejects_unredacted_dom() -> None:
    store = NoopEvidenceArtifactStore()
    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:fixture",
            attempt_ref="attempt:1",
            kind=ArtifactKind.DOM,
            payload=b"<html>...</html>",
            content_type="text/html",
            redaction_applied=False,
        )


def test_noop_put_accepts_unredacted_screenshot() -> None:
    """Image bytes have no field-level keys to redact — the kind is
    exempt from the redaction-required check."""

    store = NoopEvidenceArtifactStore()
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.SCREENSHOT,
        payload=b"\x89PNG\r\n\x1a\n...",
        content_type="image/png",
        redaction_applied=False,
    )
    assert result.redaction_applied is False
    assert "screenshot" in result.artifact_ref


def test_noop_get_always_returns_none() -> None:
    """The no-op never persists, so reads always miss — same shape as
    a fresh production store with no prior writes."""

    store = NoopEvidenceArtifactStore()
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=b'{"log":{}}',
        content_type="application/json",
        redaction_applied=True,
    )
    assert store.get(artifact_ref=result.artifact_ref) is None


def test_evidence_put_result_is_immutable() -> None:
    result = EvidencePutResult(
        artifact_ref="artifact:noop:har:abc",
        content_digest_sha256="0" * 64,
        size_bytes=42,
        redaction_applied=True,
    )
    with pytest.raises((AttributeError, Exception)):
        result.size_bytes = 99  # type: ignore[misc]
