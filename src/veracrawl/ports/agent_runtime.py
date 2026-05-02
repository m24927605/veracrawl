"""Framework-neutral agent runtime ports."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.agent import (
    AgentRunRequest,
    AgentRunResult,
    ContextBundle,
    ContextRef,
    ModelRequest,
    ModelResponse,
)
from veracrawl.contracts.command import CommandEnvelope, CommandResult


class AgentRuntimePort(Protocol):
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...


class ModelProviderPort(Protocol):
    def complete(self, request: ModelRequest) -> ModelResponse: ...


class ToolGatewayPort(Protocol):
    def execute(self, command: CommandEnvelope) -> CommandResult: ...


class ContextStorePort(Protocol):
    def read_context_refs(self, refs: list[ContextRef]) -> ContextBundle: ...
