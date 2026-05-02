"""OpenAI Agent SDK conformance stub.

This adapter intentionally does not import the real SDK. It proves the adapter
boundary maps framework-shaped execution into VeraCrawl contracts.
"""

from __future__ import annotations

from veracrawl.contracts.agent import (
    AgentActionTrace,
    AgentRunRequest,
    AgentRunResult,
    ContextBundleTrace,
    ModelCallTrace,
)
from veracrawl.contracts.enums import AgentRunStatus


class OpenAIAgentSDKConformanceAdapter:
    framework_name = "OpenAI Agent SDK"

    def __init__(self) -> None:
        self.last_trace: AgentActionTrace | None = None
        self.last_context_trace: ContextBundleTrace | None = None
        self.last_model_trace: ModelCallTrace | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        context_trace = ContextBundleTrace(
            id=f"context-trace:{request.id}",
            run_id=request.run_id,
            agent_id="agent:openai-sdk",
            context_ref_schema="ContextRef",
            included_context_refs=[request.context_bundle_id],
            sanitized_context_ref=f"sanitized:{request.context_bundle_id}",
            redaction_policy_ref="redaction:default",
            credential_exposure_check_ref="credential-check:none",
        )
        trace = AgentActionTrace(
            id=f"agent-trace:{request.id}",
            run_id=request.run_id,
            objective_id=request.objective_ref,
            agent_id="agent:openai-sdk",
            agent_role=request.agent_role,
            runtime_spec_id=request.runtime_spec_id,
            model_call_trace_refs=[f"model-trace:{request.id}"],
            context_bundle_trace_id=context_trace.id,
            tool_call_trace_refs=[],
            command_result_refs=[],
            policy_decision_refs=request.policy_decision_refs,
            input_refs=[request.context_bundle_id],
            output_refs=[f"agent-output:{request.id}"],
            reasoning_summary_ref=f"reasoning:{request.id}",
            assumptions=["foundation conformance stub"],
            alternatives_considered=["native runtime"],
            uncertainty_notes=[],
            redaction_policy_ref="redaction:default",
            retention_policy_ref="retention:foundation",
        )
        model_trace = ModelCallTrace(
            id=f"model-trace:{request.id}",
            run_id=request.run_id,
            agent_action_trace_id=trace.id,
            provider_name="openai-agent-sdk",
            model_id="fixture-model",
            model_version="fixture",
            prompt_template_ref="prompt:planner",
            prompt_template_version="1",
            context_bundle_trace_id=context_trace.id,
            request_ref=f"model-request:{request.id}",
            response_ref=f"model-response:{request.id}",
            token_usage={"input": 1, "output": 1},
            latency_ms=1,
            redaction_policy_ref="redaction:default",
        )
        self.last_context_trace = context_trace
        self.last_trace = trace
        self.last_model_trace = model_trace
        return AgentRunResult(
            id=f"agent-result:{request.id}",
            agent_run_request_id=request.id,
            agent_action_trace_id=trace.id,
            output_ref=f"agent-output:{request.id}",
            proposed_tool_call_refs=[],
            recommendation_refs=[f"recommendation:{request.id}"],
            status=AgentRunStatus.COMPLETED,
        )
