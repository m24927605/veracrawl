"""Native VeraCrawl agent runtime adapter."""

from __future__ import annotations

from veracrawl.contracts.agent import AgentRunRequest, AgentRunResult
from veracrawl.contracts.enums import AgentRunStatus


class NativeAgentRuntimeAdapter:
    framework_name = "VeraCrawl Native Runtime"

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        return AgentRunResult(
            id=f"agent-run-result:{request.run_id}:{request.agent_role.value}",
            agent_run_request_id=request.id,
            agent_action_trace_id=(
                f"agent-action-trace:{request.run_id}:{request.agent_role.value}"
            ),
            output_ref=f"agent-output:{request.run_id}:{request.agent_role.value}",
            proposed_tool_call_refs=[
                f"tool-call-proposal:{request.run_id}:{request.agent_role.value}:read"
            ],
            recommendation_refs=[
                f"agent-recommendation:{request.run_id}:{request.agent_role.value}"
            ],
            status=AgentRunStatus.COMPLETED,
        )


def build_agent_runtime() -> NativeAgentRuntimeAdapter:
    return NativeAgentRuntimeAdapter()
