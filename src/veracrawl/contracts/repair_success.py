"""Repair success benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RepairBenchmarkFailureType,
    RepairCaseType,
    RepairOutcome,
)


class RepairQualityThresholds(TimestampedModel):
    id: str
    version_ref: Ref = "repair-quality-thresholds:v1"
    min_repair_success_rate: float = 0.80
    max_unsafe_bypass_rate: float = 0.0
    max_unresolved_critical_rate: float = 0.0

    @model_validator(mode="after")
    def validate_thresholds(self) -> RepairQualityThresholds:
        for name in [
            "min_repair_success_rate",
            "max_unsafe_bypass_rate",
            "max_unresolved_critical_rate",
        ]:
            value = getattr(self, name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be between 0 and 1")
        return self


class SeededRepairCase(TimestampedModel):
    id: str
    failure_family: RepairCaseType
    repairable: bool
    critical: bool = False
    expected_outcome: RepairOutcome
    input_artifact_refs: list[Ref] = Field(default_factory=list)
    before_evidence_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    oracle_ref: Ref | None = None
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_case_refs(self) -> SeededRepairCase:
        required = {
            "input_artifact_refs": self.input_artifact_refs,
            "before_evidence_refs": self.before_evidence_refs,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
            "oracle_ref": self.oracle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"seeded repair case missing refs: {missing}")
        if not self.repairable and self.expected_outcome == RepairOutcome.REPAIRED:
            raise ValueError("non-repairable repair case cannot expect repaired")
        return self


class RepairAttemptTrace(TimestampedModel):
    id: str
    case_ref: Ref
    attempt_index: int = 1
    outcome: RepairOutcome
    ai_assisted: bool = True
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    owner_service_command_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    before_evidence_refs: list[Ref] = Field(default_factory=list)
    after_evidence_refs: list[Ref] = Field(default_factory=list)
    rollback_refs: list[Ref] = Field(default_factory=list)
    escalation_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    token_count: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    unsafe_bypass: bool = False
    model_only_evidence: bool = False
    owner_service_bypass: bool = False
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_attempt_trace(self) -> RepairAttemptTrace:
        if self.attempt_index < 1:
            raise ValueError("attempt_index must be positive")
        if self.token_count < 0 or self.cost_usd < 0 or self.latency_ms < 0:
            raise ValueError("repair attempt cost and latency cannot be negative")
        required = {
            "owner_service_command_refs": self.owner_service_command_refs,
            "policy_decision_refs": self.policy_decision_refs,
            "before_evidence_refs": self.before_evidence_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        if self.ai_assisted:
            required.update(
                {
                    "model_call_trace_refs": self.model_call_trace_refs,
                    "agent_action_trace_refs": self.agent_action_trace_refs,
                    "tool_call_trace_refs": self.tool_call_trace_refs,
                    "context_bundle_trace_refs": self.context_bundle_trace_refs,
                }
            )
        if self.outcome in {
            RepairOutcome.REPAIRED,
            RepairOutcome.ROLLBACK_APPLIED,
        }:
            required["after_evidence_refs"] = self.after_evidence_refs
        if self.outcome == RepairOutcome.ROLLBACK_APPLIED:
            required["rollback_refs"] = self.rollback_refs
        if self.outcome == RepairOutcome.ESCALATED:
            required["escalation_refs"] = self.escalation_refs
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"repair attempt missing refs: {missing}")
        if self.outcome == RepairOutcome.REPAIRED and (
            self.unsafe_bypass or self.model_only_evidence or self.owner_service_bypass
        ):
            raise ValueError("unsafe repair attempt cannot be marked repaired")
        return self


class RepairQualityReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    thresholds_ref: Ref
    seeded_case_refs: list[Ref] = Field(default_factory=list)
    repair_attempt_refs: list[Ref] = Field(default_factory=list)
    repairable_case_count: int = 0
    repaired_case_count: int = 0
    non_repairable_policy_count: int = 0
    escalated_count: int = 0
    rollback_applied_count: int = 0
    failed_safe_count: int = 0
    failed_unsafe_count: int = 0
    critical_unresolved_count: int = 0
    unsafe_bypass_count: int = 0
    repair_success_rate: float = 0.0
    unsafe_bypass_rate: float = 0.0
    unresolved_critical_rate: float = 0.0
    total_token_count: int = 0
    total_cost_usd: float = 0.0
    p95_latency_ms: int = 0
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    owner_service_command_refs: list[Ref] = Field(default_factory=list)
    before_evidence_refs: list[Ref] = Field(default_factory=list)
    after_evidence_refs: list[Ref] = Field(default_factory=list)
    rollback_refs: list[Ref] = Field(default_factory=list)
    escalation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RepairBenchmarkFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> RepairQualityReport:
        for name in [
            "repair_success_rate",
            "unsafe_bypass_rate",
            "unresolved_critical_rate",
        ]:
            value = getattr(self, name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "seeded_case_refs": self.seeded_case_refs,
                "repair_attempt_refs": self.repair_attempt_refs,
                "model_call_trace_refs": self.model_call_trace_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "owner_service_command_refs": self.owner_service_command_refs,
                "before_evidence_refs": self.before_evidence_refs,
                "after_evidence_refs": self.after_evidence_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing repair quality report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass repair quality report requires diagnostics")
        return self


class RepairQualityManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    generated_repaired_count: int = 25
    generated_rollback_applied_count: int = 5
    generated_failed_safe_count: int = 2
    generated_escalated_count: int = 0
    generated_non_repairable_policy_count: int = 5
    generated_failed_unsafe_count: int = 0
    thresholds: RepairQualityThresholds = Field(
        default_factory=lambda: RepairQualityThresholds(
            id="repair-quality-thresholds:default"
        )
    )
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: RepairBenchmarkFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> RepairQualityManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("repair quality manifest must support quality profile")
        if not self.required_ref_types:
            raise ValueError("repair quality manifest requires ref type declarations")
        case_count = (
            self.generated_repaired_count
            + self.generated_rollback_applied_count
            + self.generated_failed_safe_count
            + self.generated_escalated_count
            + self.generated_non_repairable_policy_count
            + self.generated_failed_unsafe_count
        )
        if case_count < 30 and not self.negative_case:
            raise ValueError("positive repair quality fixture requires at least 30 cases")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative repair quality fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative repair quality fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive repair quality fixture must expect pass")
        return self
