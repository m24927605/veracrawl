"""Framework-neutral runtime helpers."""

from __future__ import annotations

from veracrawl.contracts.agent import AgentRunRequest, AgentRunResult
from veracrawl.ports.agent_runtime import AgentRuntimePort


def run_agent(runtime: AgentRuntimePort, request: AgentRunRequest) -> AgentRunResult:
    return runtime.run(request)
