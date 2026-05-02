"""Deterministic artifact store used by runtime spine fixtures."""

from __future__ import annotations

from dataclasses import dataclass, field

from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import ArtifactType, OwnerService, PrivacyClassification


@dataclass
class InMemoryArtifactStore:
    """Fixture store that records content by stable artifact refs, not raw SDK state."""

    _content: dict[Ref, str] = field(default_factory=dict)
    _refs: dict[Ref, RuntimeArtifactRef] = field(default_factory=dict)

    def write(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        producer_service: OwnerService,
        source_ref: Ref,
        content: str,
        privacy_classification: PrivacyClassification = PrivacyClassification.INTERNAL,
    ) -> RuntimeArtifactRef:
        artifact_ref = RuntimeArtifactRef(
            id=artifact_id,
            artifact_type=artifact_type,
            producer_service=producer_service,
            source_ref=source_ref,
            content_digest=stable_hash(content),
            size_bytes=len(content.encode("utf-8")),
            privacy_classification=privacy_classification,
            lifecycle_state_ref=f"lifecycle:{artifact_id}:active",
            retention_policy_ref="retention:runtime-fixture",
        )
        self._content[artifact_id] = content
        self._refs[artifact_id] = artifact_ref
        return artifact_ref

    def read(self, artifact_ref: Ref) -> str | None:
        return self._content.get(artifact_ref)

    def get_ref(self, artifact_ref: Ref) -> RuntimeArtifactRef | None:
        return self._refs.get(artifact_ref)

    def list_refs(self) -> list[RuntimeArtifactRef]:
        return list(self._refs.values())
