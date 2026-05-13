"""``CrawlArtifactStorePort`` — unified bytes+text artifact persistence.

Used by the external crawl runtime introduced in
``docs/plans/general-purpose-crawler-goal.md``. This is a sister port
to the existing text-only ``ports.artifact_store.ArtifactStorePort``
and the bytes-only ``ports.stores.ArtifactStorePort``; both remain
untouched for backward compat with the fixture runtimes.

Every artifact carries evidence-grade metadata so the run report can
reconstruct lineage without a separate sidecar lookup.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import VeraModel

REQUIRED_METADATA_KEYS = frozenset({"source_url", "privacy_classification", "replay_ref"})


class ArtifactWriteResult(VeraModel):
    artifact_ref: str = Field(min_length=1)
    content_digest: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    content_type: str = Field(min_length=1)
    metadata: dict[str, str]
    created_at: datetime

    @field_validator("content_digest")
    @classmethod
    def validate_digest_hex(cls, value: str) -> str:
        # sha256 hex digest: exactly 64 lowercase hex chars
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("content_digest must be a 64-char lowercase sha256 hex digest")
        return value

    @field_validator("created_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_evidence_metadata(self) -> ArtifactWriteResult:
        missing = REQUIRED_METADATA_KEYS - self.metadata.keys()
        if missing:
            # Surface each missing key in the error so callers can
            # match on the specific field they forgot.
            key = sorted(missing)[0]
            raise ValueError(
                f"metadata missing required key {key!r}; "
                f"required keys are {sorted(REQUIRED_METADATA_KEYS)}"
            )
        return self


class CrawlArtifactStorePort(Protocol):
    """Persist raw bytes / text under stable, content-addressed refs.

    Implementations are expected to:
    * store the bytes under a stable layout so ``get_bytes(ref)``
      returns the exact bytes that were written;
    * compute and verify a sha256 content hash;
    * persist the supplied metadata next to the artifact so the
      run report can reconstruct it without a separate sidecar
      lookup.
    """

    def put_bytes(
        self,
        artifact_ref: str,
        data: bytes,
        *,
        content_type: str,
        metadata: dict[str, str],
    ) -> ArtifactWriteResult: ...

    def put_text(
        self,
        artifact_ref: str,
        text: str,
        *,
        content_type: str,
        metadata: dict[str, str],
    ) -> ArtifactWriteResult: ...

    def get_bytes(self, artifact_ref: str) -> bytes: ...

    def exists(self, artifact_ref: str) -> bool: ...


__all__ = [
    "REQUIRED_METADATA_KEYS",
    "ArtifactWriteResult",
    "CrawlArtifactStorePort",
]
