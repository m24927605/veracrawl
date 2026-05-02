"""Artifact store port for runtime fixtures and future storage adapters."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import ArtifactType, OwnerService, PrivacyClassification


class ArtifactStorePort(Protocol):
    def write(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        producer_service: OwnerService,
        source_ref: Ref,
        content: str,
        privacy_classification: PrivacyClassification = PrivacyClassification.INTERNAL,
    ) -> RuntimeArtifactRef: ...

    def read(self, artifact_ref: Ref) -> str | None: ...
