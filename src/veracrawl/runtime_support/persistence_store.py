"""Reference filesystem persistence store for adapter-contract fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import DurableCommandRecord, EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import (
    CommandResultStatus,
    DurableCommandRecordStatus,
    OutboxStatus,
    PersistentQueueOperation,
    ScaleQueueItemStatus,
    UnitOfWorkStatus,
)
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)
from veracrawl.contracts.scale import QueueItem, RetryDeadLetterRecord, ShardLease
from veracrawl.runtime_events.durable import build_event_cursor_record

ModelT = TypeVar("ModelT", bound=BaseModel)


class ReferencePersistenceStore:
    """Small filesystem-backed store that exercises persistence ports without vendor SDKs."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def reopen(self) -> ReferencePersistenceStore:
        return ReferencePersistenceStore(self.root)

    def _path(self, name: str) -> Path:
        return self.root / f"{name}.json"

    def _load_mapping(self, name: str) -> dict[str, Any]:
        path = self._path(name)
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return data

    def _write_mapping(self, name: str, data: dict[str, Any]) -> None:
        path = self._path(name)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def _put_model(self, name: str, key: Ref, model: BaseModel) -> Ref:
        data = self._load_mapping(name)
        data[key] = model.model_dump(mode="json")
        self._write_mapping(name, data)
        return key

    def _get_model(self, name: str, key: Ref, model_type: type[ModelT]) -> ModelT | None:
        data = self._load_mapping(name).get(key)
        if data is None:
            return None
        return model_type.model_validate(data)

    def _list_models(self, name: str, model_type: type[ModelT]) -> list[ModelT]:
        return [model_type.model_validate(value) for value in self._load_mapping(name).values()]

    def save_canonical_model(self, collection: str, key: Ref, model: BaseModel) -> Ref:
        return self._put_model(f"canonical_{collection}", key, model)

    def load_canonical_model(
        self,
        collection: str,
        key: Ref,
        model_type: type[ModelT],
    ) -> ModelT | None:
        return self._get_model(f"canonical_{collection}", key, model_type)

    def begin_transaction(
        self,
        *,
        run_ref: Ref,
        unit_of_work_ref: Ref,
        adapter_ref: Ref = "persistence-adapter:reference-filesystem",
    ) -> PersistenceTransactionRecord:
        record = PersistenceTransactionRecord(
            id=f"persistence-transaction:{run_ref}:{len(self._load_mapping('transactions')) + 1}",
            adapter_ref=adapter_ref,
            run_ref=run_ref,
            unit_of_work_ref=unit_of_work_ref,
        )
        self._put_model("transactions", record.id, record)
        return record

    def commit_transaction(
        self,
        record: PersistenceTransactionRecord,
    ) -> PersistenceTransactionRecord:
        updated = record.model_copy(
            update={
                "status": UnitOfWorkStatus.COMMITTED,
                "committed_at_ref": f"clock:{record.id}:committed",
            }
        )
        self._put_model("transactions", updated.id, updated)
        return updated

    def rollback_transaction(
        self,
        record: PersistenceTransactionRecord,
        *,
        reason_ref: Ref,
    ) -> PersistenceTransactionRecord:
        updated = record.model_copy(
            update={
                "status": UnitOfWorkStatus.ROLLED_BACK,
                "rollback_reason_refs": [reason_ref],
            }
        )
        self._put_model("transactions", updated.id, updated)
        return updated

    def save_command_record(self, record: DurableCommandRecord) -> Ref:
        return self._put_model("command_records", record.id, record)

    def save_command_result(self, result: CommandResult) -> Ref:
        return self._put_model("command_results", result.id, result)

    def get_command_result(self, result_ref: Ref) -> CommandResult | None:
        return self._get_model("command_results", result_ref, CommandResult)

    def save_idempotency_record(self, record: IdempotencyPersistenceRecord) -> Ref:
        return self._put_model("idempotency_records", record.id, record)

    def find_idempotency_record(self, command_identity: str) -> IdempotencyPersistenceRecord | None:
        for record in self._list_models("idempotency_records", IdempotencyPersistenceRecord):
            if (
                record.command_identity == command_identity
                and record.status == DurableCommandRecordStatus.COMMITTED
            ):
                return record
        return None

    def append_event(self, event: CrawlRunEvent) -> Ref:
        events = self.stream_events(event.run_id)
        expected = len(events) + 1
        if event.sequence != expected:
            raise ValueError(
                f"event sequence gap for {event.run_id}: expected {expected}, got {event.sequence}"
            )
        return self._put_model("events", event.id, event)

    def force_append_event_for_fixture(self, event: CrawlRunEvent) -> Ref:
        return self._put_model("events", event.id, event)

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]:
        events = [
            event for event in self._list_models("events", CrawlRunEvent) if event.run_id == run_ref
        ]
        return sorted(events, key=lambda event: event.sequence)

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord:
        return build_event_cursor_record(run_ref, self.stream_events(run_ref))

    def append_outbox(self, record: OutboxRecord) -> Ref:
        return self._put_model("outbox_records", record.id, record)

    def list_outbox(self, run_ref: Ref | None = None) -> list[OutboxRecord]:
        records = self._list_models("outbox_records", OutboxRecord)
        if run_ref is None:
            return records
        return [record for record in records if record.run_ref == run_ref]

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        return [
            record
            for record in self.list_outbox(run_ref)
            if record.status == OutboxStatus.PENDING
        ]

    def mark_outbox_dispatched(self, outbox_ref: Ref, *, dispatched_at_ref: Ref) -> OutboxRecord:
        current = self._get_model("outbox_records", outbox_ref, OutboxRecord)
        if current is None:
            raise ValueError(f"unknown outbox record: {outbox_ref}")
        if current.status == OutboxStatus.DISPATCHED:
            return current
        updated = current.model_copy(
            update={
                "status": OutboxStatus.DISPATCHED,
                "dispatched_at_ref": dispatched_at_ref,
                "attempt_count": current.attempt_count + 1,
            }
        )
        self.append_outbox(updated)
        return updated

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        current = self._get_model("outbox_records", outbox_ref, OutboxRecord)
        if current is None:
            raise ValueError(f"unknown outbox record: {outbox_ref}")
        updated = current.model_copy(
            update={
                "status": OutboxStatus.FAILED,
                "last_error_ref": error_ref,
                "attempt_count": current.attempt_count + 1,
            }
        )
        self.append_outbox(updated)
        return updated

    def register_artifact_ref(self, artifact_ref: Ref) -> Ref:
        data = self._load_mapping("artifact_refs")
        data[artifact_ref] = {"id": artifact_ref}
        self._write_mapping("artifact_refs", data)
        return artifact_ref

    def remove_artifact_ref_for_fixture(self, artifact_ref: Ref) -> None:
        data = self._load_mapping("artifact_refs")
        data.pop(artifact_ref, None)
        self._write_mapping("artifact_refs", data)

    def has_artifact_ref(self, artifact_ref: Ref) -> bool:
        return artifact_ref in self._load_mapping("artifact_refs")

    def list_artifact_refs(self) -> list[Ref]:
        return sorted(self._load_mapping("artifact_refs"))

    def enqueue_queue_item(self, item: QueueItem) -> PersistentQueueOperationRecord:
        self._put_model("queue_items", item.id, item)
        return self._record_queue_operation(
            queue_name=item.queue_name,
            operation=PersistentQueueOperation.ENQUEUE,
            queue_item_ref=item.id,
            policy_decision_refs=[],
        )

    def acquire_queue_lease(
        self,
        item: QueueItem,
        lease: ShardLease,
    ) -> PersistentQueueOperationRecord:
        self._put_model("queue_items", item.id, item)
        self._put_model("shard_leases", lease.id, lease)
        return self._record_queue_operation(
            queue_name=item.queue_name,
            operation=PersistentQueueOperation.LEASE,
            queue_item_ref=item.id,
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token,
            policy_decision_refs=lease.policy_decision_refs,
        )

    def heartbeat_queue_lease(
        self,
        lease_ref: Ref,
        *,
        lease_token_ref: Ref,
        heartbeat_ref: Ref,
    ) -> PersistentQueueOperationRecord:
        lease = self._get_model("shard_leases", lease_ref, ShardLease)
        if lease is None or lease.lease_token != lease_token_ref:
            raise ValueError(f"invalid shard lease token for {lease_ref}")
        return self._record_queue_operation(
            queue_name=lease.queue_name,
            operation=PersistentQueueOperation.HEARTBEAT,
            queue_item_ref=f"queue-item-for:{lease_ref}",
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token,
            heartbeat_ref=heartbeat_ref,
            policy_decision_refs=lease.policy_decision_refs,
        )

    def ack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        command_result_ref: Ref,
    ) -> PersistentQueueOperationRecord:
        item = self._get_model("queue_items", item_ref, QueueItem)
        lease = self._get_model("shard_leases", lease_ref, ShardLease)
        if item is None or lease is None or lease.lease_token != lease_token_ref:
            raise ValueError(f"invalid queue ack refs for {item_ref}")
        updated_item = item.model_copy(update={"status": ScaleQueueItemStatus.ACKED})
        self._put_model("queue_items", updated_item.id, updated_item)
        return self._record_queue_operation(
            queue_name=item.queue_name,
            operation=PersistentQueueOperation.ACK,
            queue_item_ref=item.id,
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token,
            command_result_ref=command_result_ref,
            policy_decision_refs=lease.policy_decision_refs,
        )

    def nack_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        failure_refs: list[Ref],
        recovery_refs: list[Ref],
    ) -> PersistentQueueOperationRecord:
        item = self._get_model("queue_items", item_ref, QueueItem)
        lease = self._get_model("shard_leases", lease_ref, ShardLease)
        if item is None or lease is None or lease.lease_token != lease_token_ref:
            raise ValueError(f"invalid queue nack refs for {item_ref}")
        updated_item = item.model_copy(update={"status": ScaleQueueItemStatus.NACKED})
        self._put_model("queue_items", updated_item.id, updated_item)
        return self._record_queue_operation(
            queue_name=item.queue_name,
            operation=PersistentQueueOperation.NACK,
            queue_item_ref=item.id,
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token,
            failure_record_refs=failure_refs,
            recovery_action_refs=recovery_refs,
            policy_decision_refs=lease.policy_decision_refs,
        )

    def dead_letter_queue_item(
        self,
        item_ref: Ref,
        *,
        lease_ref: Ref,
        lease_token_ref: Ref,
        dead_letter: RetryDeadLetterRecord,
    ) -> PersistentQueueOperationRecord:
        item = self._get_model("queue_items", item_ref, QueueItem)
        lease = self._get_model("shard_leases", lease_ref, ShardLease)
        if item is None or lease is None or lease.lease_token != lease_token_ref:
            raise ValueError(f"invalid queue dead-letter refs for {item_ref}")
        updated_item = item.model_copy(update={"status": ScaleQueueItemStatus.DEAD_LETTERED})
        self._put_model("queue_items", updated_item.id, updated_item)
        self._put_model("dead_letters", dead_letter.id, dead_letter)
        return self._record_queue_operation(
            queue_name=item.queue_name,
            operation=PersistentQueueOperation.DEAD_LETTER,
            queue_item_ref=item.id,
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token,
            failure_record_refs=[dead_letter.failure_record_id],
            recovery_action_refs=dead_letter.recovery_action_refs,
            dead_letter_ref=dead_letter.id,
            policy_decision_refs=lease.policy_decision_refs,
        )

    def list_queue_operations(self) -> list[PersistentQueueOperationRecord]:
        return self._list_models("queue_operations", PersistentQueueOperationRecord)

    def _record_queue_operation(
        self,
        *,
        queue_name: Any,
        operation: PersistentQueueOperation,
        queue_item_ref: Ref,
        lease_ref: Ref | None = None,
        lease_token_ref: Ref | None = None,
        heartbeat_ref: Ref | None = None,
        command_result_ref: Ref | None = None,
        failure_record_refs: list[Ref] | None = None,
        recovery_action_refs: list[Ref] | None = None,
        dead_letter_ref: Ref | None = None,
        policy_decision_refs: list[Ref] | None = None,
    ) -> PersistentQueueOperationRecord:
        count = len(self._load_mapping("queue_operations")) + 1
        record = PersistentQueueOperationRecord(
            id=f"persistent-queue-operation:{queue_item_ref}:{operation.value}:{count}",
            queue_name=queue_name,
            operation=operation,
            queue_item_ref=queue_item_ref,
            lease_ref=lease_ref,
            lease_token_ref=lease_token_ref,
            heartbeat_ref=heartbeat_ref,
            command_result_ref=command_result_ref,
            failure_record_refs=failure_record_refs or [],
            recovery_action_refs=recovery_action_refs or [],
            dead_letter_ref=dead_letter_ref,
            policy_decision_refs=policy_decision_refs or [],
        )
        self._put_model("queue_operations", record.id, record)
        return record

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
        command_identity = (
            f"{command.command_type}|{command.target_aggregate_type}|"
            f"{command.target_aggregate_id}|{command.idempotency_key}"
        )
        existing = self.find_idempotency_record(command_identity)
        if existing is not None and existing.command_result_ref is not None:
            result = self.get_command_result(existing.command_result_ref)
            outbox = self._get_model("outbox_records", existing.outbox_refs[0], OutboxRecord)
            if result is None or outbox is None:
                raise ValueError("idempotency record points to missing result or outbox")
            duplicate_command = DurableCommandRecord(
                id=f"durable-command-duplicate:{command.id}",
                command_ref=command.id,
                command_type=command.command_type,
                target_aggregate_type=command.target_aggregate_type,
                target_aggregate_id=command.target_aggregate_id,
                idempotency_key=command.idempotency_key,
                command_result_ref=result.id,
                event_refs=existing.event_refs,
                outbox_refs=existing.outbox_refs,
                status=DurableCommandRecordStatus.DUPLICATE,
                duplicate_of_ref=existing.command_record_ref,
            )
            duplicate_idempotency = IdempotencyPersistenceRecord(
                id=f"idempotency-duplicate:{command.id}",
                idempotency_key=command.idempotency_key,
                command_identity=command_identity,
                command_record_ref=duplicate_command.id,
                duplicate_of_ref=existing.id,
                status=DurableCommandRecordStatus.DUPLICATE,
            )
            self.save_idempotency_record(duplicate_idempotency)
            return duplicate_command, result, outbox, duplicate_idempotency, True

        sequence = len(self.stream_events(run_ref)) + 1
        event = CrawlRunEvent(
            id=f"event:{run_ref}:{sequence}",
            run_id=run_ref,
            objective_id=objective_ref,
            crawl_plan_id=plan_ref,
            sequence=sequence,
            event_type=event_type,
            event_type_spec_id=f"event-type:{event_type}",
            payload_ref=command.payload_ref,
            causation_id=command.id,
            correlation_id=f"corr:{run_ref}",
            trace_id=f"trace:{run_ref}:{sequence}",
            output_refs=output_refs,
            policy_decision_refs=command.policy_decision_refs,
            idempotency_key=f"event:{command.id}",
            state_before={"status": "accepted"},
            state_after={"status": "committed"},
        )
        self.append_event(event)
        result = CommandResult(
            id=f"command-result:{command.id}",
            command_id=command.id,
            result=CommandResultStatus.COMMITTED,
            emitted_event_refs=[event.id],
            output_refs=output_refs,
        )
        self.save_command_result(result)
        outbox = OutboxRecord(
            id=f"outbox:{command.id}",
            run_ref=run_ref,
            command_result_ref=result.id,
            event_ref=event.id,
            dispatch_topic=f"topic:{event_type}",
            payload_ref=command.payload_ref,
            idempotency_key=f"outbox:{command.id}",
        )
        self.append_outbox(outbox)
        record = DurableCommandRecord(
            id=f"durable-command:{command.id}",
            command_ref=command.id,
            command_type=command.command_type,
            target_aggregate_type=command.target_aggregate_type,
            target_aggregate_id=command.target_aggregate_id,
            idempotency_key=command.idempotency_key,
            command_result_ref=result.id,
            event_refs=[event.id],
            outbox_refs=[outbox.id],
            status=DurableCommandRecordStatus.COMMITTED,
        )
        self.save_command_record(record)
        idempotency = IdempotencyPersistenceRecord(
            id=f"idempotency:{command.id}",
            idempotency_key=command.idempotency_key,
            command_identity=command_identity,
            command_record_ref=record.id,
            command_result_ref=result.id,
            event_refs=[event.id],
            outbox_refs=[outbox.id],
            status=DurableCommandRecordStatus.COMMITTED,
        )
        self.save_idempotency_record(idempotency)
        return record, result, outbox, idempotency, False
