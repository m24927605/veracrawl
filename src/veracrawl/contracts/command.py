"""Command contract models."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CommandResultStatus, CommandStatus, OwnerService


class BaseCommandPayload(TimestampedModel):
    command_payload_id: str
    target_ref: Ref
    actor_ref: Ref
    idempotency_key: str
    expected_version: int | None = None
    lease_token_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    input_refs: list[Ref] = Field(default_factory=list)
    output_refs: list[Ref] = Field(default_factory=list)
    reason: str = ""
    redaction_policy_ref: Ref | None = None
    payload_hash: str


class CommandEnvelope(TimestampedModel):
    id: str
    command_type: str
    target_aggregate_type: str
    target_aggregate_id: str
    expected_version: int | None = None
    idempotency_key: str
    actor_ref: Ref
    precondition_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    payload_ref: Ref
    status: CommandStatus = CommandStatus.PROPOSED

    def transition(self, status: CommandStatus) -> CommandEnvelope:
        allowed = {
            CommandStatus.PROPOSED: {
                CommandStatus.ACCEPTED,
                CommandStatus.REJECTED,
                CommandStatus.FAILED,
            },
            CommandStatus.ACCEPTED: {CommandStatus.COMMITTED, CommandStatus.FAILED},
            CommandStatus.REJECTED: set(),
            CommandStatus.COMMITTED: set(),
            CommandStatus.FAILED: set(),
        }
        if status not in allowed[self.status]:
            raise ValueError(f"invalid command transition {self.status.value}->{status.value}")
        return self.model_copy(update={"status": status})


class CommandResult(TimestampedModel):
    id: str
    command_id: str
    result: CommandResultStatus
    emitted_event_refs: list[Ref] = Field(default_factory=list)
    output_refs: list[Ref] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    error: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result(self) -> CommandResult:
        if self.result == CommandResultStatus.COMMITTED and not self.emitted_event_refs:
            raise ValueError("committed command result requires emitted_event_refs")
        if self.result == CommandResultStatus.REJECTED and not self.rejection_reasons:
            raise ValueError("rejected command result requires rejection_reasons")
        if self.result == CommandResultStatus.FAILED and not self.error:
            raise ValueError("failed command result requires error")
        return self


class CommandTypeSpec(TimestampedModel):
    id: str
    command_type: str
    owner_service: OwnerService
    target_aggregate_type: str
    payload_schema_ref: Ref
    precondition_refs: list[Ref] = Field(default_factory=list)
    required_policy_decision_types: list[str] = Field(default_factory=list)
    approval_required: bool = False
    required_approval_subject_types: list[str] = Field(default_factory=list)
    expected_version_required: bool = False
    lease_required: bool = False
    emitted_event_types: list[str] = Field(default_factory=list)
    failure_record_type: str | None = None
