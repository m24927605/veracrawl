"""Runtime evidence contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    EvidencePacketStatus,
    LiveEvidenceVerificationFailureType,
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


class LiveEvidenceVerificationRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    schema_extraction_runtime_report_ref: Ref | None = None
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    evidence_manifest_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    conflict_record_refs: list[Ref] = Field(default_factory=list)
    contradiction_record_refs: list[Ref] = Field(default_factory=list)
    freshness_refs: list[Ref] = Field(default_factory=list)
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)
    agent_reasoning_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    publication_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: LiveEvidenceVerificationFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_evidence_report(self) -> LiveEvidenceVerificationRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "schema_extraction_runtime_report_ref": (
                    self.schema_extraction_runtime_report_ref
                ),
                "extraction_candidate_refs": self.extraction_candidate_refs,
                "normalized_document_refs": self.normalized_document_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "evidence_coverage_refs": self.evidence_coverage_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "evidence_manifest_refs": self.evidence_manifest_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "review_decision_refs": self.review_decision_refs,
                "freshness_refs": self.freshness_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.publication_refs
            ):
                raise ValueError(f"passing live evidence report invalid refs: {missing}")
        else:
            if not self.failure_type:
                raise ValueError("non-pass live evidence report requires failure type")
            if not (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.conflict_record_refs
                or self.contradiction_record_refs
            ):
                raise ValueError("non-pass live evidence report requires diagnostics")
        return self


class LiveEvidenceVerificationFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    schema_ref: Ref
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: LiveEvidenceVerificationFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_evidence_fixture(self) -> LiveEvidenceVerificationFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("live evidence fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("live evidence fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative live evidence fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative live evidence fixture requires failure type")
        return self
