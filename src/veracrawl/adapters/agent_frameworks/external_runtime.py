"""Generic external agent framework runtime adapter wrapper."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any, cast

from veracrawl.contracts.agent import AgentRunRequest, AgentRunResult


class ExternalAgentFrameworkRuntimeAdapter:
    def __init__(
        self,
        *,
        framework_name: str,
        module_name: str,
        callable_name: str = "run_agent",
    ) -> None:
        self.framework_name = framework_name
        self.module_name = module_name
        self.callable_name = callable_name

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        module = importlib.import_module(self.module_name)
        raw_callable = getattr(module, self.callable_name, None)
        if raw_callable is None:
            raise RuntimeError(
                f"{self.module_name}.{self.callable_name} is not configured"
            )
        run_agent = cast(Callable[[AgentRunRequest], AgentRunResult | dict[str, Any]], raw_callable)
        result = run_agent(request)
        if isinstance(result, AgentRunResult):
            return result
        return AgentRunResult.model_validate(result)


def build_agent_runtime(
    *,
    framework_name: str,
    module_name: str,
    callable_name: str = "run_agent",
) -> ExternalAgentFrameworkRuntimeAdapter:
    return ExternalAgentFrameworkRuntimeAdapter(
        framework_name=framework_name,
        module_name=module_name,
        callable_name=callable_name,
    )
