"""Runtime normalization and extraction contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import ExtractionCandidateStatus


class NormalizedDocument(TimestampedModel):
    id: str
    run_ref: Ref
    source_adapter_result_ref: Ref
    raw_artifact_ref: Ref
    normalized_artifact_ref: Ref
    anchor_map_ref: Ref
    normalization_manifest_ref: Ref
    language_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_refs(self) -> NormalizedDocument:
        if not self.raw_artifact_ref or not self.normalized_artifact_ref or not self.anchor_map_ref:
            raise ValueError("normalized document requires raw, normalized, and anchor refs")
        return self


class ExtractionCandidate(TimestampedModel):
    id: str
    run_ref: Ref
    schema_ref: Ref
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    field_values: dict[str, object] = Field(default_factory=dict)
    field_anchor_refs: dict[str, Ref] = Field(default_factory=dict)
    confidence_refs: list[Ref] = Field(default_factory=list)
    strategy_ref: Ref
    agent_recommendation_ref: Ref | None = None
    status: ExtractionCandidateStatus = ExtractionCandidateStatus.CANDIDATE

    @model_validator(mode="after")
    def validate_candidate(self) -> ExtractionCandidate:
        if not self.normalized_document_refs:
            raise ValueError("extraction candidate requires normalized document refs")
        missing_anchors = [
            field for field in self.field_values if field not in self.field_anchor_refs
        ]
        if missing_anchors:
            raise ValueError(f"candidate fields missing anchors: {missing_anchors}")
        return self
