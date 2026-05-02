"""LangGraph conformance stub.

This adapter intentionally does not import LangGraph. Framework-native graph
state is represented only by diagnostic refs.
"""

from __future__ import annotations

from veracrawl.contracts.agent import (
    AgentActionTrace,
    AgentRunRequest,
    AgentRunResult,
    ContextBundleTrace,
)
from veracrawl.contracts.enums import AgentRunStatus


class LangGraphConformanceAdapter:
    framework_name = "LangGraph"

    def __init__(self) -> None:
        self.last_trace: AgentActionTrace | None = None
        self.last_context_trace: ContextBundleTrace | None = None
        self.diagnostic_state_ref: str | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        context_trace = ContextBundleTrace(
            id=f"context-trace:{request.id}",
            run_id=request.run_id,
            agent_id="agent:langgraph",
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
            agent_id="agent:langgraph",
            agent_role=request.agent_role,
            runtime_spec_id=request.runtime_spec_id,
            model_call_trace_refs=[],
            context_bundle_trace_id=context_trace.id,
            tool_call_trace_refs=[],
            command_result_refs=[],
            policy_decision_refs=request.policy_decision_refs,
            input_refs=[request.context_bundle_id],
            output_refs=[f"agent-output:{request.id}"],
            reasoning_summary_ref=f"reasoning:{request.id}",
            assumptions=["workflow conformance stub"],
            alternatives_considered=["single agent runtime"],
            uncertainty_notes=["diagnostic graph state is not canonical"],
            redaction_policy_ref="redaction:default",
            retention_policy_ref="retention:foundation",
        )
        self.last_context_trace = context_trace
        self.last_trace = trace
        self.diagnostic_state_ref = f"diagnostic-framework-state:{request.id}"
        return AgentRunResult(
            id=f"agent-result:{request.id}",
            agent_run_request_id=request.id,
            agent_action_trace_id=trace.id,
            output_ref=f"agent-output:{request.id}",
            proposed_tool_call_refs=[],
            recommendation_refs=[self.diagnostic_state_ref],
            status=AgentRunStatus.COMPLETED,
        )
