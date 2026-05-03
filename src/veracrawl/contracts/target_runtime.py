"""Target crawl runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AdapterType,
    AgentRecommendationSubject,
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
    TargetWebsitePattern,
)

TARGET_RUNTIME_MINIMUM_PATTERN_COUNT = 7


class TargetCrawlPatternRecord(TimestampedModel):
    id: str
    run_ref: Ref
    website_pattern: TargetWebsitePattern
    frontier_item_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    extraction_result_refs: list[Ref] = Field(default_factory=list)
    accepted_output_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)
    verification_refs: list[Ref] = Field(default_factory=list)
    graph_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    operator_visible_refs: list[Ref] = Field(default_factory=list)
    pattern_specific_refs: dict[str, Ref] = Field(default_factory=dict)
    single_site_assumption_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    unsafe_action_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_pattern_record(self) -> TargetCrawlPatternRecord:
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "frontier_item_refs": self.frontier_item_refs,
                "source_observation_refs": self.source_observation_refs,
                "source_adapter_result_refs": self.source_adapter_result_refs,
                "extraction_result_refs": self.extraction_result_refs,
                "accepted_output_refs": self.accepted_output_refs,
                "evidence_refs": self.evidence_refs,
                "verification_refs": self.verification_refs,
                "graph_refs": self.graph_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "replay_refs": self.replay_refs,
                "operator_visible_refs": self.operator_visible_refs,
                "pattern_specific_refs": self.pattern_specific_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.single_site_assumption_refs
                or self.scaffold_only_refs
                or self.unsafe_action_refs
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(f"passing target pattern record missing refs: {missing}")
        elif not (self.failure_report_refs or self.missing_ref_fields):
            raise ValueError("non-passing target pattern record requires diagnostics")
        return self


class TargetAIRecommendationRecord(TimestampedModel):
    id: str
    run_ref: Ref
    subject: AgentRecommendationSubject
    recommendation_ref: Ref
    accepted: bool
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    tool_call_refs: list[Ref] = Field(default_factory=list)
    trace_refs: list[Ref] = Field(default_factory=list)
    blocked_action_refs: list[Ref] = Field(default_factory=list)
    repair_frontier_refs: list[Ref] = Field(default_factory=list)
    framework_native_state_refs: list[Ref] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_ai_recommendation(self) -> TargetAIRecommendationRecord:
        if self.framework_native_state_refs:
            raise ValueError("target runtime cannot persist framework-native state")
        if self.accepted:
            missing = [
                name
                for name, value in {
                    "policy_decision_refs": self.policy_decision_refs,
                    "tool_call_refs": self.tool_call_refs,
                    "trace_refs": self.trace_refs,
                }.items()
                if not value
            ]
            if missing or self.result != CompletenessResult.PASS:
                raise ValueError(
                    f"accepted target AI recommendation missing refs: {missing}"
                )
        elif not (self.blocked_action_refs and self.policy_decision_refs):
            raise ValueError("blocked target AI recommendation requires policy refs")
        return self


class TargetRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    objective_ref: Ref
    plan_ref: Ref
    status: TargetRuntimeStatus
    completion_result: CompletenessResult
    covered_patterns: list[TargetWebsitePattern] = Field(default_factory=list)
    pattern_record_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    adapter_backed_source_refs: list[Ref] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    adapter_output_refs: list[Ref] = Field(default_factory=list)
    processing_evidence_refs: list[Ref] = Field(default_factory=list)
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    publication_report_refs: list[Ref] = Field(default_factory=list)
    accepted_output_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)
    verification_refs: list[Ref] = Field(default_factory=list)
    graph_refs: list[Ref] = Field(default_factory=list)
    export_receipt_refs: list[Ref] = Field(default_factory=list)
    output_manifest_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    ai_recommendation_refs: list[Ref] = Field(default_factory=list)
    repair_action_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    operator_status: str
    failure_type: TargetRuntimeFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_runtime_report(self) -> TargetRuntimeReport:
        if self.status == TargetRuntimeStatus.COMPLETE:
            required: dict[str, object] = {
                "pattern_record_refs": self.pattern_record_refs,
                "accepted_output_refs": self.accepted_output_refs,
                "evidence_refs": self.evidence_refs,
                "verification_refs": self.verification_refs,
                "graph_refs": self.graph_refs,
                "export_receipt_refs": self.export_receipt_refs,
                "output_manifest_refs": self.output_manifest_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "ai_recommendation_refs": self.ai_recommendation_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                self.completion_result != CompletenessResult.PASS
                or len(set(self.covered_patterns)) < TARGET_RUNTIME_MINIMUM_PATTERN_COUNT
                or missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(f"complete target runtime report missing refs: {missing}")
        elif self.status == TargetRuntimeStatus.NEEDS_REVIEW:
            if self.completion_result != CompletenessResult.NEEDS_REVIEW:
                raise ValueError("needs-review target runtime must use needs_review result")
            if not (self.review_item_refs or self.recovery_action_refs or self.missing_ref_fields):
                raise ValueError("needs-review target runtime requires review diagnostics")
        elif self.status in {TargetRuntimeStatus.BLOCKED, TargetRuntimeStatus.FAILED}:
            if self.completion_result != CompletenessResult.FAIL:
                raise ValueError("blocked/failed target runtime must fail completeness")
            if not (self.failure_type and self.failure_report_refs):
                raise ValueError("blocked/failed target runtime requires failure refs")
        return self


class TargetRuntimeFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    source_corpus_ref: Ref | None = None
    adapter_backed_source_ref: Ref | None = None
    processing_evidence_ref: Ref | None = None
    expected_status: TargetRuntimeStatus
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: TargetRuntimeFailureType | None = None
    expected_pattern_count: int = 0
    expected_source_observation_count: int = 0
    expected_adapter_result_count: int = 0
    expected_processing_evidence_count: int = 0
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_target_runtime_fixture(self) -> TargetRuntimeFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("target runtime fixture must support target profile")
        if (
            self.expected_status == TargetRuntimeStatus.COMPLETE
            and self.expected_pattern_count < TARGET_RUNTIME_MINIMUM_PATTERN_COUNT
        ):
            raise ValueError("complete target runtime fixture must cover target patterns")
        if self.negative_case:
            if self.expected_status not in {
                TargetRuntimeStatus.BLOCKED,
                TargetRuntimeStatus.FAILED,
            }:
                raise ValueError("negative target runtime fixture must block or fail")
            if self.expected_failure_type is None:
                raise ValueError("negative target runtime fixture requires failure type")
        return self


class TargetSourceCorpusEntry(TimestampedModel):
    id: str
    website_pattern: TargetWebsitePattern
    source_path: str
    content_type: str
    expected_fields: dict[str, str] = Field(default_factory=dict)
    evidence_markers: dict[str, str] = Field(default_factory=dict)
    policy_decision_ref: Ref
    allowed: bool = True
    contains_prompt_injection: bool = False
    requires_export_ref: bool = True
    expected_content_hash_ref: Ref | None = None
    drift_aliases: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_corpus_entry(self) -> TargetSourceCorpusEntry:
        has_required_source = self.source_path and self.expected_fields and self.evidence_markers
        if self.allowed and not has_required_source:
            raise ValueError("allowed source corpus entry requires source and evidence fields")
        if not self.policy_decision_ref:
            raise ValueError("source corpus entry requires policy decision ref")
        if self.content_type not in {"html", "json", "text"}:
            raise ValueError("unsupported source corpus content type")
        return self


class TargetSourceCorpusManifest(TimestampedModel):
    id: str
    fixture_id: str
    entries: list[TargetSourceCorpusEntry] = Field(default_factory=list)
    expected_pattern_count: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_oracle_ref: Ref
    export_complete: bool = True

    @model_validator(mode="after")
    def validate_source_corpus_manifest(self) -> TargetSourceCorpusManifest:
        entry_ids = [entry.id for entry in self.entries]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("source corpus entry ids must be unique")
        has_target_pattern_count = (
            self.expected_pattern_count >= TARGET_RUNTIME_MINIMUM_PATTERN_COUNT
        )
        if self.export_complete and has_target_pattern_count:
            if len(self.entries) < TARGET_RUNTIME_MINIMUM_PATTERN_COUNT:
                raise ValueError("passing source corpus requires target pattern coverage")
        if not self.policy_decision_refs:
            raise ValueError("source corpus manifest requires policy refs")
        return self


class TargetSourceObservationRecord(TimestampedModel):
    id: str
    run_ref: Ref
    corpus_entry_ref: Ref
    website_pattern: TargetWebsitePattern
    source_path_ref: Ref
    content_hash_ref: Ref | None = None
    source_observation_ref: Ref | None = None
    artifact_ref: Ref | None = None
    extracted_field_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)
    graph_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    missing_field_refs: list[Ref] = Field(default_factory=list)
    prompt_injection_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_source_observation(self) -> TargetSourceObservationRecord:
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "content_hash_ref": self.content_hash_ref,
                "source_observation_ref": self.source_observation_ref,
                "artifact_ref": self.artifact_ref,
                "extracted_field_refs": self.extracted_field_refs,
                "evidence_refs": self.evidence_refs,
                "graph_refs": self.graph_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_refs": self.replay_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.missing_field_refs
                or self.prompt_injection_refs
                or self.failure_report_refs
            ):
                raise ValueError(f"passing source observation missing refs: {missing}")
        else:
            has_failure_diagnostics = (
                self.missing_field_refs
                or self.prompt_injection_refs
                or self.failure_report_refs
            )
            if not has_failure_diagnostics:
                raise ValueError("failed source observation requires diagnostics")
        return self


class TargetAdapterBackedSourceEntry(TimestampedModel):
    id: str
    corpus_entry_ref: Ref
    adapter_type: AdapterType
    adapter_spec_ref: Ref
    adapter_source_ref: Ref
    policy_decision_ref: Ref
    expected_output_ref: Ref | None = None
    expected_content_hash_ref: Ref | None = None
    require_source_adapter_result: bool = True
    allow_direct_source_fallback: bool = False
    policy_denied: bool = False
    simulate_missing_adapter_result: bool = False
    simulate_direct_source_bypass: bool = False

    @model_validator(mode="after")
    def validate_adapter_backed_entry(self) -> TargetAdapterBackedSourceEntry:
        if not (self.adapter_spec_ref and self.adapter_source_ref and self.policy_decision_ref):
            raise ValueError("adapter-backed source entry requires adapter and policy refs")
        simulated_negative = (
            self.simulate_missing_adapter_result or self.simulate_direct_source_bypass
        )
        if (
            not self.require_source_adapter_result
            and not self.allow_direct_source_fallback
            and not simulated_negative
        ):
            raise ValueError("adapter-backed source entry cannot omit adapter result proof")
        return self


class TargetAdapterBackedSourceManifest(TimestampedModel):
    id: str
    fixture_id: str
    entries: list[TargetAdapterBackedSourceEntry] = Field(default_factory=list)
    required_adapter_types: list[AdapterType] = Field(default_factory=list)
    expected_adapter_result_count: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_oracle_ref: Ref
    allow_direct_source_fallback: bool = False

    @model_validator(mode="after")
    def validate_adapter_backed_manifest(self) -> TargetAdapterBackedSourceManifest:
        corpus_refs = [entry.corpus_entry_ref for entry in self.entries]
        if len(corpus_refs) != len(set(corpus_refs)):
            raise ValueError("adapter-backed source corpus refs must be unique")
        if self.expected_adapter_result_count > 0 and not self.required_adapter_types:
            raise ValueError("adapter-backed source manifest requires adapter types")
        if not self.policy_decision_refs:
            raise ValueError("adapter-backed source manifest requires policy refs")
        if self.allow_direct_source_fallback:
            raise ValueError("adapter-backed source manifest cannot allow direct fallback")
        return self


class TargetAdapterBackedSourceRecord(TimestampedModel):
    id: str
    run_ref: Ref
    corpus_entry_ref: Ref
    adapter_type: AdapterType
    source_adapter_result_ref: Ref | None = None
    adapter_output_refs: list[Ref] = Field(default_factory=list)
    adapter_policy_decision_refs: list[Ref] = Field(default_factory=list)
    adapter_replay_refs: list[Ref] = Field(default_factory=list)
    source_observation_ref: Ref | None = None
    content_hash_ref: Ref | None = None
    direct_source_bypass_refs: list[Ref] = Field(default_factory=list)
    missing_adapter_result_refs: list[Ref] = Field(default_factory=list)
    adapter_output_mismatch_refs: list[Ref] = Field(default_factory=list)
    policy_denied_refs: list[Ref] = Field(default_factory=list)
    replay_mismatch_refs: list[Ref] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_adapter_backed_record(self) -> TargetAdapterBackedSourceRecord:
        diagnostics = (
            self.direct_source_bypass_refs
            or self.missing_adapter_result_refs
            or self.adapter_output_mismatch_refs
            or self.policy_denied_refs
            or self.replay_mismatch_refs
        )
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_adapter_result_ref": self.source_adapter_result_ref,
                "adapter_output_refs": self.adapter_output_refs,
                "adapter_policy_decision_refs": self.adapter_policy_decision_refs,
                "adapter_replay_refs": self.adapter_replay_refs,
                "source_observation_ref": self.source_observation_ref,
                "content_hash_ref": self.content_hash_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or diagnostics:
                raise ValueError(f"passing adapter-backed source missing refs: {missing}")
        elif not diagnostics:
            raise ValueError("failed adapter-backed source requires typed diagnostics")
        return self


class TargetProcessingEvidenceEntry(TimestampedModel):
    id: str
    corpus_entry_ref: Ref
    adapter_backed_source_ref: Ref
    required_field_refs: list[Ref] = Field(default_factory=list)
    policy_decision_ref: Ref
    simulate_missing_normalization: bool = False
    simulate_missing_candidate_anchor: bool = False
    simulate_missing_evidence_packet: bool = False
    simulate_graph_only_evidence: bool = False
    simulate_publication_bypass: bool = False

    @model_validator(mode="after")
    def validate_processing_entry(self) -> TargetProcessingEvidenceEntry:
        if not self.adapter_backed_source_ref:
            raise ValueError("processing evidence entry requires adapter-backed source ref")
        if not self.required_field_refs:
            raise ValueError("processing evidence entry requires field refs")
        if not self.policy_decision_ref:
            raise ValueError("processing evidence entry requires policy ref")
        return self


class TargetProcessingEvidenceManifest(TimestampedModel):
    id: str
    fixture_id: str
    entries: list[TargetProcessingEvidenceEntry] = Field(default_factory=list)
    expected_processing_evidence_count: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_oracle_ref: Ref

    @model_validator(mode="after")
    def validate_processing_manifest(self) -> TargetProcessingEvidenceManifest:
        corpus_refs = [entry.corpus_entry_ref for entry in self.entries]
        if self.expected_processing_evidence_count < 0:
            raise ValueError("processing evidence count cannot be negative")
        if len(corpus_refs) != len(set(corpus_refs)):
            raise ValueError("processing evidence corpus refs must be unique")
        if self.expected_processing_evidence_count > 0 and not self.entries:
            raise ValueError("processing evidence manifest requires entries")
        if self.expected_processing_evidence_count > len(self.entries):
            raise ValueError("processing evidence count cannot exceed entries")
        if not self.policy_decision_refs:
            raise ValueError("processing evidence manifest requires policy refs")
        return self


class TargetProcessingEvidenceRecord(TimestampedModel):
    id: str
    run_ref: Ref
    corpus_entry_ref: Ref
    adapter_backed_source_ref: Ref
    source_observation_ref: Ref | None = None
    adapter_output_refs: list[Ref] = Field(default_factory=list)
    normalized_document_ref: Ref | None = None
    extraction_candidate_ref: Ref | None = None
    candidate_anchor_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_ref: Ref | None = None
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    publication_report_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    graph_only_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_normalization_refs: list[Ref] = Field(default_factory=list)
    missing_candidate_anchor_refs: list[Ref] = Field(default_factory=list)
    missing_evidence_packet_refs: list[Ref] = Field(default_factory=list)
    publication_bypass_refs: list[Ref] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_processing_record(self) -> TargetProcessingEvidenceRecord:
        diagnostics = (
            self.graph_only_evidence_refs
            or self.missing_normalization_refs
            or self.missing_candidate_anchor_refs
            or self.missing_evidence_packet_refs
            or self.publication_bypass_refs
        )
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_observation_ref": self.source_observation_ref,
                "adapter_output_refs": self.adapter_output_refs,
                "normalized_document_ref": self.normalized_document_ref,
                "extraction_candidate_ref": self.extraction_candidate_ref,
                "candidate_anchor_refs": self.candidate_anchor_refs,
                "evidence_packet_ref": self.evidence_packet_ref,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "publication_report_ref": self.publication_report_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_refs": self.replay_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or diagnostics:
                raise ValueError(f"passing processing evidence missing refs: {missing}")
        elif not diagnostics:
            raise ValueError("failed processing evidence requires typed diagnostics")
        return self
