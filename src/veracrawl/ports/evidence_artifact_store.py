"""``EvidenceArtifactStorePort`` — per-attempt evidence persistence.

Phase 1 step 1.4 introduces a hexagonal port for HAR / screenshot /
DOM / response-headers persistence. The default production impl is
:class:`LocalFsEvidenceArtifactStore`
(``adapters/object_stores/local_fs_evidence_store.py``); the
framework default is :class:`NoopEvidenceArtifactStore` so existing
tests pass without configuration (Phase 1 boundary acceptance,
design.md §4 Phase 1).

Surface:

* :meth:`EvidenceArtifactStorePort.put` persists ``payload`` under
  ``(run_ref, attempt_ref, kind)`` and returns an
  :class:`EvidencePutResult` carrying the deterministic
  ``artifact_ref`` + content digest + size + redaction marker.
* :meth:`EvidenceArtifactStorePort.get` retrieves bytes by
  ``artifact_ref``; returns ``None`` when absent.

The ``redaction_applied`` flag on :meth:`put` is **load-bearing**
and required for **every** kind. Semantically the producer attests
that the payload has passed the kind's safety policy:

* ``HAR`` / ``DOM`` / ``RESPONSE_HEADERS`` / ``REQUEST_HEADERS``:
  field-level structural redaction has been applied (e.g. via
  :func:`redact_har_payload`). Bytes that fail this attestation
  must never reach the store.
* ``SCREENSHOT`` / ``TRACE`` / ``OTHER``: no field-level keys exist
  to redact, but retention is governed by the Phase 6
  ``ArtifactLifecycle`` gate (TTL, customer-withdrawal purge,
  encrypted-at-rest). The producer attests
  ``redaction_applied=True`` to acknowledge that lifecycle-policy
  shape; the flag is a producer contract, not a content guarantee
  for these kinds.

Calling ``put(redaction_applied=False)`` always raises
:class:`EvidenceRedactionRequired` — there is no kind where
unattested persistence is allowed. The earlier blanket exemption
for ``SCREENSHOT`` was rejected because screenshots can capture
account UI, tokens rendered in DOM, and PII; treating them as
categorically safe creates a weak contract that leaks into Phase 6.

Path traversal hygiene is the *implementation*'s responsibility:
``run_ref`` and ``attempt_ref`` come from internal contracts but
should still be sanitised before they hit the filesystem (the
default impl uses a SHA-256 digest + safe-prefix scheme — same
pattern step 1.1 uses for ``storage_state.json``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class ArtifactKind(StrEnum):
    """Coarse category for evidence payloads.

    Values:
        HAR: HTTP Archive 1.2 JSON (Playwright ``record_har_path`` /
            equivalent).
        SCREENSHOT: PNG / JPEG bytes from ``page.screenshot``.
        DOM: serialized DOM HTML / text (post-render).
        RESPONSE_HEADERS: redacted response-header block (sidecar
            artifact for replay).
        REQUEST_HEADERS: redacted request-header block.
        TRACE: Playwright tracing zip (snapshots + screenshots).
        OTHER: catch-all for adapter-specific payloads.
    """

    HAR = "har"
    SCREENSHOT = "screenshot"
    DOM = "dom"
    RESPONSE_HEADERS = "response_headers"
    REQUEST_HEADERS = "request_headers"
    TRACE = "trace"
    OTHER = "other"


def kind_requires_redaction(kind: ArtifactKind) -> bool:
    """Return ``True`` for every kind — every put requires attestation.

    The function is kept as a public symbol because the previous
    iteration of this module exposed it for caller use (and so a
    field-level vs lifecycle-attestation distinction can be added
    later without breaking callers). For now the policy is uniform:
    ``put(redaction_applied=False)`` is always a contract violation.
    """

    del kind
    return True


class EvidenceArtifactStoreError(RuntimeError):
    """Base class for store-side errors (disk full, permission, etc.)."""


class EvidenceRedactionRequired(EvidenceArtifactStoreError):
    """Caller called ``put`` with ``redaction_applied=False`` for a
    payload kind whose plaintext form would leak credentials / PII.
    """


@dataclass(frozen=True)
class EvidencePutResult:
    """Result of a successful ``put`` call.

    Attributes:
        artifact_ref: Deterministic content-addressed identifier the
            caller stores on the surrounding evidence record (e.g.
            :class:`NetworkAttemptEvidence.har_artifact_ref`). Same
            ``run_ref`` + ``attempt_ref`` + ``kind`` + payload bytes
            always produce the same ref.
        content_digest_sha256: Hex-encoded SHA-256 of the persisted
            bytes — exposed so callers can include the digest in
            replay audit records without re-reading the artifact.
        size_bytes: Persisted size in bytes (post-redaction).
        redaction_applied: Echoes the caller's flag so audit / outbox
            records can prove redaction was performed at intake.
    """

    artifact_ref: str
    content_digest_sha256: str
    size_bytes: int
    redaction_applied: bool


@runtime_checkable
class EvidenceArtifactStorePort(Protocol):
    """Hexagonal port for per-attempt evidence persistence."""

    def put(
        self,
        *,
        run_ref: str,
        attempt_ref: str,
        kind: ArtifactKind,
        payload: bytes,
        content_type: str,
        redaction_applied: bool,
    ) -> EvidencePutResult:
        """Persist ``payload`` and return a deterministic artifact ref.

        Implementations must:

        * Refuse the call (raise :class:`EvidenceRedactionRequired`)
          when ``kind_requires_redaction(kind) and not redaction_applied``.
        * Sanitise ``run_ref`` / ``attempt_ref`` so neither can escape
          the storage root via path traversal.
        * Be safe to call from concurrent threads against the same
          store instance (atomic writes; concurrent writers must
          never observe a partial payload).
        """

    def get(self, *, artifact_ref: str) -> bytes | None:
        """Retrieve persisted bytes; return ``None`` when absent."""


class NoopEvidenceArtifactStore:
    """Permissive default — accepts every ``put`` and never reads back.

    Used when no evidence store is configured (Phase 1 boundary
    acceptance: existing tests pass without configuration). Production
    callers must inject :class:`LocalFsEvidenceArtifactStore` (or
    another real impl); the production-mode gate at adapter
    construction refuses to silently ship the no-op.

    Behavior:

    * :meth:`put` enforces the redaction-required check (so callers
      who exercise the no-op in tests still see the contract failure
      mode they would see in production).
    * :meth:`put` returns a deterministic ``artifact_ref`` keyed on
      a SHA-256 of ``payload`` so two ``put`` calls with the same
      payload produce the same ref, mirroring the production
      content-addressing semantics.
    * :meth:`get` always returns ``None`` — the no-op never persists.
    """

    def put(
        self,
        *,
        run_ref: str,
        attempt_ref: str,
        kind: ArtifactKind,
        payload: bytes,
        content_type: str,
        redaction_applied: bool,
    ) -> EvidencePutResult:
        del content_type
        if kind_requires_redaction(kind) and not redaction_applied:
            raise EvidenceRedactionRequired(f"kind={kind.value} requires redaction_applied=True")
        import hashlib

        # Scope the ref by ``run_ref + attempt_ref + kind + payload``
        # so two attempts with identical bytes still produce
        # distinct refs — same shape the production impl returns,
        # so unit tests cannot accidentally rely on a payload-only
        # ref the production store would never emit.
        scope = f"{run_ref}|{attempt_ref}|{kind.value}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        scoped_digest = hashlib.sha256(scope + b"|" + digest.encode("ascii")).hexdigest()
        return EvidencePutResult(
            artifact_ref=f"artifact:noop:{kind.value}:{scoped_digest[:16]}",
            content_digest_sha256=digest,
            size_bytes=len(payload),
            redaction_applied=redaction_applied,
        )

    def get(self, *, artifact_ref: str) -> bytes | None:
        del artifact_ref
        return None


__all__ = [
    "ArtifactKind",
    "EvidenceArtifactStoreError",
    "EvidenceArtifactStorePort",
    "EvidencePutResult",
    "EvidenceRedactionRequired",
    "NoopEvidenceArtifactStore",
    "kind_requires_redaction",
]
