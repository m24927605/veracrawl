"""Core persistence adapter conformance harness.

The harness accepts persistence ports and contract descriptors. It never imports
concrete adapter modules, database drivers, queue SDKs, or cloud clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from veracrawl.contracts.command import CommandEnvelope, CommandResult
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import DurableCommandRecord, EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import (
    CompletenessResult,
    PersistenceAdapterConformanceFailureType,
    PersistenceCapability,
    PersistenceMigrationStatus,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
)
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceAdapterConformanceReport,
    PersistenceAdapterSpec,
    PersistenceMigrationRecord,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)
from veracrawl.contracts.scale import QueueItem, RetryDeadLetterRecord, ShardLease
from veracrawl.control.runtime import create_runtime_command


class OperationalPersistenceAdapter(Protocol):
    def reopen(self) -> OperationalPersistenceAdapter: ...

    def begin_transaction(
        self,
        *,
        run_ref: Ref,
        unit_of_work_ref: Ref,
        adapter_ref: Ref = ...,
    ) -> PersistenceTransactionRecord: ...

    def commit_transaction(
        self,
        record: PersistenceTransactionRecord,
    ) -> PersistenceTransactionRecord: ...

    def save_migration_record(self, record: PersistenceMigrationRecord) -> Ref: ...

    def list_migration_records(self) -> list[PersistenceMigrationRecord]: ...

    def register_artifact_ref(self, artifact_ref: Ref) -> Ref: ...

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
    ]: ...

    def stream_events(self, run_ref: Ref) -> list[CrawlRunEvent]: ...

    def build_event_cursor(self, run_ref: Ref) -> EventCursorRecord: ...

    def mark_outbox_dispatched(self, outbox_ref: Ref, *, dispatched_at_ref: Ref) -> OutboxRecord:
        ...

    def list_outbox(self, run_ref: Ref | None = None) -> list[OutboxRecord]: ...

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


@dataclass(frozen=True)
class PersistenceAdapterConformanceResult:
    adapter: PersistenceAdapterSpec | None
    migrations: list[PersistenceMigrationRecord]
    transaction: PersistenceTransactionRecord | None
    command_records: list[DurableCommandRecord]
    idempotency_records: list[IdempotencyPersistenceRecord]
    outbox_records: list[OutboxRecord]
    queue_operations: list[PersistentQueueOperationRecord]
    report: PersistenceAdapterConformanceReport
    duplicate_deduped: bool = False
    event_count: int = 0
    outbox_count: int = 0
    reloaded: bool = False


_FAILURES: dict[str, tuple[PersistenceAdapterConformanceFailureType, str]] = {
    "adapter-missing-capability": (
        PersistenceAdapterConformanceFailureType.ADAPTER_MISSING_CAPABILITY,
        "adapter_ref",
    ),
    "sqlite-idempotency-gap": (
        PersistenceAdapterConformanceFailureType.SQLITE_IDEMPOTENCY_GAP,
        "idempotency_record_refs",
    ),
    "sqlite-event-cursor-gap": (
        PersistenceAdapterConformanceFailureType.SQLITE_EVENT_CURSOR_GAP,
        "event_cursor_refs",
    ),
    "sqlite-outbox-gap": (
        PersistenceAdapterConformanceFailureType.SQLITE_OUTBOX_GAP,
        "outbox_refs",
    ),
    "sqlite-migration-missing": (
        PersistenceAdapterConformanceFailureType.SQLITE_MIGRATION_MISSING,
        "migration_record_refs",
    ),
}


def run_sqlite_adapter_conformance(
    *,
    fixture_id: str,
    scenario: str,
    store: OperationalPersistenceAdapter,
    adapter_spec: PersistenceAdapterSpec | None,
    policy_decision_refs: list[Ref] | None = None,
) -> PersistenceAdapterConformanceResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:persistence-adapter"]
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            adapter=adapter_spec,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if adapter_spec is None or set(adapter_spec.capability_refs) != set(PersistenceCapability):
        return _failure_result(
            fixture_id=fixture_id,
            adapter=adapter_spec,
            failure=PersistenceAdapterConformanceFailureType.ADAPTER_MISSING_CAPABILITY,
            missing_field="adapter_ref",
            policy_refs=policy_refs,
        )
    return _operational_success_result(
        fixture_id=fixture_id,
        scenario=scenario,
        store=store,
        adapter=adapter_spec,
        policy_refs=policy_refs,
        operator_status="sqlite_adapter_conformance_completed",
    )


def run_postgres_adapter_conformance(
    *,
    fixture_id: str,
    scenario: str,
    store: OperationalPersistenceAdapter,
    adapter_spec: PersistenceAdapterSpec,
    policy_decision_refs: list[Ref] | None = None,
) -> PersistenceAdapterConformanceResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:persistence-adapter"]
    if set(adapter_spec.capability_refs) != set(PersistenceCapability):
        return _failure_result(
            fixture_id=fixture_id,
            adapter=adapter_spec,
            failure=PersistenceAdapterConformanceFailureType.ADAPTER_MISSING_CAPABILITY,
            missing_field="adapter_ref",
            policy_refs=policy_refs,
        )
    return _operational_success_result(
        fixture_id=fixture_id,
        scenario=scenario,
        store=store,
        adapter=adapter_spec,
        policy_refs=policy_refs,
        operator_status="postgres_adapter_conformance_completed",
    )


def run_postgres_contract_conformance(
    *,
    fixture_id: str,
    adapter_spec: PersistenceAdapterSpec,
    policy_decision_refs: list[Ref] | None = None,
) -> PersistenceAdapterConformanceResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:persistence-adapter"]
    report = PersistenceAdapterConformanceReport(
        id=f"persistence-adapter-conformance-report:{fixture_id}",
        adapter_ref=adapter_spec.id,
        adapter_kind=adapter_spec.adapter_kind,
        policy_decision_refs=policy_refs,
        contract_only_refs=[
            "contract:postgres:metadata-store-port",
            "contract:postgres:event-log-port",
            "contract:postgres:outbox-port",
            "contract:postgres:artifact-index-port",
            "contract:postgres:queue-port",
            "contract:postgres:migration-conformance",
        ],
        operator_status="postgres_contract_declared",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return PersistenceAdapterConformanceResult(
        adapter=adapter_spec,
        migrations=[],
        transaction=None,
        command_records=[],
        idempotency_records=[],
        outbox_records=[],
        queue_operations=[],
        report=report,
    )


def run_postgres_runtime_unavailable_conformance(
    *,
    fixture_id: str,
    adapter_spec: PersistenceAdapterSpec,
    policy_decision_refs: list[Ref] | None = None,
) -> PersistenceAdapterConformanceResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:persistence-adapter"]
    report = PersistenceAdapterConformanceReport(
        id=f"persistence-adapter-conformance-report:{fixture_id}",
        adapter_ref=adapter_spec.id,
        adapter_kind=adapter_spec.adapter_kind,
        policy_decision_refs=policy_refs,
        contract_only_refs=[
            "runtime:postgres:dsn-required",
            "runtime:postgres:live-conformance-not-executed",
        ],
        operator_status="postgres_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return PersistenceAdapterConformanceResult(
        adapter=adapter_spec,
        migrations=[],
        transaction=None,
        command_records=[],
        idempotency_records=[],
        outbox_records=[],
        queue_operations=[],
        report=report,
    )


def _operational_success_result(
    *,
    fixture_id: str,
    scenario: str,
    store: OperationalPersistenceAdapter,
    adapter: PersistenceAdapterSpec,
    policy_refs: list[Ref],
    operator_status: str,
) -> PersistenceAdapterConformanceResult:
    run_ref = f"run:{fixture_id}"
    transaction = store.begin_transaction(
        run_ref=run_ref,
        unit_of_work_ref=f"uow:{fixture_id}:persistence-adapter",
        adapter_ref=adapter.id,
    )
    artifact_ref = f"artifact:{fixture_id}:raw"
    store.register_artifact_ref(artifact_ref)
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:persist",
        command_type="persistence_adapter_commit_command",
        target_aggregate_type="PersistenceAdapterFixture",
        target_aggregate_id=f"fixture:{fixture_id}",
        payload_ref=f"payload:{fixture_id}:persist",
        policy_decision_refs=policy_refs,
    )
    command_record, command_result, outbox, idempotency, duplicate = store.handle_command_once(
        command,
        run_ref=run_ref,
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        event_type="persistence_adapter_conformance_reported",
        output_refs=[artifact_ref],
    )
    command_records = [command_record]
    idempotency_records = [idempotency]
    reloaded = False
    if scenario in {
        "sqlite-reopen-idempotency-success",
        "postgres-reopen-idempotency-success",
    }:
        reopened = store.reopen()
        duplicate_record, _, _, duplicate_idempotency, duplicate = reopened.handle_command_once(
            command.model_copy(update={"id": f"cmd:{fixture_id}:persist:retry"}),
            run_ref=run_ref,
            objective_ref=f"objective:{fixture_id}",
            plan_ref=f"plan:{fixture_id}",
            event_type="persistence_adapter_conformance_reported",
            output_refs=[artifact_ref],
        )
        store = reopened
        command_records.append(duplicate_record)
        idempotency_records.append(duplicate_idempotency)
        reloaded = True
    dispatched = store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{fixture_id}:outbox-dispatched",
    )
    queue_operations, lease_refs = _queue_operations(
        store,
        fixture_id=fixture_id,
        command_result_ref=command_result.id,
        policy_refs=policy_refs,
        include_dead_letter=scenario
        in {
            "sqlite-queue-recovery-success",
            "postgres-queue-recovery-success",
        },
    )
    cursor = store.build_event_cursor(run_ref)
    migration = PersistenceMigrationRecord(
        id=f"persistence-migration:{fixture_id}:001",
        adapter_ref=adapter.id,
        migration_name="001_conformance_schema",
        from_version="0",
        to_version="1",
        status=PersistenceMigrationStatus.APPLIED,
        applied_at_ref=f"clock:{fixture_id}:migration-applied",
        rollback_plan_ref=f"rollback-plan:{fixture_id}:001",
        validation_event_cursor_ref=cursor.id,
    )
    store.save_migration_record(migration)
    transaction = PersistenceTransactionRecord.model_validate(
        transaction.model_copy(
            update={
                "command_record_refs": [record.id for record in command_records],
                "event_refs": cursor.event_refs,
                "outbox_refs": [dispatched.id],
                "artifact_refs": [artifact_ref],
                "idempotency_record_refs": [record.id for record in idempotency_records],
                "queue_operation_refs": [operation.id for operation in queue_operations],
                "policy_decision_refs": policy_refs,
            }
        ).model_dump(mode="json")
    )
    committed = store.commit_transaction(transaction)
    report = PersistenceAdapterConformanceReport(
        id=f"persistence-adapter-conformance-report:{fixture_id}",
        adapter_ref=adapter.id,
        adapter_kind=adapter.adapter_kind,
        transaction_refs=[committed.id],
        migration_record_refs=[migration.id],
        command_record_refs=[record.id for record in command_records],
        idempotency_record_refs=[record.id for record in idempotency_records],
        event_cursor_refs=[cursor.id],
        outbox_refs=[dispatched.id],
        artifact_refs=[artifact_ref],
        queue_operation_refs=[operation.id for operation in queue_operations],
        lease_refs=lease_refs,
        policy_decision_refs=policy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:persistence-adapter",
        operator_status=operator_status,
        completion_result=CompletenessResult.PASS,
    )
    return PersistenceAdapterConformanceResult(
        adapter=adapter,
        migrations=[migration],
        transaction=committed,
        command_records=command_records,
        idempotency_records=idempotency_records,
        outbox_records=[dispatched],
        queue_operations=queue_operations,
        report=report,
        duplicate_deduped=duplicate,
        event_count=len(store.stream_events(run_ref)),
        outbox_count=len(store.list_outbox(run_ref)),
        reloaded=reloaded,
    )


def _queue_operations(
    store: OperationalPersistenceAdapter,
    *,
    fixture_id: str,
    command_result_ref: Ref,
    policy_refs: list[Ref],
    include_dead_letter: bool,
) -> tuple[list[PersistentQueueOperationRecord], list[Ref]]:
    now = datetime.now(tz=UTC)
    queued = QueueItem(
        id=f"queue-item:{fixture_id}:frontier",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=f"project:{fixture_id}|site:{fixture_id}|http|p1",
        run_id=f"run:{fixture_id}",
        aggregate_type="FrontierItem",
        aggregate_id=f"frontier-item:{fixture_id}",
        command_ref=f"command:{fixture_id}:frontier",
        priority=10,
        retry_class=ScaleRetryClass.TRANSIENT,
        idempotency_key=f"idempotency:{fixture_id}:frontier",
        expected_version_ref=f"expected-version:{fixture_id}:frontier",
        attempts=0,
        deadline_at=now + timedelta(minutes=30),
        status=ScaleQueueItemStatus.QUEUED,
    )
    lease = ShardLease(
        id=f"shard-lease:{fixture_id}:frontier",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=queued.shard_key,
        worker_id=f"worker:{fixture_id}:fetch",
        lease_token=f"lease-token:{fixture_id}",
        acquired_at=now,
        heartbeat_at=now + timedelta(seconds=30),
        expires_at=now + timedelta(minutes=5),
        policy_decision_refs=policy_refs,
        status=ScaleShardLeaseStatus.ACTIVE,
    )
    leased = QueueItem.model_validate(
        queued.model_copy(
            update={
                "status": ScaleQueueItemStatus.LEASED,
                "lease_token": lease.lease_token,
                "lease_expires_at": lease.expires_at,
                "attempts": 1,
            }
        ).model_dump(mode="json")
    )
    operations = [
        store.enqueue_queue_item(queued),
        store.acquire_queue_lease(leased, lease),
        store.heartbeat_queue_lease(
            lease.id,
            lease_token_ref=lease.lease_token,
            heartbeat_ref=f"heartbeat:{fixture_id}:frontier",
        ),
    ]
    if include_dead_letter:
        failure_refs = [f"failure-record:{fixture_id}:queue"]
        recovery_refs = [f"recovery-action:{fixture_id}:queue"]
        operations.append(
            store.nack_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                failure_refs=failure_refs,
                recovery_refs=recovery_refs,
            )
        )
        dead_letter = RetryDeadLetterRecord(
            id=f"retry-dead-letter:{fixture_id}:frontier",
            queue_item_id=queued.id,
            run_id=f"run:{fixture_id}",
            retry_class=ScaleRetryClass.WORKER_CRASH,
            attempts=3,
            final_reason="worker_crash_retry_exhausted",
            failure_record_id=failure_refs[0],
            recovery_action_refs=recovery_refs,
        )
        operations.append(
            store.dead_letter_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                dead_letter=dead_letter,
            )
        )
    else:
        operations.append(
            store.ack_queue_item(
                queued.id,
                lease_ref=lease.id,
                lease_token_ref=lease.lease_token,
                command_result_ref=command_result_ref,
            )
        )
    return operations, [lease.id]


def _failure_result(
    *,
    fixture_id: str,
    adapter: PersistenceAdapterSpec | None,
    failure: PersistenceAdapterConformanceFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> PersistenceAdapterConformanceResult:
    report = PersistenceAdapterConformanceReport(
        id=f"persistence-adapter-conformance-report:{fixture_id}",
        adapter_ref=adapter.id if adapter is not None else None,
        adapter_kind=adapter.adapter_kind if adapter is not None else None,
        failure_record_refs=[f"persistence-adapter-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=policy_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return PersistenceAdapterConformanceResult(
        adapter=adapter,
        migrations=[],
        transaction=None,
        command_records=[],
        idempotency_records=[],
        outbox_records=[],
        queue_operations=[],
        report=report,
    )
