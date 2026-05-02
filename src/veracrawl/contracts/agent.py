"""Framework-neutral agent runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AgentRecommendationStatus,
    AgentRecommendationSubject,
    AgentRole,
    AgentRunStatus,
    FrameworkStatePersistence,
    RuntimeType,
    ToolCallStatus,
    ToolType,
)


class AgentToolSpec(TimestampedModel):
    id: str
    name: str
    version: str
    tool_type: ToolType
    allowed_agent_roles: list[AgentRole]
    input_schema_ref: Ref
    output_schema_ref: Ref
    approval_required: bool = False
    policy_refs: list[Ref] = Field(default_factory=list)


class AgentRuntimeSpec(TimestampedModel):
    id: str
    name: str
    version: str
    implementation_language: str = "python"
    runtime_type: RuntimeType
    adapter_name: str
    allowed_agent_roles: list[AgentRole]
    supported_tool_protocols: list[str] = Field(default_factory=list)
    context_ref_schema: Ref
    command_envelope_schema_ref: Ref
    event_schema_ref: Ref
    policy_refs: list[Ref] = Field(default_factory=list)
    framework_state_persistence: FrameworkStatePersistence
    replay_contract_ref: Ref

    @model_validator(mode="after")
    def validate_language(self) -> AgentRuntimeSpec:
        if self.implementation_language != "python":
            raise ValueError("agent runtimes must be Python")
        return self


class ContextRef(TimestampedModel):
    id: str
    ref_type: str
    target_ref: Ref
    trust_level: str
    taint_labels: list[str] = Field(default_factory=list)
    redaction_policy_ref: Ref
    retention_policy_ref: Ref


class ContextBundle(TimestampedModel):
    id: str
    run_id: str
    context_refs: list[Ref] = Field(default_factory=list)
    sanitized_context_ref: Ref
    excluded_context_refs: list[Ref] = Field(default_factory=list)
    exclusion_reasons: list[str] = Field(default_factory=list)
    credential_exposure_check_ref: Ref
    prompt_injection_policy_ref: Ref

    @model_validator(mode="after")
    def validate_exclusions(self) -> ContextBundle:
        if self.excluded_context_refs and not self.exclusion_reasons:
            raise ValueError("excluded context refs require exclusion reasons")
        return self


class AgentRunRequest(TimestampedModel):
    id: str
    run_id: str
    agent_role: AgentRole
    runtime_spec_id: str
    objective_ref: Ref
    context_bundle_id: str
    allowed_tool_spec_refs: list[Ref] = Field(default_factory=list)
    required_output_schema_ref: Ref
    loop_budget_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)


class AgentRunResult(TimestampedModel):
    id: str
    agent_run_request_id: str
    agent_action_trace_id: str
    output_ref: Ref
    proposed_tool_call_refs: list[Ref] = Field(default_factory=list)
    recommendation_refs: list[Ref] = Field(default_factory=list)
    status: AgentRunStatus
    error: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self) -> AgentRunResult:
        if self.status == AgentRunStatus.COMPLETED and not self.agent_action_trace_id:
            raise ValueError("completed agent runs require agent_action_trace_id")
        return self


class ModelRequest(TimestampedModel):
    id: str
    agent_run_request_id: str
    provider_name: str
    model_id: str
    prompt_template_ref: Ref
    prompt_template_version: str
    context_bundle_id: str
    tool_schema_refs: list[Ref] = Field(default_factory=list)
    response_schema_ref: Ref
    redaction_policy_ref: Ref


class ModelResponse(TimestampedModel):
    id: str
    model_request_id: str
    response_ref: Ref
    parsed_output_ref: Ref | None = None
    tool_request_refs: list[Ref] = Field(default_factory=list)
    safety_filter_result_ref: Ref | None = None
    status: str


class AgentActionTrace(TimestampedModel):
    id: str
    run_id: str
    objective_id: str
    agent_id: str
    agent_role: AgentRole
    runtime_spec_id: str
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_id: str
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    command_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    input_refs: list[Ref] = Field(default_factory=list)
    output_refs: list[Ref] = Field(default_factory=list)
    reasoning_summary_ref: Ref
    assumptions: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    redaction_policy_ref: Ref
    retention_policy_ref: Ref
    replay_required: bool = True


class ModelCallTrace(TimestampedModel):
    id: str
    run_id: str
    agent_action_trace_id: str
    provider_name: str
    model_id: str
    model_version: str
    prompt_template_ref: Ref
    prompt_template_version: str
    context_bundle_trace_id: str
    request_ref: Ref
    response_ref: Ref
    token_usage: dict[str, int] = Field(default_factory=dict)
    latency_ms: int
    safety_filter_result_ref: Ref | None = None
    redaction_policy_ref: Ref
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    replay_mode: str = "structural"


class ToolCallTrace(TimestampedModel):
    id: str
    run_id: str
    agent_action_trace_id: str
    tool_spec_id: str
    tool_name: str
    tool_version: str
    input_schema_ref: Ref
    output_schema_ref: Ref
    input_ref: Ref
    output_ref: Ref | None = None
    command_envelope_id: str
    command_result_id: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    status: ToolCallStatus
    error: dict[str, object] = Field(default_factory=dict)


class ContextBundleTrace(TimestampedModel):
    id: str
    run_id: str
    agent_id: str
    context_ref_schema: Ref
    included_context_refs: list[Ref] = Field(default_factory=list)
    excluded_context_refs: list[Ref] = Field(default_factory=list)
    taint_labels: list[str] = Field(default_factory=list)
    sanitized_context_ref: Ref
    redaction_policy_ref: Ref
    credential_exposure_check_ref: Ref
    memory_retrieval_trace_refs: list[Ref] = Field(default_factory=list)
    graph_snapshot_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)


class AgentRecommendation(TimestampedModel):
    id: str
    run_ref: Ref
    subject_type: AgentRecommendationSubject
    subject_ref: Ref
    agent_role: AgentRole
    context_bundle_trace_ref: Ref
    agent_action_trace_ref: Ref
    recommendation_payload_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_ref: Ref | None = None
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    owner_command_ref: Ref | None = None
    rejection_reasons: list[str] = Field(default_factory=list)
    status: AgentRecommendationStatus = AgentRecommendationStatus.PROPOSED

    @model_validator(mode="after")
    def validate_recommendation(self) -> AgentRecommendation:
        if self.status == AgentRecommendationStatus.ACCEPTED and not self.owner_command_ref:
            raise ValueError("accepted recommendation requires owner_command_ref")
        if self.status == AgentRecommendationStatus.REJECTED and not self.rejection_reasons:
            raise ValueError("rejected recommendation requires rejection_reasons")
        if not self.policy_decision_refs:
            raise ValueError("agent recommendation requires policy_decision_refs")
        return self
