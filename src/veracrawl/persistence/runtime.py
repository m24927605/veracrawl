"""Production-facing persistence and queue runtime spine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import DurableCommandRecord, OutboxRecord
from veracrawl.contracts.enums import (
    CompletenessResult,
    PersistenceAdapterKind,
    PersistenceCapability,
    PersistenceFailureType,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
)
from veracrawl.contracts.persistence import (
    IdempotencyPersistenceRecord,
    PersistenceAdapterSpec,
    PersistenceRuntimeReport,
    PersistenceTransactionRecord,
    PersistentQueueOperationRecord,
)
from veracrawl.contracts.scale import QueueItem, RetryDeadLetterRecord, ShardLease
from veracrawl.control.runtime import create_runtime_command
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


@dataclass(frozen=True)
class PersistenceRuntimeResult:
    adapter: PersistenceAdapterSpec | None
    transaction: PersistenceTransactionRecord | None
    command_records: list[DurableCommandRecord]
    idempotency_records: list[IdempotencyPersistenceRecord]
    outbox_records: list[OutboxRecord]
    queue_operations: list[PersistentQueueOperationRecord]
    report: PersistenceRuntimeReport
    duplicate_deduped: bool = False
    event_count: int = 0
    outbox_count: int = 0
    reloaded: bool = False


def run_persistence_queue_runtime(
    *,
    fixture_id: str,
    scenario: str,
    root: Path,
    policy_decision_refs: list[Ref] | None = None,
) -> PersistenceRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:persistence"]
    failures = {
        "non-atomic-commit": (
            PersistenceFailureType.NON_ATOMIC_COMMIT,
            "transaction_ref",
        ),
        "idempotency-not-persisted": (
            PersistenceFailureType.IDEMPOTENCY_NOT_PERSISTED,
            "idempotency_record_refs",
        ),
        "event-log-gap": (
            PersistenceFailureType.EVENT_LOG_GAP,
            "event_cursor_ref",
        ),
        "outbox-dispatch-missing": (
            PersistenceFailureType.OUTBOX_DISPATCH_MISSING,
            "outbox_refs",
        ),
        "artifact-index-missing": (
            PersistenceFailureType.ARTIFACT_INDEX_MISSING,
            "artifact_refs",
        ),
        "lease-heartbeat-missing": (
            PersistenceFailureType.LEASE_HEARTBEAT_MISSING,
            "queue_operation_refs",
        ),
    }
    if scenario in failures:
        failure, missing = failures[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing,
            policy_refs=policy_refs,
        )
    return _success_result(
        fixture_id=fixture_id,
        scenario=scenario,
        root=root,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    root: Path,
    policy_refs: list[Ref],
) -> PersistenceRuntimeResult:
    store = ReferencePersistenceStore(root)
    adapter = _adapter(fixture_id, policy_refs)
    transaction = store.begin_transaction(
        run_ref=f"run:{fixture_id}",
        unit_of_work_ref=f"uow:{fixture_id}:persistence",
        adapter_ref=adapter.id,
    )
    artifact_ref = f"artifact:{fixture_id}:raw"
    store.register_artifact_ref(artifact_ref)
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:persist",
        command_type="durable_commit_command",
        target_aggregate_type="PersistenceFixture",
        target_aggregate_id=f"fixture:{fixture_id}",
        payload_ref=f"payload:{fixture_id}:persist",
        policy_decision_refs=policy_refs,
    )
    command_record, command_result, outbox, idempotency, duplicate = store.handle_command_once(
        command,
        run_ref=f"run:{fixture_id}",
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        event_type="persistence_runtime_reported",
        output_refs=[artifact_ref],
    )
    idempotency_records = [idempotency]
    command_records = [command_record]
    reloaded = False
    if scenario == "idempotent-replay-success":
        reopened = store.reopen()
        duplicate_record, _, _, duplicate_idempotency, duplicate = reopened.handle_command_once(
            command.model_copy(update={"id": f"cmd:{fixture_id}:persist:retry"}),
            run_ref=f"run:{fixture_id}",
            objective_ref=f"objective:{fixture_id}",
            plan_ref=f"plan:{fixture_id}",
            event_type="persistence_runtime_reported",
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
        include_dead_letter=scenario == "queue-lease-recovery-success",
    )
    cursor = store.build_event_cursor(f"run:{fixture_id}")
    transaction = transaction.model_copy(
        update={
            "command_record_refs": [record.id for record in command_records],
            "event_refs": cursor.event_refs,
            "outbox_refs": [dispatched.id],
            "artifact_refs": [artifact_ref],
            "idempotency_record_refs": [record.id for record in idempotency_records],
            "queue_operation_refs": [operation.id for operation in queue_operations],
            "policy_decision_refs": policy_refs,
        }
    )
    transaction = PersistenceTransactionRecord.model_validate(
        transaction.model_dump(mode="json")
    )
    committed = store.commit_transaction(transaction)
    report = PersistenceRuntimeReport(
        id=f"persistence-runtime-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        adapter_ref=adapter.id,
        transaction_ref=committed.id,
        command_record_refs=[record.id for record in command_records],
        idempotency_record_refs=[record.id for record in idempotency_records],
        event_cursor_ref=cursor.id,
        outbox_refs=[dispatched.id],
        artifact_refs=[artifact_ref],
        queue_operation_refs=[operation.id for operation in queue_operations],
        lease_refs=lease_refs,
        failure_record_refs=[f"failure-record:{fixture_id}:queue"] if lease_refs else [],
        recovery_action_refs=[f"recovery-action:{fixture_id}:queue"] if lease_refs else [],
        policy_decision_refs=policy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:persistence",
        operator_status="persistence_queue_runtime_completed",
        completion_result=CompletenessResult.PASS,
    )
    return PersistenceRuntimeResult(
        adapter=adapter,
        transaction=committed,
        command_records=command_records,
        idempotency_records=idempotency_records,
        outbox_records=[dispatched],
        queue_operations=queue_operations,
        report=report,
        duplicate_deduped=duplicate,
        event_count=len(store.stream_events(f"run:{fixture_id}")),
        outbox_count=len(store.list_outbox(f"run:{fixture_id}")),
        reloaded=reloaded,
    )


def _adapter(fixture_id: str, policy_refs: list[Ref]) -> PersistenceAdapterSpec:
    return PersistenceAdapterSpec(
        id=f"persistence-adapter:{fixture_id}:reference-filesystem",
        adapter_kind=PersistenceAdapterKind.REFERENCE_FILESYSTEM,
        capability_refs=list(PersistenceCapability),
        port_refs=[
            "port:metadata-persistence",
            "port:event-log-persistence",
            "port:outbox-persistence",
            "port:artifact-index-persistence",
            "port:queue-persistence",
        ],
        transaction_supported=True,
        idempotency_supported=True,
        lease_supported=True,
        policy_decision_refs=policy_refs,
    )


def _queue_operations(
    store: ReferencePersistenceStore,
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
    failure: PersistenceFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> PersistenceRuntimeResult:
    report = PersistenceRuntimeReport(
        id=f"persistence-runtime-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        failure_record_refs=[f"persistence-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=policy_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return PersistenceRuntimeResult(
        adapter=None,
        transaction=None,
        command_records=[],
        idempotency_records=[],
        outbox_records=[],
        queue_operations=[],
        report=report,
    )
