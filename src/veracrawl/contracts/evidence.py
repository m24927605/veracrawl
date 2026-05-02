"""Runtime evidence contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, EvidencePacketStatus


class EvidenceCoverageResult(TimestampedModel):
    id: str
    candidate_ref: Ref
    required_field_refs: list[str] = Field(default_factory=list)
    covered_field_refs: list[str] = Field(default_factory=list)
    missing_field_refs: list[str] = Field(default_factory=list)
    completeness_result: CompletenessResult

    @model_validator(mode="after")
    def validate_coverage(self) -> EvidenceCoverageResult:
        if self.completeness_result == CompletenessResult.PASS and self.missing_field_refs:
            raise ValueError("passing evidence coverage cannot have missing fields")
        return self


class EvidencePacket(TimestampedModel):
    id: str
    candidate_ref: Ref
    source_evidence_refs: list[Ref] = Field(default_factory=list)
    anchor_refs: list[Ref] = Field(default_factory=list)
    coverage_result_ref: Ref
    prior_verified_output_refs: list[Ref] = Field(default_factory=list)
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)
    agent_reasoning_refs: list[Ref] = Field(default_factory=list)
    status: EvidencePacketStatus = EvidencePacketStatus.BUILT

    @model_validator(mode="after")
    def validate_evidence(self) -> EvidencePacket:
        if not self.source_evidence_refs and not self.prior_verified_output_refs:
            raise ValueError(
                "evidence packet requires source evidence or accepted prior output refs"
            )
        if not self.anchor_refs:
            raise ValueError("evidence packet requires anchor refs")
        return self
