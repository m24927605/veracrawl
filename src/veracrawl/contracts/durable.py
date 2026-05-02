"""Durable runtime persistence contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    DurableCommandRecordStatus,
    OutboxStatus,
    UnitOfWorkStatus,
)


class UnitOfWorkRecord(TimestampedModel):
    id: str
    run_ref: Ref
    status: UnitOfWorkStatus = UnitOfWorkStatus.OPEN
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    committed_at_ref: Ref | None = None
    failure_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unit_of_work(self) -> UnitOfWorkRecord:
        if self.status == UnitOfWorkStatus.COMMITTED:
            if not (self.command_record_refs or self.event_refs):
                raise ValueError("committed unit of work requires command records or events")
            if not self.committed_at_ref:
                raise ValueError("committed unit of work requires committed_at_ref")
        if self.status == UnitOfWorkStatus.FAILED and not self.failure_refs:
            raise ValueError("failed unit of work requires failure_refs")
        return self


class DurableCommandRecord(TimestampedModel):
    id: str
    command_ref: Ref
    command_type: str
    target_aggregate_type: str
    target_aggregate_id: str
    idempotency_key: str
    command_result_ref: Ref | None = None
    event_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    status: DurableCommandRecordStatus = DurableCommandRecordStatus.RECORDED
    duplicate_of_ref: Ref | None = None
    rejection_reason_refs: list[Ref] = Field(default_factory=list)

    @property
    def identity(self) -> str:
        return (
            f"{self.command_type}|{self.target_aggregate_type}|"
            f"{self.target_aggregate_id}|{self.idempotency_key}"
        )

    @model_validator(mode="after")
    def validate_record(self) -> DurableCommandRecord:
        if self.status == DurableCommandRecordStatus.COMMITTED:
            if not self.command_result_ref or not self.event_refs:
                raise ValueError("committed durable command requires result and event refs")
        if self.status == DurableCommandRecordStatus.DUPLICATE and not self.duplicate_of_ref:
            raise ValueError("duplicate durable command requires duplicate_of_ref")
        if self.status == DurableCommandRecordStatus.REJECTED and not self.rejection_reason_refs:
            raise ValueError("rejected durable command requires rejection reasons")
        return self


class OutboxRecord(TimestampedModel):
    id: str
    run_ref: Ref
    command_result_ref: Ref
    event_ref: Ref
    dispatch_topic: str
    payload_ref: Ref
    idempotency_key: str
    status: OutboxStatus = OutboxStatus.PENDING
    attempt_count: int = 0
    dispatched_at_ref: Ref | None = None
    last_error_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_outbox(self) -> OutboxRecord:
        if self.attempt_count < 0:
            raise ValueError("outbox attempt_count must be non-negative")
        if self.status == OutboxStatus.DISPATCHED and not self.dispatched_at_ref:
            raise ValueError("dispatched outbox record requires dispatched_at_ref")
        if self.status == OutboxStatus.FAILED and not self.last_error_ref:
            raise ValueError("failed outbox record requires last_error_ref")
        return self


class EventCursorRecord(TimestampedModel):
    id: str
    run_ref: Ref
    from_sequence: int
    to_sequence: int
    event_refs: list[Ref] = Field(default_factory=list)
    contiguous: bool = True
    missing_sequence_numbers: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_cursor(self) -> EventCursorRecord:
        if self.from_sequence < 1 or self.to_sequence < self.from_sequence:
            raise ValueError("event cursor range is invalid")
        expected_count = self.to_sequence - self.from_sequence + 1
        if self.contiguous and len(self.event_refs) != expected_count:
            raise ValueError("contiguous event cursor requires complete event refs")
        if not self.contiguous and not self.missing_sequence_numbers:
            raise ValueError("non-contiguous event cursor requires missing sequence numbers")
        return self


class DurableFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_publication: bool = False
    required_ref_types: list[str] = Field(default_factory=list)
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> DurableFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("durable fixture must support target profile")
        if self.negative_case and self.expected_publication:
            raise ValueError("negative durable fixture must not expect publication")
        if not self.required_ref_types:
            raise ValueError("durable fixture requires ref type expectations")
        return self
