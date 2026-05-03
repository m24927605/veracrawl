from __future__ import annotations

import pytest

from veracrawl.agents.real_adapter_runtime import (
    AgentModelAdapterRuntimeResult,
    AgentRuntimeBinding,
    ModelRuntimeBinding,
    run_real_agent_model_adapter_runtime,
)
from veracrawl.contracts.agent import AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse
from veracrawl.contracts.enums import (
    AgentModelAdapterRuntimeFailureType,
    AgentRunStatus,
    CompletenessResult,
)


class _ModelPort:
    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            id=f"model-response:{request.id}",
            model_request_id=request.id,
            response_ref=f"model-response-payload:{request.id}",
            parsed_output_ref=f"model-parsed-output:{request.id}",
            status="completed",
        )


class _AgentPort:
    def run(self, request: AgentRunRequest) -> AgentRunResult:
        return AgentRunResult(
            id=f"agent-run-result:{request.run_id}:{request.agent_role.value}",
            agent_run_request_id=request.id,
            agent_action_trace_id=(
                f"agent-action-trace:{request.run_id}:{request.agent_role.value}"
            ),
            output_ref=f"agent-output:{request.run_id}:{request.agent_role.value}",
            status=AgentRunStatus.COMPLETED,
        )


def _model_binding() -> ModelRuntimeBinding:
    return ModelRuntimeBinding(
        provider_name="Local model runtime",
        model_id="local",
        model_version="1",
        runtime_ref="model-runtime:fixture:local",
        adapter_module_ref="module:local",
        port=_ModelPort(),
    )


def _agent_binding() -> AgentRuntimeBinding:
    return AgentRuntimeBinding(
        framework_name="VeraCrawl Native Runtime",
        runtime_spec_id="agent-runtime-spec:fixture:native",
        runtime_ref="agent-runtime:fixture:native",
        adapter_module_ref="module:native",
        port=_AgentPort(),
    )


def _run(
    scenario: str = "agent-model-adapter-local-runtime-success",
) -> AgentModelAdapterRuntimeResult:
    return run_real_agent_model_adapter_runtime(
        fixture_id="fixture",
        scenario=scenario,
        run_control_report_ref="production-run-control-report:fixture",
        live_normalization_runtime_report_ref="live-normalization-runtime-report:fixture",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:fixture",
        model_bindings=[_model_binding()],
        agent_bindings=[_agent_binding()],
        policy_decision_refs=["policy:fixture:agent-model-adapter"],
    )


def test_real_agent_model_adapter_runtime_executes_required_agent_turns() -> None:
    result = _run()
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert len(report.planning_agent_run_refs) == 1
    assert len(report.extraction_agent_run_refs) == 1
    assert len(report.repair_agent_run_refs) == 1
    assert len(result.model_execution_records) == 3
    assert len(result.framework_execution_records) == 3
    assert set(report.verified_provider_names) == {"Local model runtime"}
    assert set(report.verified_framework_names) == {"VeraCrawl Native Runtime"}


def test_real_agent_model_adapter_runtime_unavailable_is_needs_review() -> None:
    result = run_real_agent_model_adapter_runtime(
        fixture_id="fixture",
        scenario="agent-model-adapter-runtime-unavailable",
        run_control_report_ref="production-run-control-report:fixture",
        live_normalization_runtime_report_ref="live-normalization-runtime-report:fixture",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:fixture",
        model_bindings=[
            _model_binding().__class__(
                provider_name="OpenAI",
                model_id="gpt",
                model_version="unavailable",
                runtime_ref="model-runtime:fixture:openai:unavailable",
                adapter_module_ref="module:openai",
                port=None,
            )
        ],
        agent_bindings=[
            _agent_binding().__class__(
                framework_name="OpenAI Agent SDK",
                runtime_spec_id="agent-runtime-spec:fixture:openai",
                runtime_ref="agent-runtime:fixture:openai:unavailable",
                adapter_module_ref="module:openai-agents",
                port=None,
            )
        ],
        policy_decision_refs=["policy:fixture:agent-model-adapter"],
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.unavailable_runtime_refs


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "agent-model-adapter-unsupported-provider",
            AgentModelAdapterRuntimeFailureType.UNSUPPORTED_PROVIDER,
        ),
        (
            "agent-model-adapter-unsupported-framework",
            AgentModelAdapterRuntimeFailureType.UNSUPPORTED_FRAMEWORK,
        ),
        (
            "agent-model-adapter-raw-prompt-leak",
            AgentModelAdapterRuntimeFailureType.RAW_PROMPT_LEAK,
        ),
        (
            "agent-model-adapter-raw-response-leak",
            AgentModelAdapterRuntimeFailureType.RAW_RESPONSE_LEAK,
        ),
        (
            "agent-model-adapter-raw-credential-leak",
            AgentModelAdapterRuntimeFailureType.RAW_CREDENTIAL_LEAK,
        ),
        (
            "agent-model-adapter-framework-state-canonical",
            AgentModelAdapterRuntimeFailureType.FRAMEWORK_STATE_CANONICAL,
        ),
        (
            "agent-model-adapter-provider-transcript-canonical",
            AgentModelAdapterRuntimeFailureType.PROVIDER_TRANSCRIPT_CANONICAL,
        ),
        (
            "agent-model-adapter-missing-model-trace",
            AgentModelAdapterRuntimeFailureType.MISSING_MODEL_TRACE,
        ),
        (
            "agent-model-adapter-missing-tool-trace",
            AgentModelAdapterRuntimeFailureType.MISSING_TOOL_TRACE,
        ),
        (
            "agent-model-adapter-missing-replay",
            AgentModelAdapterRuntimeFailureType.MISSING_REPLAY_REFS,
        ),
        (
            "agent-model-adapter-core-import-boundary",
            AgentModelAdapterRuntimeFailureType.CORE_IMPORT_BOUNDARY,
        ),
    ],
)
def test_real_agent_model_adapter_runtime_typed_failures(
    scenario: str,
    failure: AgentModelAdapterRuntimeFailureType,
) -> None:
    result = _run(scenario)
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure


def test_real_agent_model_adapter_runtime_missing_upstream_fails() -> None:
    result = run_real_agent_model_adapter_runtime(
        fixture_id="fixture",
        scenario="agent-model-adapter-local-runtime-success",
        run_control_report_ref=None,
        live_normalization_runtime_report_ref="live-normalization-runtime-report:fixture",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:fixture",
        model_bindings=[_model_binding()],
        agent_bindings=[_agent_binding()],
    )
    assert result.report.failure_type == AgentModelAdapterRuntimeFailureType.MISSING_RUN_CONTROL
