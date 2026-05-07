"""Framework-neutral agent runtime contracts."""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, VeraModel
from veracrawl.contracts.enums import (
    AgentHandoffStatus,
    AgentRecommendationStatus,
    AgentRecommendationSubject,
    AgentRole,
    AgentRunStatus,
    CalibrationMethod,
    CompletenessResult,
    CoordinationDecisionStatus,
    CoordinationDecisionType,
    FrameworkStatePersistence,
    MessageRole,
    MultiAgentFailureType,
    MultiAgentWorkflowStatus,
    RecoveryDecisionKind,
    RecoveryDecisionSource,
    RecoveryTerminationReason,
    RepairSignalStatus,
    ResponseFormatKind,
    RuntimeType,
    ToolCallStatus,
    ToolType,
)

_FLOAT_TOL = 1e-9
_TERMINATION_REASONS_REQUIRING_DECISIONS = frozenset(
    {
        RecoveryTerminationReason.REPEATED_SIGNATURE_HARD_STOP,
        RecoveryTerminationReason.MAX_ITERATIONS_EXCEEDED,
    }
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


class MultiAgentWorkflow(TimestampedModel):
    id: str
    run_ref: Ref
    workflow_type: str
    coordinator_service_ref: Ref
    agent_role_sequence: list[AgentRole] = Field(default_factory=list)
    loop_budget_ref: Ref
    termination_rule_ref: Ref
    escalation_rule_ref: Ref
    arbitration_policy_ref: Ref
    context_bundle_ref: Ref
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    memory_retrieval_trace_refs: list[Ref] = Field(default_factory=list)
    evidence_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: MultiAgentWorkflowStatus

    @model_validator(mode="after")
    def validate_workflow(self) -> MultiAgentWorkflow:
        if not self.agent_role_sequence:
            raise ValueError("multi-agent workflow requires agent role sequence")
        required = [
            self.coordinator_service_ref,
            self.loop_budget_ref,
            self.termination_rule_ref,
            self.escalation_rule_ref,
            self.arbitration_policy_ref,
            self.context_bundle_ref,
        ]
        if not all(required):
            raise ValueError("multi-agent workflow requires coordination refs")
        if not self.policy_decision_refs:
            raise ValueError("multi-agent workflow requires policy refs")
        return self


class AgentHandoff(TimestampedModel):
    id: str
    run_ref: Ref
    workflow_ref: Ref
    from_agent_action_trace_ref: Ref
    to_agent_role: AgentRole
    context_bundle_trace_ref: Ref
    required_output_schema_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: AgentHandoffStatus
    output_ref: Ref | None = None
    rejection_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_handoff(self) -> AgentHandoff:
        if not self.workflow_ref or not self.from_agent_action_trace_ref:
            raise ValueError("agent handoff requires workflow and source trace refs")
        if not self.context_bundle_trace_ref or not self.required_output_schema_ref:
            raise ValueError("agent handoff requires context and output schema refs")
        if not self.policy_decision_refs:
            raise ValueError("agent handoff requires policy refs")
        if self.status == AgentHandoffStatus.COMPLETED and not self.output_ref:
            raise ValueError("completed agent handoff requires output ref")
        if self.status == AgentHandoffStatus.REJECTED and not self.rejection_reasons:
            raise ValueError("rejected agent handoff requires reasons")
        return self


class CoordinationDecision(TimestampedModel):
    id: str
    run_ref: Ref
    workflow_ref: Ref
    decision_type: CoordinationDecisionType
    candidate_refs: list[Ref] = Field(default_factory=list)
    selected_ref: Ref | None = None
    rationale_ref: Ref
    arbitration_policy_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    owner_command_ref: Ref | None = None
    status: CoordinationDecisionStatus

    @model_validator(mode="after")
    def validate_decision(self) -> CoordinationDecision:
        if not self.workflow_ref or not self.candidate_refs:
            raise ValueError("coordination decision requires workflow and candidates")
        if self.status == CoordinationDecisionStatus.APPLIED and not self.owner_command_ref:
            raise ValueError("applied coordination decision requires owner command ref")
        if self.status != CoordinationDecisionStatus.REJECTED and not self.selected_ref:
            raise ValueError("coordination decision requires selected ref")
        if not self.policy_decision_refs:
            raise ValueError("coordination decision requires policy refs")
        return self


class DriftRepairSignal(TimestampedModel):
    id: str
    run_ref: Ref
    workflow_ref: Ref
    affected_refs: list[Ref] = Field(default_factory=list)
    before_evidence_refs: list[Ref] = Field(default_factory=list)
    after_evidence_refs: list[Ref] = Field(default_factory=list)
    repair_proposal_refs: list[Ref] = Field(default_factory=list)
    rollback_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: RepairSignalStatus

    @model_validator(mode="after")
    def validate_repair_signal(self) -> DriftRepairSignal:
        if not self.affected_refs or not self.repair_proposal_refs:
            raise ValueError("repair signal requires affected and repair refs")
        if not self.before_evidence_refs or not self.after_evidence_refs:
            raise ValueError("repair signal requires before and after evidence")
        if not self.rollback_ref or not self.policy_decision_refs:
            raise ValueError("repair signal requires rollback and policy refs")
        return self


class MultiAgentRepairReport(TimestampedModel):
    id: str
    run_ref: Ref
    workflow_ref: Ref | None = None
    agent_model_adapter_runtime_report_ref: Ref | None = None
    live_evidence_verification_runtime_report_ref: Ref | None = None
    handoff_refs: list[Ref] = Field(default_factory=list)
    coordination_decision_refs: list[Ref] = Field(default_factory=list)
    repair_signal_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    controlled_tool_call_refs: list[Ref] = Field(default_factory=list)
    owner_command_refs: list[Ref] = Field(default_factory=list)
    review_escalation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: MultiAgentFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_repair_report(self) -> MultiAgentRepairReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "workflow_ref": self.workflow_ref,
                "agent_model_adapter_runtime_report_ref": (
                    self.agent_model_adapter_runtime_report_ref
                ),
                "live_evidence_verification_runtime_report_ref": (
                    self.live_evidence_verification_runtime_report_ref
                ),
                "handoff_refs": self.handoff_refs,
                "coordination_decision_refs": self.coordination_decision_refs,
                "repair_signal_refs": self.repair_signal_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "controlled_tool_call_refs": self.controlled_tool_call_refs,
                "owner_command_refs": self.owner_command_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields or self.failure_type:
                raise ValueError(f"passing multi-agent repair report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS:
            if self.failure_type is None:
                raise ValueError("non-pass multi-agent repair report requires failure_type")
            if not (self.failure_report_refs or self.missing_ref_fields):
                raise ValueError("non-pass multi-agent repair report requires failures")
        return self


class MultiAgentFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_failure_type: MultiAgentFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> MultiAgentFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("multi-agent fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative multi-agent fixture must not expect pass")
        return self


# ---------------------------------------------------------------------------
# v2 contracts (production-authorized-source-crawler design §3.5)
#
# Added in Phase 0 step 0.2. Behavior-free in this phase: only the type
# surface and pydantic validators land here. Phase 4 / Phase 5 wire these
# into the v2 ``ModelProviderPort``, the LLM-driven extraction rewrite,
# and the ``RecoveryPort``.
#
# ``LLMExtractionCandidate`` / ``LLMFieldCitation`` / ``LLMFieldConfidence``
# carry an ``LLM`` prefix to avoid colliding with the existing heuristic
# ``processing.ExtractionCandidate`` contract, which the foundation
# registry and many runtime modules already pin by name. The ``LLM``
# prefix signals "produced by the LLM-driven extraction path"; the
# semantic intent matches design.md §3.5. STATUS.md records this as a
# rename divergence so Phase 4 can decide whether to migrate the
# heuristic path off ``ExtractionCandidate`` and reclaim the bare name.
# ---------------------------------------------------------------------------


class ToolCall(VeraModel):
    """A model-emitted tool invocation request.

    Mirrors the OpenAI Responses ``tool_calls`` and Anthropic
    Messages ``tool_use`` shapes without leaking either provider's
    types. ``id`` is the provider-assigned correlation id used to
    pair the call with its tool result message.
    """

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tool_call(self) -> ToolCall:
        if not self.id.strip():
            raise ValueError("tool call id must be non-blank")
        if not self.name.strip():
            raise ValueError("tool call name must be non-blank")
        return self


class Message(VeraModel):
    """A single chat message in an LLM conversation.

    Provider-neutral: the role / content / tool-call shape is the
    intersection of OpenAI Responses and Anthropic Messages. The
    structured-tool dance — assistant emits tool_calls, environment
    replies with role=tool messages keyed by tool_call_id — works on
    both providers.
    """

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_message(self) -> Message:
        if self.role is MessageRole.TOOL:
            if not self.tool_call_id:
                raise ValueError("tool-role message requires tool_call_id")
            if not self.name:
                raise ValueError("tool-role message requires name")
            if self.tool_calls:
                raise ValueError("tool-role message must not carry tool_calls")
        elif self.role is MessageRole.ASSISTANT:
            if self.tool_call_id is not None:
                raise ValueError("assistant message must not set tool_call_id")
            if not self.tool_calls and not self.content:
                raise ValueError(
                    "assistant message requires content unless tool_calls is non-empty"
                )
        else:  # USER, SYSTEM
            if self.tool_call_id is not None:
                raise ValueError(f"{self.role.value} message must not set tool_call_id")
            if self.tool_calls:
                raise ValueError(f"{self.role.value} message must not carry tool_calls")
        return self


class ToolSpec(VeraModel):
    """A tool definition exposed to the model.

    ``parameters_schema`` is a JSON Schema dict; ``strict=True``
    requests provider-side strict-mode validation (OpenAI structured
    tools, Anthropic ``input_schema``). The schema must declare a
    top-level ``type`` so providers can reject obviously malformed
    specs before round-tripping the full payload.
    """

    name: str
    description: str
    parameters_schema: dict[str, Any]
    strict: bool = False

    @model_validator(mode="after")
    def validate_tool_spec(self) -> ToolSpec:
        if not self.name.strip():
            raise ValueError("tool spec name must be non-blank")
        if not self.description.strip():
            raise ValueError("tool spec description must be non-blank")
        if "type" not in self.parameters_schema:
            raise ValueError("tool spec parameters_schema must declare a JSON Schema 'type'")
        return self


class ResponseFormat(VeraModel):
    """Structured-output spec for a model response.

    ``kind=TEXT`` (default) leaves the response as free-form text.
    ``kind=JSON_OBJECT`` asks for any JSON object (no schema enforcement).
    ``kind=JSON_SCHEMA`` requires both a ``schema_name`` and a JSON
    Schema dict; ``strict=True`` opts into provider-side strict
    validation (OpenAI ``response_format.strict``, Anthropic
    ``response_format`` JSON-mode plus client-side validation).
    """

    kind: ResponseFormatKind
    schema_name: str | None = None
    json_schema: dict[str, Any] | None = None
    strict: bool = False

    @model_validator(mode="after")
    def validate_response_format(self) -> ResponseFormat:
        if self.kind is ResponseFormatKind.JSON_SCHEMA:
            if not self.schema_name:
                raise ValueError("json_schema response format requires schema_name")
            if self.json_schema is None:
                raise ValueError("json_schema response format requires json_schema")
        else:
            if self.json_schema is not None:
                raise ValueError(f"{self.kind.value} response format must not carry json_schema")
            if self.kind is ResponseFormatKind.TEXT and self.schema_name is not None:
                raise ValueError("text response format must not carry schema_name")
        return self


class TokenUsage(VeraModel):
    """Per-call token accounting reported by a model provider.

    Counts are non-negative; ``total = prompt + completion`` is
    enforced because both providers report consistent totals.
    ``cached_input_tokens`` is a subset of ``prompt_tokens`` (OpenAI
    prompt-cache hits, Anthropic prompt caching read tokens) and
    ``reasoning_tokens`` is a subset of ``completion_tokens`` (OpenAI
    reasoning-model output, Anthropic extended-thinking output).
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0

    @model_validator(mode="after")
    def validate_token_usage(self) -> TokenUsage:
        for name, value in (
            ("prompt_tokens", self.prompt_tokens),
            ("completion_tokens", self.completion_tokens),
            ("total_tokens", self.total_tokens),
            ("cached_input_tokens", self.cached_input_tokens),
            ("reasoning_tokens", self.reasoning_tokens),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("total_tokens must equal prompt_tokens + completion_tokens")
        if self.cached_input_tokens > self.prompt_tokens:
            raise ValueError("cached_input_tokens cannot exceed prompt_tokens")
        if self.reasoning_tokens > self.completion_tokens:
            raise ValueError("reasoning_tokens cannot exceed completion_tokens")
        return self


class TokenBudget(TimestampedModel):
    """Per-run cap that ``OutboxBackedBudget`` (Phase 4) decrements.

    At least one of ``max_input_tokens`` / ``max_output_tokens`` /
    ``max_total_tokens`` / ``max_cost_usd`` must be set; an empty
    budget is meaningless and almost always indicates a wiring bug
    upstream.
    """

    id: str
    run_ref: Ref
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_total_tokens: int | None = None
    max_cost_usd: float | None = None

    @model_validator(mode="after")
    def validate_budget(self) -> TokenBudget:
        caps: tuple[tuple[str, int | float | None], ...] = (
            ("max_input_tokens", self.max_input_tokens),
            ("max_output_tokens", self.max_output_tokens),
            ("max_total_tokens", self.max_total_tokens),
            ("max_cost_usd", self.max_cost_usd),
        )
        if all(value is None for _, value in caps):
            raise ValueError(
                "token budget requires at least one cap (input / output / total / cost)"
            )
        for name, value in caps:
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when set")
        return self


class LLMExtractionCandidate(TimestampedModel):
    """LLM-driven extraction output (Phase 4 ``schema_runtime`` rewrite).

    Each entry in ``field_values`` must have a matching entry in both
    ``field_citation_refs`` (where the LLM grounded the value) and
    ``field_confidence_refs`` (the per-field calibrated score).
    Fields the model declined to extract appear in ``abstentions`` —
    not in ``field_values`` — with a non-blank reason.
    """

    id: str
    run_ref: Ref
    source_url: str
    schema_ref: Ref
    model_call_trace_ref: Ref
    field_values: dict[str, Any] = Field(default_factory=dict)
    field_citation_refs: dict[str, Ref] = Field(default_factory=dict)
    field_confidence_refs: dict[str, Ref] = Field(default_factory=dict)
    abstentions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_candidate(self) -> LLMExtractionCandidate:
        value_keys = set(self.field_values)
        missing_citations = sorted(value_keys - set(self.field_citation_refs))
        if missing_citations:
            raise ValueError(f"LLM extraction fields missing citation refs: {missing_citations}")
        missing_confidences = sorted(value_keys - set(self.field_confidence_refs))
        if missing_confidences:
            raise ValueError(
                f"LLM extraction fields missing confidence refs: {missing_confidences}"
            )
        overlap = sorted(set(self.abstentions) & value_keys)
        if overlap:
            raise ValueError(f"abstentions cannot also appear in field_values: {overlap}")
        for field_name, reason in self.abstentions.items():
            if not reason.strip():
                raise ValueError(f"abstention reason for '{field_name}' must be non-blank")
        return self


class LLMFieldCitation(TimestampedModel):
    """Anchor refs proving where an extracted field came from.

    ``anchor_refs`` point into the per-attempt evidence anchors that
    Phase 1 populates; ``excerpt`` is the snippet the LLM grounded on;
    ``selector`` is an optional CSS / XPath; ``screenshot_region_ref``
    points to a bounding box on the page screenshot when available.
    """

    id: str
    candidate_ref: Ref
    field_name: str
    anchor_refs: list[Ref] = Field(default_factory=list)
    excerpt: str
    selector: str | None = None
    screenshot_region_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_citation(self) -> LLMFieldCitation:
        if not self.field_name.strip():
            raise ValueError("citation field_name must be non-blank")
        if not self.anchor_refs:
            raise ValueError("citation requires at least one anchor ref")
        if not self.excerpt.strip():
            raise ValueError("citation excerpt must be non-blank")
        return self


class LLMFieldConfidence(TimestampedModel):
    """Per-field confidence with explicit calibration provenance.

    ``raw_score`` is what the LLM self-reported; ``calibrated_score``
    is the post-calibration value. When ``calibration_method`` is
    ``NONE`` the calibrated score must equal the raw score and no
    ``calibration_version`` may be set; any other method requires a
    pinned ``calibration_version`` so the calibrator is reproducible
    in replay.
    """

    id: str
    candidate_ref: Ref
    field_name: str
    raw_score: float
    calibrated_score: float
    calibration_method: CalibrationMethod
    calibration_version: Ref | None = None

    @model_validator(mode="after")
    def validate_confidence(self) -> LLMFieldConfidence:
        if not self.field_name.strip():
            raise ValueError("confidence field_name must be non-blank")
        for name, value in (
            ("raw_score", self.raw_score),
            ("calibrated_score", self.calibrated_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0]")
        if self.calibration_method is CalibrationMethod.NONE:
            if self.calibration_version is not None:
                raise ValueError(
                    "calibration_version must be unset when calibration_method is NONE"
                )
            if not math.isclose(self.raw_score, self.calibrated_score, abs_tol=_FLOAT_TOL):
                raise ValueError("calibration_method=NONE requires calibrated_score == raw_score")
        else:
            if not self.calibration_version:
                raise ValueError(
                    f"calibration_method={self.calibration_method.value} "
                    "requires calibration_version"
                )
        return self


class RecoveryDecision(TimestampedModel):
    """Outcome of one recovery iteration (Phase 5 ``RecoveryPort``).

    ``failure_signature`` is the deterministic hash the cost-gate uses
    to detect repeated-same-failure loops. ``source`` records which
    subsystem produced the decision so cost can be attributed
    correctly: ``CHEAP_CLASSIFIER`` decisions cost zero, while
    ``LLM_RECOVERY`` decisions accumulate against the per-objective
    and per-host caps.
    """

    id: str
    kind: RecoveryDecisionKind
    reason: str
    failure_signature: str
    source: RecoveryDecisionSource
    alternative_url: str | None = None
    escalation_target: str | None = None
    cost_usd: float = 0.0

    @model_validator(mode="after")
    def validate_decision(self) -> RecoveryDecision:
        if not self.reason.strip():
            raise ValueError("recovery decision reason must be non-blank")
        if not self.failure_signature.strip():
            raise ValueError("recovery decision failure_signature must be non-blank")
        if self.cost_usd < 0:
            raise ValueError("recovery decision cost_usd must be non-negative")
        if self.kind is RecoveryDecisionKind.DIFFERENT_URL:
            if not self.alternative_url:
                raise ValueError("different_url recovery decision requires alternative_url")
            if self.escalation_target is not None:
                raise ValueError("different_url recovery decision must not set escalation_target")
        elif self.kind is RecoveryDecisionKind.ESCALATE_ADAPTER:
            if not self.escalation_target:
                raise ValueError("escalate_adapter recovery decision requires escalation_target")
            if self.alternative_url is not None:
                raise ValueError("escalate_adapter recovery decision must not set alternative_url")
        else:  # ABANDON, REQUEST_REVIEW
            if self.alternative_url is not None:
                raise ValueError(
                    f"{self.kind.value} recovery decision must not set alternative_url"
                )
            if self.escalation_target is not None:
                raise ValueError(
                    f"{self.kind.value} recovery decision must not set escalation_target"
                )
        return self


class RecoveryTrace(TimestampedModel):
    """Per-run recovery audit trail.

    Carries the ordered list of ``RecoveryDecision`` refs produced
    during a single ``AgentRunRequest``, plus the final termination
    reason and accumulated cost. Termination reasons that imply the
    recovery loop ran (``REPEATED_SIGNATURE_HARD_STOP``,
    ``MAX_ITERATIONS_EXCEEDED``) require at least one decision ref —
    otherwise the trace would describe an outcome that no work
    produced.
    """

    id: str
    agent_run_request_ref: Ref
    decision_refs: list[Ref] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    terminated_by: RecoveryTerminationReason

    @model_validator(mode="after")
    def validate_trace(self) -> RecoveryTrace:
        if self.total_cost_usd < 0:
            raise ValueError("recovery trace total_cost_usd must be non-negative")
        if (
            self.terminated_by in _TERMINATION_REASONS_REQUIRING_DECISIONS
            and not self.decision_refs
        ):
            raise ValueError(
                f"recovery trace terminated by {self.terminated_by.value} "
                "requires at least one decision ref"
            )
        return self
