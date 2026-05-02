"""Durable runtime persistence ports."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import (
    DurableCommandRecord,
    EventCursorRecord,
    OutboxRecord,
    UnitOfWorkRecord,
)
from veracrawl.contracts.event import CrawlRunEvent


class UnitOfWorkPort(Protocol):
    def begin(self, *, run_ref: Ref) -> UnitOfWorkRecord: ...

    def commit(self, unit_of_work_ref: Ref) -> UnitOfWorkRecord: ...

    def rollback(self, unit_of_work_ref: Ref, *, reason_ref: Ref) -> UnitOfWorkRecord: ...


class DurableCommandRepositoryPort(Protocol):
    def save_command_record(self, record: DurableCommandRecord) -> Ref: ...

    def find_command_record(
        self,
        *,
        command_type: str,
        target_aggregate_type: str,
        target_aggregate_id: str,
        idempotency_key: str,
    ) -> DurableCommandRecord | None: ...

    def get_command_result(self, result_ref: Ref) -> CommandResult | None: ...


class DurableEventStorePort(Protocol):
    def append_event(self, event: CrawlRunEvent) -> Ref: ...

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]: ...

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord: ...


class OutboxRepositoryPort(Protocol):
    def append_outbox(self, record: OutboxRecord) -> Ref: ...

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]: ...

    def mark_outbox_dispatched(
        self, outbox_ref: Ref, *, dispatched_at_ref: Ref
    ) -> OutboxRecord: ...

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord: ...


class DurableArtifactIndexPort(Protocol):
    def register_artifact_ref(self, artifact_ref: Ref) -> Ref: ...

    def has_artifact_ref(self, artifact_ref: Ref) -> bool: ...


class DurableCommandHandlerPort(Protocol):
    def handle_command(
        self,
        command: CommandEnvelope,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        plan_ref: Ref,
        event_type: str,
        output_refs: list[Ref],
    ) -> tuple[DurableCommandRecord, CommandResult, OutboxRecord, bool]: ...
