"""Tool gateway validation."""

from __future__ import annotations

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
