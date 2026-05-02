"""Runtime normalization owner service."""

from __future__ import annotations

from veracrawl.artifact_lifecycle.runtime import InMemoryArtifactStore
from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.enums import ArtifactType, OwnerService
from veracrawl.contracts.objective import CrawlRun
from veracrawl.contracts.processing import NormalizedDocument
from veracrawl.contracts.source_adapter import SourceAdapterResult
from veracrawl.control.runtime import require_owner


def normalize_source_result(
    *,
    run: CrawlRun,
    source_result: SourceAdapterResult,
    raw_artifact_ref: RuntimeArtifactRef,
    artifact_store: InMemoryArtifactStore,
    owner: OwnerService = OwnerService.NORMALIZE,
) -> tuple[NormalizedDocument, list[RuntimeArtifactRef]]:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.NORMALIZE,
        target_ref=f"normalized:{run.id}",
    )
    raw_content = artifact_store.read(raw_artifact_ref.id) or ""
    normalized = artifact_store.write(
        artifact_id=f"artifact:{run.id}:normalized",
        artifact_type=ArtifactType.NORMALIZED_DOCUMENT,
        producer_service=OwnerService.NORMALIZE,
        source_ref=raw_artifact_ref.id,
        content=raw_content.lower(),
    )
    anchor_map = artifact_store.write(
        artifact_id=f"artifact:{run.id}:anchors",
        artifact_type=ArtifactType.ANCHOR_MAP,
        producer_service=OwnerService.NORMALIZE,
        source_ref=normalized.id,
        content='{"name":"$.name","price":"$.price","currency":"$.currency"}',
    )
    document = NormalizedDocument(
        id=f"normalized:{run.id}",
        run_ref=run.id,
        source_adapter_result_ref=source_result.id,
        raw_artifact_ref=raw_artifact_ref.id,
        normalized_artifact_ref=normalized.id,
        anchor_map_ref=anchor_map.id,
        normalization_manifest_ref=f"normalization-manifest:{run.id}",
        language_refs=["language:en"],
    )
    return document, [normalized, anchor_map]
