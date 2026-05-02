"""Reusable conformance checks for agent framework adapters."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.agent import AgentActionTrace, AgentRunRequest, AgentRunResult
from veracrawl.contracts.errors import AdapterConformanceError
from veracrawl.ports.agent_runtime import AgentRuntimePort


@dataclass(frozen=True)
class AgentConformanceResult:
    framework_name: str
    request: AgentRunRequest
    result: AgentRunResult
    trace: AgentActionTrace


def assert_agent_conformance(
    framework_name: str,
    runtime: AgentRuntimePort,
    request: AgentRunRequest,
    trace: AgentActionTrace,
) -> AgentConformanceResult:
    result = runtime.run(request)
    if result.agent_run_request_id != request.id:
        raise AdapterConformanceError("agent result does not reference request")
    if result.agent_action_trace_id != trace.id:
        raise AdapterConformanceError("agent result does not reference canonical trace")
    if trace.runtime_spec_id != request.runtime_spec_id:
        raise AdapterConformanceError("trace runtime spec does not match request")
    return AgentConformanceResult(framework_name, request, result, trace)
