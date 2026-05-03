from __future__ import annotations

import sys
from types import ModuleType

import pytest

from veracrawl.adapters.agent_frameworks.external_runtime import (
    ExternalAgentFrameworkRuntimeAdapter,
)
from veracrawl.adapters.agent_frameworks.native_runtime import NativeAgentRuntimeAdapter
from veracrawl.adapters.model_providers.external_runtime import (
    ExternalModelProviderRuntimeAdapter,
)
from veracrawl.adapters.model_providers.local_runtime import LocalModelProviderRuntimeAdapter
from veracrawl.contracts.agent import AgentRunRequest, ModelRequest
from veracrawl.contracts.enums import AgentRole, AgentRunStatus


def _agent_request() -> AgentRunRequest:
    return AgentRunRequest(
        id="agent-run-request:test:planner",
        run_id="run:test",
        agent_role=AgentRole.PLANNER,
        runtime_spec_id="agent-runtime-spec:test:native",
        objective_ref="objective:test",
        context_bundle_id="context-bundle:test:planner",
        required_output_schema_ref="schema:test:planner",
        loop_budget_ref="loop-budget:test",
        policy_decision_refs=["policy:test:agent-model"],
    )


def _model_request() -> ModelRequest:
    return ModelRequest(
        id="model-request:test:planner",
        agent_run_request_id="agent-run-request:test:planner",
        provider_name="Local model runtime",
        model_id="local",
        prompt_template_ref="prompt:test",
        prompt_template_version="1",
        context_bundle_id="context-bundle:test:planner",
        response_schema_ref="schema:test:planner",
        redaction_policy_ref="redaction:test",
    )


def test_local_model_provider_runtime_adapter_completes() -> None:
    response = LocalModelProviderRuntimeAdapter().complete(_model_request())
    assert response.status == "completed"
    assert response.model_request_id == "model-request:test:planner"


def test_native_agent_runtime_adapter_runs() -> None:
    result = NativeAgentRuntimeAdapter().run(_agent_request())
    assert result.status == AgentRunStatus.COMPLETED
    assert result.agent_run_request_id == "agent-run-request:test:planner"


def test_external_model_provider_runtime_adapter_uses_configured_callable() -> None:
    module_name = "veracrawl_test_external_model_provider"
    module = ModuleType(module_name)

    def complete(request: ModelRequest) -> dict[str, object]:
        return {
            "id": f"external-model-response:{request.id}",
            "model_request_id": request.id,
            "response_ref": f"external-response:{request.id}",
            "status": "completed",
        }

    module.complete = complete  # type: ignore[attr-defined]
    sys.modules[module_name] = module
    try:
        adapter = ExternalModelProviderRuntimeAdapter(
            provider_name="OpenAI-compatible endpoint",
            model_id="fixture",
            model_version="1",
            module_name=module_name,
        )
        response = adapter.complete(_model_request())
    finally:
        sys.modules.pop(module_name, None)
    assert response.id == "external-model-response:model-request:test:planner"


def test_external_agent_framework_runtime_adapter_uses_configured_callable() -> None:
    module_name = "veracrawl_test_external_agent_framework"
    module = ModuleType(module_name)

    def run_agent(request: AgentRunRequest) -> dict[str, object]:
        return {
            "id": f"external-agent-result:{request.id}",
            "agent_run_request_id": request.id,
            "agent_action_trace_id": f"external-agent-trace:{request.id}",
            "output_ref": f"external-agent-output:{request.id}",
            "status": "completed",
        }

    module.run_agent = run_agent  # type: ignore[attr-defined]
    sys.modules[module_name] = module
    try:
        adapter = ExternalAgentFrameworkRuntimeAdapter(
            framework_name="LangGraph",
            module_name=module_name,
        )
        result = adapter.run(_agent_request())
    finally:
        sys.modules.pop(module_name, None)
    assert result.id == "external-agent-result:agent-run-request:test:planner"


def test_external_wrappers_fail_when_module_is_unavailable() -> None:
    adapter = ExternalAgentFrameworkRuntimeAdapter(
        framework_name="LangChain",
        module_name="veracrawl_missing_agent_framework_module",
    )
    with pytest.raises(ModuleNotFoundError):
        adapter.run(_agent_request())
