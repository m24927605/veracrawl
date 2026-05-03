"""Real-world AI agent benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldAIAgentBenchmarkFailureType,
    RealWorldAIAgentDecisionType,
)

_REQUIRED_DECISIONS: frozenset[RealWorldAIAgentDecisionType] = frozenset(
    RealWorldAIAgentDecisionType
)


class RealWorldAIAgentDecisionTrace(TimestampedModel):
    id: str
    benchmark_fixture_id: str
    site_observation_ref: Ref
    target_url: str
    decision_type: RealWorldAIAgentDecisionType
    model_request_ref: Ref | None = None
    model_response_ref: Ref | None = None
    model_call_trace_ref: Ref | None = None
    agent_run_request_ref: Ref | None = None
    agent_run_result_ref: Ref | None = None
    agent_action_trace_ref: Ref | None = None
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_ref: Ref | None = None
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    decision_output_ref: Ref | None = None
    framework_native_state_refs: list[Ref] = Field(default_factory=list)
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldAIAgentBenchmarkFailureType | None = None
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decision(self) -> RealWorldAIAgentDecisionTrace:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "model_request_ref": self.model_request_ref,
                "model_response_ref": self.model_response_ref,
                "model_call_trace_ref": self.model_call_trace_ref,
                "agent_run_request_ref": self.agent_run_request_ref,
                "agent_run_result_ref": self.agent_run_result_ref,
                "agent_action_trace_ref": self.agent_action_trace_ref,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_ref": self.context_bundle_trace_ref,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
                "decision_output_ref": self.decision_output_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.framework_native_state_refs
                or self.llm_output_evidence_refs
            ):
                raise ValueError(f"passing AI decision missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass AI decision requires typed diagnostics")
        return self


class RealWorldAIAgentExtractionCandidate(TimestampedModel):
    id: str
    benchmark_fixture_id: str
    site_observation_ref: Ref
    target_url: str
    candidate_payload_ref: Ref | None = None
    field_anchor_refs: dict[str, Ref] = Field(default_factory=dict)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_ref: Ref | None = None
    agent_action_trace_ref: Ref | None = None
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_ref: Ref | None = None
    evidence_coverage_ref: Ref | None = None
    evidence_packet_ref: Ref | None = None
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    publication_gate_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    direct_publication_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldAIAgentBenchmarkFailureType | None = None
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_candidate(self) -> RealWorldAIAgentExtractionCandidate:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "candidate_payload_ref": self.candidate_payload_ref,
                "field_anchor_refs": self.field_anchor_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "model_call_trace_ref": self.model_call_trace_ref,
                "agent_action_trace_ref": self.agent_action_trace_ref,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_ref": self.context_bundle_trace_ref,
                "evidence_coverage_ref": self.evidence_coverage_ref,
                "evidence_packet_ref": self.evidence_packet_ref,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "review_decision_refs": self.review_decision_refs,
                "publication_gate_ref": self.publication_gate_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            anchor_gap = [
                ref
                for ref in self.field_anchor_refs.values()
                if ref not in set(self.source_anchor_refs)
            ]
            if (
                missing
                or anchor_gap
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.llm_output_evidence_refs
                or self.direct_publication_refs
            ):
                raise ValueError(
                    "passing AI extraction candidate has invalid refs: "
                    f"missing={missing}, anchor_gap={anchor_gap}"
                )
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass AI extraction candidate requires diagnostics")
        return self


class RealWorldAIAgentBenchmarkRunReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    real_world_benchmark_run_report_ref: Ref | None = None
    site_observation_refs: list[Ref] = Field(default_factory=list)
    live_http_report_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    crawl_planning_decision_refs: list[Ref] = Field(default_factory=list)
    site_understanding_decision_refs: list[Ref] = Field(default_factory=list)
    extraction_candidate_decision_refs: list[Ref] = Field(default_factory=list)
    verification_repair_decision_refs: list[Ref] = Field(default_factory=list)
    decision_trace_refs: list[Ref] = Field(default_factory=list)
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    requested_provider_names: list[str] = Field(default_factory=list)
    verified_provider_names: list[str] = Field(default_factory=list)
    requested_framework_names: list[str] = Field(default_factory=list)
    verified_framework_names: list[str] = Field(default_factory=list)
    model_request_refs: list[Ref] = Field(default_factory=list)
    model_response_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_run_request_refs: list[Ref] = Field(default_factory=list)
    agent_run_result_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    direct_publication_refs: list[Ref] = Field(default_factory=list)
    framework_native_state_refs: list[Ref] = Field(default_factory=list)
    core_import_violation_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldAIAgentBenchmarkFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self) -> RealWorldAIAgentBenchmarkRunReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "real_world_benchmark_run_report_ref": (
                    self.real_world_benchmark_run_report_ref
                ),
                "site_observation_refs": self.site_observation_refs,
                "live_http_report_refs": self.live_http_report_refs,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "crawl_planning_decision_refs": self.crawl_planning_decision_refs,
                "site_understanding_decision_refs": (
                    self.site_understanding_decision_refs
                ),
                "extraction_candidate_decision_refs": (
                    self.extraction_candidate_decision_refs
                ),
                "verification_repair_decision_refs": (
                    self.verification_repair_decision_refs
                ),
                "decision_trace_refs": self.decision_trace_refs,
                "extraction_candidate_refs": self.extraction_candidate_refs,
                "evidence_coverage_refs": self.evidence_coverage_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "review_decision_refs": self.review_decision_refs,
                "publication_gate_refs": self.publication_gate_refs,
                "verified_provider_names": self.verified_provider_names,
                "verified_framework_names": self.verified_framework_names,
                "model_request_refs": self.model_request_refs,
                "model_response_refs": self.model_response_refs,
                "model_call_trace_refs": self.model_call_trace_refs,
                "agent_run_request_refs": self.agent_run_request_refs,
                "agent_run_result_refs": self.agent_run_result_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            provider_gap = set(self.requested_provider_names) - set(
                self.verified_provider_names
            )
            framework_gap = set(self.requested_framework_names) - set(
                self.verified_framework_names
            )
            if (
                missing
                or provider_gap
                or framework_gap
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.llm_output_evidence_refs
                or self.direct_publication_refs
                or self.framework_native_state_refs
                or self.core_import_violation_refs
            ):
                raise ValueError(
                    "passing real-world AI benchmark report invalid refs: "
                    f"missing={missing}, providers={sorted(provider_gap)}, "
                    f"frameworks={sorted(framework_gap)}"
                )
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.llm_output_evidence_refs
                or self.direct_publication_refs
                or self.framework_native_state_refs
                or self.core_import_violation_refs
            )
            and self.diagnostics
        ):
            raise ValueError("non-pass AI benchmark report requires diagnostics")
        return self


class RealWorldAIAgentBenchmarkManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    real_world_corpus_fixture_path: str
    provider_names: list[str] = Field(default_factory=list)
    framework_names: list[str] = Field(default_factory=list)
    required_decision_types: list[RealWorldAIAgentDecisionType] = Field(
        default_factory=list
    )
    required_public_site_count: int = 4
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: RealWorldAIAgentBenchmarkFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> RealWorldAIAgentBenchmarkManifest:
        if "target" not in self.profile_refs:
            raise ValueError("real-world AI benchmark must support target profile")
        if not self.real_world_corpus_fixture_path:
            raise ValueError("real-world AI benchmark requires row 055 corpus path")
        if not self.provider_names or not self.framework_names:
            raise ValueError("real-world AI benchmark requires adapter declarations")
        if set(self.required_decision_types) != _REQUIRED_DECISIONS:
            raise ValueError("real-world AI benchmark requires all decision types")
        if self.required_public_site_count < 1:
            raise ValueError("required public site count must be positive")
        if not self.required_ref_types:
            raise ValueError("real-world AI benchmark requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative real-world AI benchmark cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative real-world AI benchmark requires failure type")
        return self
