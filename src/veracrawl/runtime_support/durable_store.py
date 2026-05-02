"""Deterministic durable fixture store behind VeraCrawl ports."""

from __future__ import annotations

from dataclasses import dataclass, field

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import (
    DurableCommandRecord,
    EventCursorRecord,
    OutboxRecord,
    UnitOfWorkRecord,
)
from veracrawl.contracts.enums import (
    CommandResultStatus,
    DurableCommandRecordStatus,
    FrontierItemStatus,
    OutboxStatus,
    QueueLeaseStatus,
    UnitOfWorkStatus,
)
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.scheduler import FrontierItem, QueueLease
from veracrawl.runtime_events.durable import build_event_cursor_record


@dataclass
class DurableBackingStore:
    unit_of_work_records: dict[Ref, UnitOfWorkRecord] = field(default_factory=dict)
    command_records: dict[Ref, DurableCommandRecord] = field(default_factory=dict)
    command_identity_index: dict[str, Ref] = field(default_factory=dict)
    command_results: dict[Ref, CommandResult] = field(default_factory=dict)
    events_by_run: dict[Ref, list[CrawlRunEvent]] = field(default_factory=dict)
    outbox_records: dict[Ref, OutboxRecord] = field(default_factory=dict)
    artifact_refs: set[Ref] = field(default_factory=set)
    frontier_items: dict[Ref, FrontierItem] = field(default_factory=dict)
    queue_leases: dict[Ref, QueueLease] = field(default_factory=dict)
    invalid_lease_refs: list[Ref] = field(default_factory=list)
    sequence_overrides: dict[Ref, int] = field(default_factory=dict)


class DeterministicDurableStore:
    def __init__(self, backing: DurableBackingStore | None = None) -> None:
        self.backing = backing or DurableBackingStore()

    def reopen(self) -> DeterministicDurableStore:
        return DeterministicDurableStore(self.backing)

    def begin(self, *, run_ref: Ref) -> UnitOfWorkRecord:
        record = UnitOfWorkRecord(
            id=f"uow:{run_ref}:{len(self.backing.unit_of_work_records) + 1}",
            run_ref=run_ref,
        )
        self.backing.unit_of_work_records[record.id] = record
        return record

    def commit(self, unit_of_work_ref: Ref) -> UnitOfWorkRecord:
        current = self.backing.unit_of_work_records[unit_of_work_ref]
        updated = current.model_copy(
            update={
                "status": UnitOfWorkStatus.COMMITTED,
                "committed_at_ref": f"clock:{unit_of_work_ref}:committed",
            }
        )
        self.backing.unit_of_work_records[updated.id] = updated
        return updated

    def rollback(self, unit_of_work_ref: Ref, *, reason_ref: Ref) -> UnitOfWorkRecord:
        current = self.backing.unit_of_work_records[unit_of_work_ref]
        updated = current.model_copy(
            update={"status": UnitOfWorkStatus.ROLLED_BACK, "failure_refs": [reason_ref]}
        )
        self.backing.unit_of_work_records[updated.id] = updated
        return updated

    def save_command_record(self, record: DurableCommandRecord) -> Ref:
        self.backing.command_records[record.id] = record
        self.backing.command_identity_index[record.identity] = record.id
        return record.id

    def find_command_record(
        self,
        *,
        command_type: str,
        target_aggregate_type: str,
        target_aggregate_id: str,
        idempotency_key: str,
    ) -> DurableCommandRecord | None:
        identity = f"{command_type}|{target_aggregate_type}|{target_aggregate_id}|{idempotency_key}"
        record_ref = self.backing.command_identity_index.get(identity)
        if record_ref is None:
            return None
        return self.backing.command_records[record_ref]

    def get_command_result(self, result_ref: Ref) -> CommandResult | None:
        return self.backing.command_results.get(result_ref)

    def append_event(self, event: CrawlRunEvent) -> Ref:
        events = self.backing.events_by_run.setdefault(event.run_id, [])
        expected = len(events) + 1
        if event.sequence != expected:
            raise ValueError(
                f"event sequence gap for {event.run_id}: expected {expected}, got {event.sequence}"
            )
        events.append(event)
        return event.id

    def force_append_event_for_fixture(self, event: CrawlRunEvent) -> Ref:
        self.backing.events_by_run.setdefault(event.run_id, []).append(event)
        return event.id

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]:
        return list(self.backing.events_by_run.get(run_ref, []))

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord:
        return build_event_cursor_record(run_ref, self.stream_events(run_ref))

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.backing.outbox_records[record.id] = record
        return record.id

    def get_outbox(self, outbox_ref: Ref) -> OutboxRecord | None:
        return self.backing.outbox_records.get(outbox_ref)

    def list_outbox(self, run_ref: Ref | None = None) -> list[OutboxRecord]:
        records = list(self.backing.outbox_records.values())
        if run_ref is not None:
            return [record for record in records if record.run_ref == run_ref]
        return records

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        return [
            record
            for record in self.list_outbox(run_ref)
            if record.status == OutboxStatus.PENDING
        ]

    def mark_outbox_dispatched(self, outbox_ref: Ref, *, dispatched_at_ref: Ref) -> OutboxRecord:
        current = self.backing.outbox_records[outbox_ref]
        if current.status == OutboxStatus.DISPATCHED:
            return current
        updated = current.model_copy(
            update={
                "status": OutboxStatus.DISPATCHED,
                "dispatched_at_ref": dispatched_at_ref,
                "attempt_count": current.attempt_count + 1,
            }
        )
        self.backing.outbox_records[updated.id] = updated
        return updated

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        current = self.backing.outbox_records[outbox_ref]
        updated = current.model_copy(
            update={
                "status": OutboxStatus.FAILED,
                "last_error_ref": error_ref,
                "attempt_count": current.attempt_count + 1,
            }
        )
        self.backing.outbox_records[updated.id] = updated
        return updated

    def register_artifact_ref(self, artifact_ref: Ref) -> Ref:
        self.backing.artifact_refs.add(artifact_ref)
        return artifact_ref

    def remove_artifact_ref_for_fixture(self, artifact_ref: Ref) -> None:
        self.backing.artifact_refs.discard(artifact_ref)

    def has_artifact_ref(self, artifact_ref: Ref) -> bool:
        return artifact_ref in self.backing.artifact_refs

    def save_frontier_item(self, item: FrontierItem) -> Ref:
        self.backing.frontier_items[item.id] = item
        return item.id

    def get_frontier_item(self, item_ref: Ref) -> FrontierItem | None:
        return self.backing.frontier_items.get(item_ref)

    def list_frontier_items(self, run_ref: Ref | None = None) -> list[FrontierItem]:
        items = list(self.backing.frontier_items.values())
        if run_ref is not None:
            return [item for item in items if item.run_ref == run_ref]
        return items

    def save_queue_lease(self, lease: QueueLease) -> Ref:
        self.backing.queue_leases[lease.id] = lease
        return lease.id

    def get_queue_lease(self, lease_ref: Ref) -> QueueLease | None:
        return self.backing.queue_leases.get(lease_ref)

    def list_queue_leases(self, run_ref: Ref | None = None) -> list[QueueLease]:
        leases = list(self.backing.queue_leases.values())
        if run_ref is not None:
            return [lease for lease in leases if lease.run_ref == run_ref]
        return leases

    def record_invalid_lease_ref(self, invalid_ref: Ref) -> None:
        self.backing.invalid_lease_refs.append(invalid_ref)

    def list_invalid_lease_refs(self) -> list[Ref]:
        return list(self.backing.invalid_lease_refs)

    def handle_command(
        self,
        command: CommandEnvelope,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        plan_ref: Ref,
        event_type: str,
        output_refs: list[Ref],
    ) -> tuple[DurableCommandRecord, CommandResult, OutboxRecord, bool]:
        existing = self.find_command_record(
            command_type=command.command_type,
            target_aggregate_type=command.target_aggregate_type,
            target_aggregate_id=command.target_aggregate_id,
            idempotency_key=command.idempotency_key,
        )
        if existing is not None and existing.command_result_ref is not None:
            result = self.backing.command_results[existing.command_result_ref]
            outbox = self.backing.outbox_records[existing.outbox_refs[0]]
            duplicate = DurableCommandRecord(
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
                duplicate_of_ref=existing.id,
            )
            return duplicate, result, outbox, True

        sequence = len(self.backing.events_by_run.get(run_ref, [])) + 1
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
        self.backing.command_results[result.id] = result
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
        return record, result, outbox, False


def mark_frontier_item_status(
    store: DeterministicDurableStore,
    item: FrontierItem,
    *,
    status: FrontierItemStatus,
    lease_ref: Ref | None = None,
    result_refs: list[Ref] | None = None,
    failure_refs: list[Ref] | None = None,
    last_error_ref: Ref | None = None,
    attempt_count: int | None = None,
) -> FrontierItem:
    updated = item.model_copy(
        update={
            "status": status,
            "lease_ref": lease_ref if lease_ref is not None else item.lease_ref,
            "result_refs": result_refs if result_refs is not None else item.result_refs,
            "failure_refs": failure_refs if failure_refs is not None else item.failure_refs,
            "last_error_ref": last_error_ref if last_error_ref is not None else item.last_error_ref,
            "attempt_count": attempt_count if attempt_count is not None else item.attempt_count,
        }
    )
    store.save_frontier_item(updated)
    return updated


def mark_queue_lease_status(
    store: DeterministicDurableStore,
    lease: QueueLease,
    *,
    status: QueueLeaseStatus,
    heartbeat_ref: Ref | None = None,
    completed_at_ref: Ref | None = None,
    released_at_ref: Ref | None = None,
    expiry_reason_ref: Ref | None = None,
    replaced_by_lease_ref: Ref | None = None,
) -> QueueLease:
    updated = lease.model_copy(
        update={
            "status": status,
            "heartbeat_ref": heartbeat_ref if heartbeat_ref is not None else lease.heartbeat_ref,
            "completed_at_ref": completed_at_ref
            if completed_at_ref is not None
            else lease.completed_at_ref,
            "released_at_ref": released_at_ref
            if released_at_ref is not None
            else lease.released_at_ref,
            "expiry_reason_ref": expiry_reason_ref
            if expiry_reason_ref is not None
            else lease.expiry_reason_ref,
            "replaced_by_lease_ref": replaced_by_lease_ref
            if replaced_by_lease_ref is not None
            else lease.replaced_by_lease_ref,
        }
    )
    store.save_queue_lease(updated)
    return updated
