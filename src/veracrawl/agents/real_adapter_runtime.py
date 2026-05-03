"""Port-composed real agent/model adapter runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.agent import AgentRunRequest, ModelRequest
from veracrawl.contracts.agent_adapter import AgentAdapterExecutionRecord
from veracrawl.contracts.agent_model_runtime import AgentModelAdapterRuntimeReport
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentModelAdapterRuntimeFailureType,
    AgentRole,
    CompletenessResult,
)
from veracrawl.contracts.model_provider_adapter import ModelProviderAdapterExecutionRecord
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort


@dataclass(frozen=True)
class ModelRuntimeBinding:
    provider_name: str
    model_id: str
    model_version: str
    runtime_ref: Ref
    adapter_module_ref: Ref
    port: ModelProviderPort | None = None


@dataclass(frozen=True)
class AgentRuntimeBinding:
    framework_name: str
    runtime_spec_id: str
    runtime_ref: Ref
    adapter_module_ref: Ref
    port: AgentRuntimePort | None = None


@dataclass(frozen=True)
class AgentModelAdapterRuntimeResult:
    report: AgentModelAdapterRuntimeReport
    model_execution_records: list[ModelProviderAdapterExecutionRecord]
    framework_execution_records: list[AgentAdapterExecutionRecord]


_ROLES: tuple[AgentRole, ...] = (
    AgentRole.PLANNER,
    AgentRole.EXTRACTOR,
    AgentRole.DRIFT,
)

_FAILURES: dict[str, tuple[AgentModelAdapterRuntimeFailureType, str]] = {
    "agent-model-adapter-missing-run-control": (
        AgentModelAdapterRuntimeFailureType.MISSING_RUN_CONTROL,
        "run_control_report_ref",
    ),
    "agent-model-adapter-missing-live-normalization": (
        AgentModelAdapterRuntimeFailureType.MISSING_LIVE_NORMALIZATION,
        "live_normalization_runtime_report_ref",
    ),
    "agent-model-adapter-missing-schema-extraction": (
        AgentModelAdapterRuntimeFailureType.MISSING_SCHEMA_EXTRACTION,
        "schema_extraction_runtime_report_ref",
    ),
    "agent-model-adapter-unsupported-provider": (
        AgentModelAdapterRuntimeFailureType.UNSUPPORTED_PROVIDER,
        "unsupported_provider_refs",
    ),
    "agent-model-adapter-unsupported-framework": (
        AgentModelAdapterRuntimeFailureType.UNSUPPORTED_FRAMEWORK,
        "unsupported_framework_refs",
    ),
    "agent-model-adapter-raw-prompt-leak": (
        AgentModelAdapterRuntimeFailureType.RAW_PROMPT_LEAK,
        "raw_prompt_leak_refs",
    ),
    "agent-model-adapter-raw-response-leak": (
        AgentModelAdapterRuntimeFailureType.RAW_RESPONSE_LEAK,
        "raw_response_leak_refs",
    ),
    "agent-model-adapter-raw-credential-leak": (
        AgentModelAdapterRuntimeFailureType.RAW_CREDENTIAL_LEAK,
        "raw_credential_leak_refs",
    ),
    "agent-model-adapter-framework-state-canonical": (
        AgentModelAdapterRuntimeFailureType.FRAMEWORK_STATE_CANONICAL,
        "framework_state_canonical_refs",
    ),
    "agent-model-adapter-provider-transcript-canonical": (
        AgentModelAdapterRuntimeFailureType.PROVIDER_TRANSCRIPT_CANONICAL,
        "provider_transcript_canonical_refs",
    ),
    "agent-model-adapter-missing-model-trace": (
        AgentModelAdapterRuntimeFailureType.MISSING_MODEL_TRACE,
        "model_call_trace_refs",
    ),
    "agent-model-adapter-missing-tool-trace": (
        AgentModelAdapterRuntimeFailureType.MISSING_TOOL_TRACE,
        "tool_call_trace_refs",
    ),
    "agent-model-adapter-missing-replay": (
        AgentModelAdapterRuntimeFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "agent-model-adapter-core-import-boundary": (
        AgentModelAdapterRuntimeFailureType.CORE_IMPORT_BOUNDARY,
        "core_import_violation_refs",
    ),
}


def run_real_agent_model_adapter_runtime(
    *,
    fixture_id: str,
    scenario: str,
    run_control_report_ref: Ref | None,
    live_normalization_runtime_report_ref: Ref | None,
    schema_extraction_runtime_report_ref: Ref | None,
    model_bindings: list[ModelRuntimeBinding],
    agent_bindings: list[AgentRuntimeBinding],
    policy_decision_refs: list[Ref] | None = None,
) -> AgentModelAdapterRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:agent-model-adapter"]
    requested_providers = [binding.provider_name for binding in model_bindings]
    requested_frameworks = [binding.framework_name for binding in agent_bindings]

    if scenario == "agent-model-adapter-runtime-unavailable":
        return _needs_review_result(
            fixture_id=fixture_id,
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            policy_refs=policy_refs,
            run_control_report_ref=run_control_report_ref,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        )

    upstream_failure = _upstream_failure(
        run_control_report_ref=run_control_report_ref,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
    )
    if upstream_failure is not None:
        failure, missing_field = upstream_failure
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            policy_refs=policy_refs,
            run_control_report_ref=run_control_report_ref,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        )

    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            policy_refs=policy_refs,
            run_control_report_ref=run_control_report_ref,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        )

    available_model_bindings = [binding for binding in model_bindings if binding.port]
    available_agent_bindings = [binding for binding in agent_bindings if binding.port]
    if not available_model_bindings or not available_agent_bindings:
        return _needs_review_result(
            fixture_id=fixture_id,
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            policy_refs=policy_refs,
            run_control_report_ref=run_control_report_ref,
            live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        )

    model_records: list[ModelProviderAdapterExecutionRecord] = []
    framework_records: list[AgentAdapterExecutionRecord] = []
    agent_run_request_refs: list[Ref] = []
    agent_run_result_refs: list[Ref] = []
    agent_action_trace_refs: list[Ref] = []
    model_request_refs: list[Ref] = []
    model_response_refs: list[Ref] = []
    model_call_trace_refs: list[Ref] = []
    tool_call_trace_refs: list[Ref] = []
    context_bundle_trace_refs: list[Ref] = []

    model_binding = available_model_bindings[0]
    agent_binding = available_agent_bindings[0]
    assert model_binding.port is not None
    assert agent_binding.port is not None
    for role in _ROLES:
        request = _agent_request(fixture_id, role, agent_binding, policy_refs)
        model_request = _model_request(fixture_id, role, model_binding, request)
        model_response = model_binding.port.complete(model_request)
        agent_result = agent_binding.port.run(request)
        role_slug = role.value
        provider_slug = _slug(model_binding.provider_name)
        model_trace_ref = f"model-call-trace:{fixture_id}:{role_slug}:{provider_slug}"
        tool_trace_ref = f"tool-call-trace:{fixture_id}:{role_slug}:controlled-tool"
        context_trace_ref = f"context-bundle-trace:{fixture_id}:{role_slug}"
        model_record = ModelProviderAdapterExecutionRecord(
            id=f"model-provider-execution:{fixture_id}:{role_slug}:{provider_slug}",
            provider_name=model_binding.provider_name,
            runtime_spec_ref=f"agent-runtime-spec:{fixture_id}:{role_slug}:model-provider",
            model_request_ref=model_request.id,
            model_response_ref=model_response.id,
            model_call_trace_ref=model_trace_ref,
            context_bundle_trace_ref=context_trace_ref,
            agent_run_request_ref=request.id,
            agent_run_result_ref=agent_result.id,
            agent_action_trace_ref=agent_result.agent_action_trace_id,
            command_result_refs=[f"command-result:{fixture_id}:{role_slug}:model"],
            policy_decision_refs=policy_refs,
            observability_report_refs=[f"observability-report:{fixture_id}:agent-model"],
            security_privacy_report_refs=[
                f"security-privacy-report:{fixture_id}:agent-model"
            ],
            replay_bundle_ref=f"replay-bundle:{fixture_id}:agent-model",
            live_runtime_refs=[model_binding.runtime_ref],
            diagnostic_provider_state_refs=[
                f"diagnostic-provider-state:{fixture_id}:{role_slug}"
            ],
            result=CompletenessResult.PASS,
        )
        framework_record = AgentAdapterExecutionRecord(
            id=f"agent-adapter-execution:{fixture_id}:{role_slug}:{_slug(agent_binding.framework_name)}",
            framework_name=agent_binding.framework_name,
            runtime_spec_ref=agent_binding.runtime_spec_id,
            agent_run_request_ref=request.id,
            agent_run_result_ref=agent_result.id,
            agent_action_trace_ref=agent_result.agent_action_trace_id,
            model_call_trace_refs=[model_trace_ref],
            tool_call_trace_refs=[tool_trace_ref],
            context_bundle_trace_ref=context_trace_ref,
            command_result_refs=[f"command-result:{fixture_id}:{role_slug}:agent"],
            policy_decision_refs=policy_refs,
            observability_report_refs=[f"observability-report:{fixture_id}:agent-model"],
            security_privacy_report_refs=[
                f"security-privacy-report:{fixture_id}:agent-model"
            ],
            replay_bundle_ref=f"replay-bundle:{fixture_id}:agent-model",
            live_runtime_refs=[agent_binding.runtime_ref],
            diagnostic_framework_state_refs=[
                f"diagnostic-framework-state:{fixture_id}:{role_slug}"
            ],
            result=CompletenessResult.PASS,
        )
        model_records.append(model_record)
        framework_records.append(framework_record)
        agent_run_request_refs.append(request.id)
        agent_run_result_refs.append(agent_result.id)
        agent_action_trace_refs.append(agent_result.agent_action_trace_id)
        model_request_refs.append(model_request.id)
        model_response_refs.append(model_response.id)
        model_call_trace_refs.append(model_trace_ref)
        tool_call_trace_refs.append(tool_trace_ref)
        context_bundle_trace_refs.append(context_trace_ref)

    report = AgentModelAdapterRuntimeReport(
        id=f"agent-model-adapter-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        run_control_report_ref=run_control_report_ref,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        planning_agent_run_refs=_role_result_refs(agent_run_result_refs, AgentRole.PLANNER),
        extraction_agent_run_refs=_role_result_refs(agent_run_result_refs, AgentRole.EXTRACTOR),
        repair_agent_run_refs=_role_result_refs(agent_run_result_refs, AgentRole.DRIFT),
        provider_execution_refs=[record.id for record in model_records],
        framework_execution_refs=[record.id for record in framework_records],
        requested_provider_names=requested_providers,
        verified_provider_names=[model_binding.provider_name],
        requested_framework_names=requested_frameworks,
        verified_framework_names=[agent_binding.framework_name],
        model_request_refs=model_request_refs,
        model_response_refs=model_response_refs,
        model_call_trace_refs=model_call_trace_refs,
        agent_run_request_refs=agent_run_request_refs,
        agent_run_result_refs=agent_run_result_refs,
        agent_action_trace_refs=agent_action_trace_refs,
        tool_call_trace_refs=tool_call_trace_refs,
        context_bundle_trace_refs=context_bundle_trace_refs,
        adapter_runtime_refs=[model_binding.runtime_ref, agent_binding.runtime_ref],
        adapter_availability_refs=[
            f"adapter-availability:{fixture_id}:{_slug(model_binding.provider_name)}",
            f"adapter-availability:{fixture_id}:{_slug(agent_binding.framework_name)}",
        ],
        policy_decision_refs=policy_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:agent-model"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:agent-model"
        ],
        command_record_refs=[f"command:{fixture_id}:agent-model-adapter"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:agent-model-adapter"],
        outbox_refs=[f"outbox:{fixture_id}:agent-model-adapter"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:agent-model",
        operator_status="agent_model_adapter_runtime_completed",
        completion_result=CompletenessResult.PASS,
    )
    return AgentModelAdapterRuntimeResult(report, model_records, framework_records)


def _upstream_failure(
    *,
    run_control_report_ref: Ref | None,
    live_normalization_runtime_report_ref: Ref | None,
    schema_extraction_runtime_report_ref: Ref | None,
) -> tuple[AgentModelAdapterRuntimeFailureType, str] | None:
    if run_control_report_ref is None:
        return (
            AgentModelAdapterRuntimeFailureType.MISSING_RUN_CONTROL,
            "run_control_report_ref",
        )
    if live_normalization_runtime_report_ref is None:
        return (
            AgentModelAdapterRuntimeFailureType.MISSING_LIVE_NORMALIZATION,
            "live_normalization_runtime_report_ref",
        )
    if schema_extraction_runtime_report_ref is None:
        return (
            AgentModelAdapterRuntimeFailureType.MISSING_SCHEMA_EXTRACTION,
            "schema_extraction_runtime_report_ref",
        )
    return None


def _needs_review_result(
    *,
    fixture_id: str,
    requested_providers: list[str],
    requested_frameworks: list[str],
    policy_refs: list[Ref],
    run_control_report_ref: Ref | None,
    live_normalization_runtime_report_ref: Ref | None,
    schema_extraction_runtime_report_ref: Ref | None,
) -> AgentModelAdapterRuntimeResult:
    unavailable_refs = [
        f"missing-runtime:{fixture_id}:{_slug(name)}"
        for name in requested_providers + requested_frameworks
    ] or [f"missing-runtime:{fixture_id}:adapter"]
    report = AgentModelAdapterRuntimeReport(
        id=f"agent-model-adapter-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        run_control_report_ref=run_control_report_ref,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        requested_provider_names=requested_providers,
        requested_framework_names=requested_frameworks,
        adapter_availability_refs=[
            f"adapter-availability:{fixture_id}:unavailable"
        ],
        policy_decision_refs=policy_refs,
        unavailable_runtime_refs=unavailable_refs,
        failure_type=AgentModelAdapterRuntimeFailureType.ADAPTER_RUNTIME_UNAVAILABLE,
        operator_status=AgentModelAdapterRuntimeFailureType.ADAPTER_RUNTIME_UNAVAILABLE.value,
        completion_result=CompletenessResult.NEEDS_REVIEW,
        diagnostics=["adapter SDK, credentials, or wrapper callable unavailable"],
    )
    return AgentModelAdapterRuntimeResult(report, [], [])


def _failure_result(
    *,
    fixture_id: str,
    failure: AgentModelAdapterRuntimeFailureType,
    missing_field: str,
    requested_providers: list[str],
    requested_frameworks: list[str],
    policy_refs: list[Ref],
    run_control_report_ref: Ref | None,
    live_normalization_runtime_report_ref: Ref | None,
    schema_extraction_runtime_report_ref: Ref | None,
) -> AgentModelAdapterRuntimeResult:
    report = AgentModelAdapterRuntimeReport(
        id=f"agent-model-adapter-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        run_control_report_ref=run_control_report_ref,
        live_normalization_runtime_report_ref=live_normalization_runtime_report_ref,
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        requested_provider_names=requested_providers,
        requested_framework_names=requested_frameworks,
        policy_decision_refs=policy_refs,
        unsupported_provider_refs=(
            [f"unsupported-provider:{fixture_id}:unknown"]
            if failure == AgentModelAdapterRuntimeFailureType.UNSUPPORTED_PROVIDER
            else []
        ),
        unsupported_framework_refs=(
            [f"unsupported-framework:{fixture_id}:unknown"]
            if failure == AgentModelAdapterRuntimeFailureType.UNSUPPORTED_FRAMEWORK
            else []
        ),
        raw_prompt_leak_refs=(
            [f"raw-prompt-leak:{fixture_id}:agent-model"]
            if failure == AgentModelAdapterRuntimeFailureType.RAW_PROMPT_LEAK
            else []
        ),
        raw_response_leak_refs=(
            [f"raw-response-leak:{fixture_id}:agent-model"]
            if failure == AgentModelAdapterRuntimeFailureType.RAW_RESPONSE_LEAK
            else []
        ),
        raw_credential_leak_refs=(
            [f"raw-credential-leak:{fixture_id}:agent-model"]
            if failure == AgentModelAdapterRuntimeFailureType.RAW_CREDENTIAL_LEAK
            else []
        ),
        framework_state_canonical_refs=(
            [f"framework-state:{fixture_id}:canonical"]
            if failure == AgentModelAdapterRuntimeFailureType.FRAMEWORK_STATE_CANONICAL
            else []
        ),
        provider_transcript_canonical_refs=(
            [f"provider-transcript:{fixture_id}:canonical"]
            if failure == AgentModelAdapterRuntimeFailureType.PROVIDER_TRANSCRIPT_CANONICAL
            else []
        ),
        core_import_violation_refs=(
            [f"core-import-violation:{fixture_id}:adapter-import"]
            if failure == AgentModelAdapterRuntimeFailureType.CORE_IMPORT_BOUNDARY
            else []
        ),
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=[f"agent/model adapter runtime failed: {failure.value}"],
    )
    return AgentModelAdapterRuntimeResult(report, [], [])


def _agent_request(
    fixture_id: str,
    role: AgentRole,
    binding: AgentRuntimeBinding,
    policy_refs: list[Ref],
) -> AgentRunRequest:
    role_slug = role.value
    return AgentRunRequest(
        id=f"agent-run-request:{fixture_id}:{role_slug}",
        run_id=f"run:{fixture_id}",
        agent_role=role,
        runtime_spec_id=binding.runtime_spec_id,
        objective_ref=f"objective:{fixture_id}",
        context_bundle_id=f"context-bundle:{fixture_id}:{role_slug}",
        allowed_tool_spec_refs=[f"tool-spec:{fixture_id}:{role_slug}:read"],
        required_output_schema_ref=f"schema:{fixture_id}:{role_slug}:output",
        loop_budget_ref=f"loop-budget:{fixture_id}:{role_slug}",
        policy_decision_refs=policy_refs,
    )


def _model_request(
    fixture_id: str,
    role: AgentRole,
    binding: ModelRuntimeBinding,
    agent_request: AgentRunRequest,
) -> ModelRequest:
    role_slug = role.value
    return ModelRequest(
        id=f"model-request:{fixture_id}:{role_slug}:{_slug(binding.provider_name)}",
        agent_run_request_id=agent_request.id,
        provider_name=binding.provider_name,
        model_id=binding.model_id,
        prompt_template_ref=f"prompt-template:{fixture_id}:{role_slug}",
        prompt_template_version="1",
        context_bundle_id=agent_request.context_bundle_id,
        tool_schema_refs=agent_request.allowed_tool_spec_refs,
        response_schema_ref=agent_request.required_output_schema_ref,
        redaction_policy_ref=f"redaction-policy:{fixture_id}:agent-model",
    )


def _role_result_refs(result_refs: list[Ref], role: AgentRole) -> list[Ref]:
    marker = f":{role.value}"
    return [ref for ref in result_refs if marker in ref]


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")
