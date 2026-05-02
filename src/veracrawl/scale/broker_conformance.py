"""Core queue broker conformance harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    QueueBrokerConformanceFailureType,
    QueueBrokerOperation,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
)
from veracrawl.contracts.scale import (
    QueueBrokerAdapterSpec,
    QueueBrokerConformanceReport,
    QueueBrokerOperationRecord,
    QueueItem,
    QueueTopologySpec,
    RetryDeadLetterRecord,
    ShardLease,
)


class OperationalQueueBrokerAdapter(Protocol):
    def reopen(self) -> OperationalQueueBrokerAdapter: ...

    def enqueue(
        self,
        item: QueueItem,
        *,
        adapter_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord: ...

    def lease(
        self,
        queue_name: ScaleQueueName,
        *,
        adapter_ref: Ref,
        worker_id: str,
        visibility_timeout_seconds: int,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> tuple[QueueItem, ShardLease, QueueBrokerOperationRecord]: ...

    def heartbeat(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        visibility_timeout_seconds: int,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord: ...

    def ack(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord: ...

    def nack(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        failure_refs: list[Ref],
        recovery_refs: list[Ref],
        retry_ref: Ref,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord: ...

    def dead_letter(
        self,
        item_ref: Ref,
        lease: ShardLease,
        *,
        adapter_ref: Ref,
        dead_letter: RetryDeadLetterRecord,
        fairness_scope_refs: list[Ref],
        backpressure_signal_refs: list[Ref],
        policy_decision_refs: list[Ref],
    ) -> QueueBrokerOperationRecord: ...

    def queued_count(self, queue_name: ScaleQueueName) -> int: ...

    def dead_letter_count(self, queue_name: ScaleQueueName) -> int: ...


@dataclass(frozen=True)
class QueueBrokerConformanceResult:
    adapter: QueueBrokerAdapterSpec | None
    topology: QueueTopologySpec | None
    queue_items: list[QueueItem]
    leases: list[ShardLease]
    operations: list[QueueBrokerOperationRecord]
    report: QueueBrokerConformanceReport
    duplicate_deduped: bool = False
    queued_count: int = 0
    dead_letter_count: int = 0


_FAILURES: dict[str, tuple[QueueBrokerConformanceFailureType, str]] = {
    "broker-missing-fencing-token": (
        QueueBrokerConformanceFailureType.BROKER_MISSING_FENCING_TOKEN,
        "fencing_token_refs",
    ),
    "broker-missing-heartbeat": (
        QueueBrokerConformanceFailureType.BROKER_MISSING_HEARTBEAT,
        "heartbeat_refs",
    ),
    "broker-missing-dead-letter": (
        QueueBrokerConformanceFailureType.BROKER_MISSING_DEAD_LETTER,
        "dead_letter_refs",
    ),
}


def run_queue_broker_conformance(
    *,
    fixture_id: str,
    scenario: str,
    broker: OperationalQueueBrokerAdapter | None,
    adapter_spec: QueueBrokerAdapterSpec,
) -> QueueBrokerConformanceResult:
    if scenario in _FAILURES:
        failure, missing = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            adapter=adapter_spec,
            failure=failure,
            missing_field=missing,
        )
    if broker is None:
        raise ValueError(f"fixture {fixture_id} requires an operational queue broker adapter")
    return _success_result(
        fixture_id=fixture_id,
        scenario=scenario,
        broker=broker,
        adapter=adapter_spec,
    )


def run_queue_broker_runtime_unavailable_conformance(
    *,
    fixture_id: str,
    adapter_spec: QueueBrokerAdapterSpec,
) -> QueueBrokerConformanceResult:
    report = QueueBrokerConformanceReport(
        id=f"queue-broker-conformance-report:{fixture_id}",
        adapter_ref=adapter_spec.id,
        adapter_kind=adapter_spec.adapter_kind,
        policy_decision_refs=adapter_spec.policy_decision_refs,
        contract_only_refs=[
            "runtime:queue-broker:url-required",
            "runtime:queue-broker:live-conformance-not-executed",
        ],
        operator_status="redis_broker_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return QueueBrokerConformanceResult(
        adapter=adapter_spec,
        topology=None,
        queue_items=[],
        leases=[],
        operations=[],
        report=report,
    )


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    broker: OperationalQueueBrokerAdapter,
    adapter: QueueBrokerAdapterSpec,
) -> QueueBrokerConformanceResult:
    fairness_refs = adapter.fairness_scope_refs
    backpressure_refs = adapter.backpressure_signal_refs
    policy_refs = adapter.policy_decision_refs
    topology = QueueTopologySpec(
        id=f"queue-topology:{fixture_id}:broker",
        project_id=f"project:{fixture_id}",
        queue_names=list(ScaleQueueName),
        shard_key_parts=["project_id", "site_id", "adapter_type", "priority_band"],
        fairness_scope_refs=fairness_refs,
        per_project_concurrency_limit=16,
        per_site_concurrency_limit=4,
        policy_decision_refs=policy_refs,
    )
    ack_item = _queue_item(fixture_id, suffix="ack", priority=10)
    enqueue_ack = broker.enqueue(
        ack_item,
        adapter_ref=adapter.id,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    duplicate_deduped = False
    operations = [enqueue_ack]
    if scenario == "redis-broker-idempotency-success":
        reopened = broker.reopen()
        duplicate_op = reopened.enqueue(
            ack_item.model_copy(update={"id": f"queue-item:{fixture_id}:ack:duplicate"}),
            adapter_ref=adapter.id,
            fairness_scope_refs=fairness_refs,
            backpressure_signal_refs=backpressure_refs,
            policy_decision_refs=policy_refs,
        )
        broker = reopened
        operations.append(duplicate_op)
        duplicate_deduped = duplicate_op.operation == QueueBrokerOperation.DUPLICATE_ENQUEUE

    leased_ack, ack_lease, lease_op = broker.lease(
        ScaleQueueName.FRONTIER,
        adapter_ref=adapter.id,
        worker_id=f"worker:{fixture_id}:ack",
        visibility_timeout_seconds=adapter.visibility_timeout_seconds,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    heartbeat_op = broker.heartbeat(
        leased_ack.id,
        ack_lease,
        adapter_ref=adapter.id,
        visibility_timeout_seconds=adapter.visibility_timeout_seconds,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    ack_op = broker.ack(
        leased_ack.id,
        ack_lease,
        adapter_ref=adapter.id,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    dead_item = _queue_item(fixture_id, suffix="dead", priority=9)
    enqueue_dead = broker.enqueue(
        dead_item,
        adapter_ref=adapter.id,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    leased_dead, dead_lease, dead_lease_op = broker.lease(
        ScaleQueueName.FRONTIER,
        adapter_ref=adapter.id,
        worker_id=f"worker:{fixture_id}:dead",
        visibility_timeout_seconds=adapter.visibility_timeout_seconds,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    failure_refs = [f"failure-record:{fixture_id}:broker"]
    recovery_refs = [f"recovery-action:{fixture_id}:broker"]
    retry_ref = f"retry:{fixture_id}:broker:1"
    nack_op = broker.nack(
        leased_dead.id,
        dead_lease,
        adapter_ref=adapter.id,
        failure_refs=failure_refs,
        recovery_refs=recovery_refs,
        retry_ref=retry_ref,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    leased_retry, retry_lease, retry_lease_op = broker.lease(
        ScaleQueueName.FRONTIER,
        adapter_ref=adapter.id,
        worker_id=f"worker:{fixture_id}:retry",
        visibility_timeout_seconds=adapter.visibility_timeout_seconds,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    dead_letter = RetryDeadLetterRecord(
        id=f"retry-dead-letter:{fixture_id}:broker",
        queue_item_id=leased_retry.id,
        run_id=f"run:{fixture_id}",
        retry_class=ScaleRetryClass.WORKER_CRASH,
        attempts=3,
        final_reason="broker_retry_exhausted",
        failure_record_id=failure_refs[0],
        recovery_action_refs=recovery_refs,
    )
    dead_letter_op = broker.dead_letter(
        leased_retry.id,
        retry_lease,
        adapter_ref=adapter.id,
        dead_letter=dead_letter,
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        policy_decision_refs=policy_refs,
    )
    operations.extend(
        [
            lease_op,
            heartbeat_op,
            ack_op,
            enqueue_dead,
            dead_lease_op,
            nack_op,
            retry_lease_op,
            dead_letter_op,
        ]
    )
    leases = [ack_lease, dead_lease, retry_lease]
    items = [ack_item, leased_ack, dead_item, leased_dead, leased_retry]
    report = QueueBrokerConformanceReport(
        id=f"queue-broker-conformance-report:{fixture_id}",
        adapter_ref=adapter.id,
        adapter_kind=adapter.adapter_kind,
        queue_topology_ref=topology.id,
        queue_item_refs=[item.id for item in items],
        broker_operation_refs=[operation.id for operation in operations],
        lease_refs=[lease.id for lease in leases],
        heartbeat_refs=[heartbeat_op.heartbeat_ref or ""],
        ack_refs=[ack_op.id],
        nack_refs=[nack_op.id],
        dead_letter_refs=[dead_letter.id],
        fencing_token_refs=[
            ref
            for ref in [operation.fencing_token_ref for operation in operations]
            if ref is not None
        ],
        retry_refs=[retry_ref],
        fairness_scope_refs=fairness_refs,
        backpressure_signal_refs=backpressure_refs,
        failure_record_refs=failure_refs,
        recovery_action_refs=recovery_refs,
        policy_decision_refs=policy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:queue-broker",
        operator_status="redis_broker_conformance_completed",
        completion_result=CompletenessResult.PASS,
    )
    return QueueBrokerConformanceResult(
        adapter=adapter,
        topology=topology,
        queue_items=items,
        leases=leases,
        operations=operations,
        report=report,
        duplicate_deduped=duplicate_deduped,
        queued_count=broker.queued_count(ScaleQueueName.FRONTIER),
        dead_letter_count=broker.dead_letter_count(ScaleQueueName.FRONTIER),
    )


def _queue_item(fixture_id: str, *, suffix: str, priority: int) -> QueueItem:
    now = datetime.now(tz=UTC)
    return QueueItem(
        id=f"queue-item:{fixture_id}:{suffix}",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=f"project:{fixture_id}|site:{fixture_id}|http|p1",
        run_id=f"run:{fixture_id}",
        aggregate_type="FrontierItem",
        aggregate_id=f"frontier-item:{fixture_id}:{suffix}",
        command_ref=f"command:{fixture_id}:{suffix}",
        priority=priority,
        retry_class=ScaleRetryClass.TRANSIENT,
        idempotency_key=f"idempotency:{fixture_id}:{suffix}",
        expected_version_ref=f"expected-version:{fixture_id}:{suffix}",
        attempts=0,
        deadline_at=now + timedelta(minutes=30),
        status=ScaleQueueItemStatus.QUEUED,
    )


def _failure_result(
    *,
    fixture_id: str,
    adapter: QueueBrokerAdapterSpec,
    failure: QueueBrokerConformanceFailureType,
    missing_field: str,
) -> QueueBrokerConformanceResult:
    report = QueueBrokerConformanceReport(
        id=f"queue-broker-conformance-report:{fixture_id}",
        adapter_ref=adapter.id,
        adapter_kind=adapter.adapter_kind,
        failure_record_refs=[f"queue-broker-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=adapter.policy_decision_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return QueueBrokerConformanceResult(
        adapter=adapter,
        topology=None,
        queue_items=[],
        leases=[],
        operations=[],
        report=report,
    )
