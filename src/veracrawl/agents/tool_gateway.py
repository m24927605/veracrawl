"""Tool gateway validation."""

from __future__ import annotations

from veracrawl.agents.recommendations import recommendation_to_owner_command
from veracrawl.contracts.agent import AgentRecommendation
from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.enums import CommandResultStatus


class InMemoryToolGateway:
    """Minimal gateway that keeps mutations command/result backed."""

    def execute(self, command: CommandEnvelope) -> CommandResult:
        return CommandResult(
            id=f"result:{command.id}",
            command_id=command.id,
            result=CommandResultStatus.COMMITTED,
            emitted_event_refs=[f"event:{command.id}:committed"],
            output_refs=[f"output:{command.id}"],
        )

    def command_for_recommendation(self, recommendation: AgentRecommendation) -> CommandEnvelope:
        return recommendation_to_owner_command(recommendation)

    def execute_recommendation(self, recommendation: AgentRecommendation) -> CommandResult:
        command = self.command_for_recommendation(recommendation)
        return self.execute(command)
