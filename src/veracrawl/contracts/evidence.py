"""Runtime evidence contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    EvidencePacketStatus,
    PrivacyClassification,
)


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


class EvidenceAnchor(TimestampedModel):
    id: str
    evidence_packet_ref: Ref
    candidate_ref: Ref
    field_name: str
    source_artifact_ref: Ref
    normalized_document_ref: Ref
    anchor_ref: Ref
    expected_text_hash: str
    privacy_classification: PrivacyClassification = PrivacyClassification.PUBLIC
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_anchor(self) -> EvidenceAnchor:
        if not self.field_name:
            raise ValueError("evidence anchor requires field name")
        if not self.expected_text_hash:
            raise ValueError("evidence anchor requires expected text hash")
        if not self.policy_decision_refs:
            raise ValueError("evidence anchor requires policy decision refs")
        return self


class EvidencePacketManifest(TimestampedModel):
    id: str
    evidence_packet_ref: Ref
    candidate_ref: Ref
    coverage_result_ref: Ref
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    source_artifact_refs: list[Ref] = Field(default_factory=list)
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    manifest_hash: str

    @model_validator(mode="after")
    def validate_manifest(self) -> EvidencePacketManifest:
        if not self.evidence_anchor_refs:
            raise ValueError("evidence manifest requires anchor refs")
        if not self.source_artifact_refs or not self.normalized_document_refs:
            raise ValueError("evidence manifest requires source and normalized refs")
        if not self.privacy_lifecycle_refs:
            raise ValueError("evidence manifest requires privacy lifecycle refs")
        if not self.policy_decision_refs:
            raise ValueError("evidence manifest requires policy decision refs")
        if not self.manifest_hash:
            raise ValueError("evidence manifest requires manifest hash")
        return self


class EvidencePublicationFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> EvidencePublicationFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("evidence fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative evidence fixture must not expect pass")
        return self
