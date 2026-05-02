from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.factories import agent_request
from veracrawl.adapters.agent_frameworks.langgraph import LangGraphConformanceAdapter
from veracrawl.adapters.agent_frameworks.openai_agent_sdk import OpenAIAgentSDKConformanceAdapter
from veracrawl.agents.recommendations import intake_agent_recommendation
from veracrawl.agents.tool_gateway import InMemoryToolGateway
from veracrawl.contracts.agent import AgentRecommendation
from veracrawl.contracts.enums import AgentRecommendationSubject, AgentRole


def _recommendation(payload_ref: str = "recommendation-payload:1") -> AgentRecommendation:
    return AgentRecommendation(
        id="recommendation:1",
        run_ref="run:1",
        subject_type=AgentRecommendationSubject.EXTRACTION_STRATEGY,
        subject_ref="candidate:1",
        agent_role=AgentRole.EXTRACTOR,
        context_bundle_trace_ref="context-trace:1",
        agent_action_trace_ref="agent-trace:1",
        recommendation_payload_ref=payload_ref,
        policy_decision_refs=["policy:prompt_context"],
    )


def test_recommendation_requires_policy_and_owner_command_when_accepted() -> None:
    with pytest.raises(ValidationError):
        AgentRecommendation(
            id="recommendation:bad",
            run_ref="run:1",
            subject_type=AgentRecommendationSubject.REPAIR,
            subject_ref="candidate:1",
            agent_role=AgentRole.OPS,
            context_bundle_trace_ref="context-trace:1",
            agent_action_trace_ref="agent-trace:1",
            recommendation_payload_ref="payload:1",
        )
    accepted, command = intake_agent_recommendation(_recommendation())
    assert command is not None
    assert accepted.owner_command_ref == command.id
    assert command.command_type == "accept_agent_recommendation"


def test_tool_gateway_converts_recommendation_to_command_without_direct_mutation() -> None:
    accepted, _ = intake_agent_recommendation(_recommendation())
    result = InMemoryToolGateway().execute_recommendation(accepted)
    assert result.output_refs == [f"output:cmd:{accepted.id}:owner-command"]


def test_forbidden_context_recommendations_are_rejected() -> None:
    rejected, command = intake_agent_recommendation(_recommendation("raw_secret:payload"))
    assert command is None
    assert rejected.rejection_reasons
    assert rejected.owner_command_ref is None


def test_framework_adapter_swap_keeps_veracrawl_canonical_subject() -> None:
    request = agent_request("agent-request:swap")
    openai_adapter = OpenAIAgentSDKConformanceAdapter()
    langgraph_adapter = LangGraphConformanceAdapter()
    openai_recommendation = openai_adapter.recommendation_fixture(request)
    langgraph_recommendation = langgraph_adapter.recommendation_fixture(request)
    openai_accepted, openai_command = intake_agent_recommendation(openai_recommendation)
    langgraph_accepted, langgraph_command = intake_agent_recommendation(langgraph_recommendation)
    assert openai_command is not None
    assert langgraph_command is not None
    assert openai_accepted.subject_ref == langgraph_accepted.subject_ref == request.objective_ref
    assert openai_command.target_aggregate_id == langgraph_command.target_aggregate_id
    assert "diagnostic-framework-state" not in langgraph_command.target_aggregate_id
