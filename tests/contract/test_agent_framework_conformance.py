from __future__ import annotations

from tests.factories import agent_request
from veracrawl.adapters.agent_frameworks.langgraph import LangGraphConformanceAdapter
from veracrawl.adapters.agent_frameworks.openai_agent_sdk import OpenAIAgentSDKConformanceAdapter
from veracrawl.agents.conformance import assert_agent_conformance


def test_openai_agent_sdk_conformance_stub_maps_to_canonical_contracts() -> None:
    request = agent_request("agent-request:openai")
    adapter = OpenAIAgentSDKConformanceAdapter()
    result = adapter.run(request)
    assert adapter.last_trace is not None
    assert result.agent_action_trace_id == adapter.last_trace.id
    checked = assert_agent_conformance(adapter.framework_name, adapter, request, adapter.last_trace)
    assert checked.result.agent_run_request_id == request.id
    assert adapter.last_model_trace is not None


def test_langgraph_conformance_stub_keeps_framework_state_diagnostic() -> None:
    request = agent_request("agent-request:langgraph")
    adapter = LangGraphConformanceAdapter()
    result = adapter.run(request)
    assert adapter.last_trace is not None
    assert result.agent_action_trace_id == adapter.last_trace.id
    assert adapter.diagnostic_state_ref is not None
    assert adapter.diagnostic_state_ref.startswith("diagnostic-framework-state:")
    checked = assert_agent_conformance(adapter.framework_name, adapter, request, adapter.last_trace)
    assert checked.framework_name == "LangGraph"
