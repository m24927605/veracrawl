"""Runtime artifact reference contracts."""

from __future__ import annotations

from pydantic import model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import ArtifactType, OwnerService, PrivacyClassification


class RuntimeArtifactRef(TimestampedModel):
    id: str
    artifact_type: ArtifactType
    producer_service: OwnerService
    source_ref: Ref
    content_digest: str
    size_bytes: int
    privacy_classification: PrivacyClassification = PrivacyClassification.INTERNAL
    lifecycle_state_ref: Ref
    retention_policy_ref: Ref

    @model_validator(mode="after")
    def validate_artifact(self) -> RuntimeArtifactRef:
        if not self.content_digest:
            raise ValueError("artifact ref requires content_hash")
        if self.size_bytes < 0:
            raise ValueError("artifact size must be non-negative")
        return self
