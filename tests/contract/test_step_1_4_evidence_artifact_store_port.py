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
    "kind",
    [
        ArtifactKind.HAR,
        ArtifactKind.DOM,
        ArtifactKind.RESPONSE_HEADERS,
        ArtifactKind.REQUEST_HEADERS,
        ArtifactKind.TRACE,
        ArtifactKind.SCREENSHOT,
        ArtifactKind.OTHER,
    ],
)
def test_every_kind_requires_attestation(kind: ArtifactKind) -> None:
    """Iter-2 #6: every kind requires ``redaction_applied=True``.

    For HAR/DOM/headers it means structural redaction was applied;
    for SCREENSHOT/TRACE/OTHER it means lifecycle policy was
    acknowledged by the producer. Either way, ``put`` refuses
    unattested persistence — earlier blanket exemption for
    SCREENSHOT created a weak contract that leaked into Phase 6.
    """

    assert kind_requires_redaction(kind) is True


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


def test_noop_put_rejects_unredacted_screenshot() -> None:
    """Iter-2 #6: screenshots also require attestation. Earlier
    exemption was rejected because screenshots can capture rendered
    PII / tokens / account UI."""

    store = NoopEvidenceArtifactStore()
    with pytest.raises(EvidenceRedactionRequired):
        store.put(
            run_ref="run:fixture",
            attempt_ref="attempt:1",
            kind=ArtifactKind.SCREENSHOT,
            payload=b"\x89PNG\r\n\x1a\n...",
            content_type="image/png",
            redaction_applied=False,
        )


def test_noop_put_accepts_attested_screenshot() -> None:
    store = NoopEvidenceArtifactStore()
    result = store.put(
        run_ref="run:fixture",
        attempt_ref="attempt:1",
        kind=ArtifactKind.SCREENSHOT,
        payload=b"\x89PNG\r\n\x1a\n...",
        content_type="image/png",
        redaction_applied=True,  # producer attests lifecycle policy applied
    )
    assert result.redaction_applied is True
    assert "screenshot" in result.artifact_ref


def test_noop_put_artifact_ref_scoped_by_run_attempt_kind() -> None:
    """Iter-2 #4: same payload under different run/attempt/kind must
    yield different artifact_refs — production impl scopes by all
    three, so the noop must too (otherwise unit tests rely on a
    payload-only ref the production store would never emit)."""

    store = NoopEvidenceArtifactStore()
    payload = b'{"log":{"entries":[]}}'
    base = store.put(
        run_ref="run:a",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    diff_run = store.put(
        run_ref="run:b",
        attempt_ref="attempt:1",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    diff_attempt = store.put(
        run_ref="run:a",
        attempt_ref="attempt:2",
        kind=ArtifactKind.HAR,
        payload=payload,
        content_type="application/json",
        redaction_applied=True,
    )
    diff_kind = store.put(
        run_ref="run:a",
        attempt_ref="attempt:1",
        kind=ArtifactKind.DOM,
        payload=payload,
        content_type="text/html",
        redaction_applied=True,
    )
    assert base.artifact_ref != diff_run.artifact_ref
    assert base.artifact_ref != diff_attempt.artifact_ref
    assert base.artifact_ref != diff_kind.artifact_ref


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
    """Frozen dataclass — assignment raises ``FrozenInstanceError``
    (a subclass of ``AttributeError``)."""

    from dataclasses import FrozenInstanceError

    result = EvidencePutResult(
        artifact_ref="artifact:noop:har:abc",
        content_digest_sha256="0" * 64,
        size_bytes=42,
        redaction_applied=True,
    )
    with pytest.raises(FrozenInstanceError):
        result.size_bytes = 99  # type: ignore[misc]
