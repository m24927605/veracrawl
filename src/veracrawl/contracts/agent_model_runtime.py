"""Integrated real agent/model adapter runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AgentModelAdapterRuntimeFailureType, CompletenessResult


class AgentModelAdapterRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    run_control_report_ref: Ref | None = None
    live_normalization_runtime_report_ref: Ref | None = None
    schema_extraction_runtime_report_ref: Ref | None = None
    planning_agent_run_refs: list[Ref] = Field(default_factory=list)
    extraction_agent_run_refs: list[Ref] = Field(default_factory=list)
    repair_agent_run_refs: list[Ref] = Field(default_factory=list)
    provider_execution_refs: list[Ref] = Field(default_factory=list)
    framework_execution_refs: list[Ref] = Field(default_factory=list)
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
    adapter_runtime_refs: list[Ref] = Field(default_factory=list)
    adapter_availability_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    unavailable_runtime_refs: list[Ref] = Field(default_factory=list)
    unsupported_provider_refs: list[Ref] = Field(default_factory=list)
    unsupported_framework_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_leak_refs: list[Ref] = Field(default_factory=list)
    raw_response_leak_refs: list[Ref] = Field(default_factory=list)
    raw_credential_leak_refs: list[Ref] = Field(default_factory=list)
    framework_state_canonical_refs: list[Ref] = Field(default_factory=list)
    provider_transcript_canonical_refs: list[Ref] = Field(default_factory=list)
    core_import_violation_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: AgentModelAdapterRuntimeFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self) -> AgentModelAdapterRuntimeReport:
        failure_refs = (
            self.unavailable_runtime_refs
            + self.unsupported_provider_refs
            + self.unsupported_framework_refs
            + self.raw_prompt_leak_refs
            + self.raw_response_leak_refs
            + self.raw_credential_leak_refs
            + self.framework_state_canonical_refs
            + self.provider_transcript_canonical_refs
            + self.core_import_violation_refs
            + self.failure_report_refs
        )
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "run_control_report_ref": self.run_control_report_ref,
                "live_normalization_runtime_report_ref": (
                    self.live_normalization_runtime_report_ref
                ),
                "schema_extraction_runtime_report_ref": (
                    self.schema_extraction_runtime_report_ref
                ),
                "planning_agent_run_refs": self.planning_agent_run_refs,
                "extraction_agent_run_refs": self.extraction_agent_run_refs,
                "repair_agent_run_refs": self.repair_agent_run_refs,
                "provider_execution_refs": self.provider_execution_refs,
                "framework_execution_refs": self.framework_execution_refs,
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
                "adapter_runtime_refs": self.adapter_runtime_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields or failure_refs or self.failure_type:
                raise ValueError(
                    "passing agent/model adapter runtime report has unresolved refs: "
                    f"{missing}"
                )
            provider_gap = set(self.requested_provider_names) - set(
                self.verified_provider_names
            )
            framework_gap = set(self.requested_framework_names) - set(
                self.verified_framework_names
            )
            if provider_gap or framework_gap:
                raise ValueError(
                    "passing agent/model adapter runtime report has adapter gaps: "
                    f"providers={sorted(provider_gap)}, frameworks={sorted(framework_gap)}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.unavailable_runtime_refs or self.adapter_availability_refs):
                raise ValueError("needs-review adapter runtime requires availability refs")
        elif self.failure_type is None:
            raise ValueError("failed adapter runtime report requires failure_type")
        elif not (failure_refs or self.missing_ref_fields):
            raise ValueError("failed adapter runtime report requires failure details")
        return self


class AgentModelAdapterFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    provider_names: list[str] = Field(default_factory=list)
    framework_names: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: AgentModelAdapterRuntimeFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> AgentModelAdapterFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("agent/model adapter fixture must support target profile")
        if self.negative_case and self.expected_completion_result == CompletenessResult.PASS:
            raise ValueError("negative agent/model adapter fixture cannot expect pass")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
