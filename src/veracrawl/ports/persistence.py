"""Persistence and queue runtime ports."""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import DurableCommandRecord, EventCursorRecord, OutboxRecord
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceMigrationRecord,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)
from veracrawl.contracts.scale import QueueItem, RetryDeadLetterRecord, ShardLease

ModelT = TypeVar("ModelT", bound=BaseModel)


class CanonicalMetadataDocumentPort(Protocol):
    def save_canonical_model(self, collection: str, key: Ref, model: BaseModel) -> Ref: ...

    def load_canonical_model(
        self,
        collection: str,
        key: Ref,
        model_type: type[ModelT],
    ) -> ModelT | None: ...


class MetadataPersistencePort(Protocol):
    def save_command_record(self, record: DurableCommandRecord) -> Ref: ...

    def find_idempotency_record(self, command_identity: str) -> IdempotencyPersistenceRecord | None:
        ...

    def save_idempotency_record(self, record: IdempotencyPersistenceRecord) -> Ref: ...


class EventLogPersistencePort(Protocol):
    def append_event(self, event: CrawlRunEvent) -> Ref: ...

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]: ...

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord: ...


class OutboxPersistencePort(Protocol):
    def append_outbox(self, record: OutboxRecord) -> Ref: ...

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]: ...

    def mark_outbox_dispatched(self, outbox_ref: Ref, *, dispatched_at_ref: Ref) -> OutboxRecord:
        ...

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord: ...


class ArtifactIndexPersistencePort(Protocol):
    def register_artifact_ref(self, artifact_ref: Ref) -> Ref: ...

    def has_artifact_ref(self, artifact_ref: Ref) -> bool: ...


class MigrationPersistencePort(Protocol):
    def save_migration_record(self, record: PersistenceMigrationRecord) -> Ref: ...

    def list_migration_records(self) -> list[PersistenceMigrationRecord]: ...


class QueuePersistencePort(Protocol):
    def enqueue_queue_item(self, item: QueueItem) -> PersistentQueueOperationRecord: ...

    def acquire_queue_lease(
        self,
        item: QueueItem,
        lease: ShardLease,
    ) -> PersistentQueueOperationRecord: ...

    def heartbeat_queue_lease(
        self,
        lease_ref: Ref,
        *,
        lease_token_ref: Ref,
        heartbeat_ref: Ref,
    ) -> PersistentQueueOperationRecord: ...

    def ack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        command_result_ref: Ref,
    ) -> PersistentQueueOperationRecord: ...

    def nack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        failure_refs: list[Ref],
        recovery_refs: list[Ref],
    ) -> PersistentQueueOperationRecord: ...

    def dead_letter_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        dead_letter: RetryDeadLetterRecord,
    ) -> PersistentQueueOperationRecord: ...


class PersistenceTransactionPort(Protocol):
    def begin_transaction(
        self,
        *,
        run_ref: Ref,
        unit_of_work_ref: Ref,
    ) -> PersistenceTransactionRecord: ...

    def commit_transaction(
        self,
        record: PersistenceTransactionRecord,
    ) -> PersistenceTransactionRecord:
        ...

    def rollback_transaction(
        self,
        record: PersistenceTransactionRecord,
        *,
        reason_ref: Ref,
    ) -> PersistenceTransactionRecord: ...


class PersistenceCommandHandlerPort(Protocol):
    def handle_command_once(
        self,
        command: CommandEnvelope,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        plan_ref: Ref,
        event_type: str,
        output_refs: list[Ref],
    ) -> tuple[
        DurableCommandRecord,
        CommandResult,
        OutboxRecord,
        IdempotencyPersistenceRecord,
        bool,
    ]:
        ...
