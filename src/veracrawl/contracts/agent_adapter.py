"""Agent runtime adapter operational gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AgentAdapterFailureType, CompletenessResult

REQUIRED_AGENT_FRAMEWORKS = (
    "OpenAI Agent SDK",
    "LangChain",
    "LangGraph",
    "CrewAI",
    "AutoGen",
    "Semantic Kernel",
    "FutureFramework",
)


class AgentAdapterExecutionRecord(TimestampedModel):
    id: str
    framework_name: str
    runtime_spec_ref: Ref
    agent_run_request_ref: Ref
    agent_run_result_ref: Ref
    agent_action_trace_ref: Ref
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_ref: Ref
    command_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    live_runtime_refs: list[Ref] = Field(default_factory=list)
    contract_adapter_refs: list[Ref] = Field(default_factory=list)
    diagnostic_framework_state_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    framework_state_canonical: bool = False
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_execution_record(self) -> AgentAdapterExecutionRecord:
        if self.raw_prompt_persisted:
            raise ValueError("agent adapter execution cannot persist raw prompt")
        if self.raw_response_persisted:
            raise ValueError("agent adapter execution cannot persist raw response")
        if self.framework_state_canonical:
            raise ValueError("framework-native state cannot be canonical")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "runtime_spec_ref": self.runtime_spec_ref,
                "agent_run_request_ref": self.agent_run_request_ref,
                "agent_run_result_ref": self.agent_run_result_ref,
                "agent_action_trace_ref": self.agent_action_trace_ref,
                "model_call_trace_refs": self.model_call_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_ref": self.context_bundle_trace_ref,
                "command_result_refs": self.command_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing adapter execution missing refs: {missing}")
            if not (self.live_runtime_refs or self.contract_adapter_refs):
                raise ValueError("passing adapter execution requires runtime or contract refs")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_adapter_refs or self.missing_ref_fields):
                raise ValueError("needs-review adapter execution requires review refs")
        return self


class AgentRuntimeAdapterReport(TimestampedModel):
    id: str
    run_ref: Ref
    framework_execution_refs: list[Ref] = Field(default_factory=list)
    required_framework_names: list[str] = Field(
        default_factory=lambda: list(REQUIRED_AGENT_FRAMEWORKS)
    )
    verified_framework_names: list[str] = Field(default_factory=list)
    model_provider_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_leak_refs: list[Ref] = Field(default_factory=list)
    raw_response_leak_refs: list[Ref] = Field(default_factory=list)
    framework_state_canonical_refs: list[Ref] = Field(default_factory=list)
    unsupported_framework_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> AgentRuntimeAdapterReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "framework_execution_refs": self.framework_execution_refs,
                "model_provider_refs": self.model_provider_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            framework_gap = set(self.required_framework_names) - set(
                self.verified_framework_names
            )
            if (
                missing
                or framework_gap
                or self.contract_only_refs
                or self.missing_runtime_refs
                or self.raw_prompt_leak_refs
                or self.raw_response_leak_refs
                or self.framework_state_canonical_refs
                or self.unsupported_framework_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    "passing agent runtime adapter report missing refs: "
                    f"{missing}, framework_gap={sorted(framework_gap)}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review adapter report requires review refs")
        elif not (
            self.raw_prompt_leak_refs
            or self.raw_response_leak_refs
            or self.framework_state_canonical_refs
            or self.unsupported_framework_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed adapter report requires failure details")
        return self


class AgentRuntimeAdapterFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: AgentAdapterFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> AgentRuntimeAdapterFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("agent runtime adapter fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative agent runtime adapter fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
