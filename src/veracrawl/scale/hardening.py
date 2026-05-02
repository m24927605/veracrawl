"""Deterministic scale hardening runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    BackpressureSignalType,
    CompletenessResult,
    OpsSeverity,
    ScaleFailureType,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
    WorkerPool,
)
from veracrawl.contracts.scale import (
    AutoscalingDecision,
    BackpressureSignal,
    QueueItem,
    QueueTopologySpec,
    RetryDeadLetterRecord,
    ScaleRecoveryReport,
    ShardLease,
)


@dataclass(frozen=True)
class ScaleHardeningResult:
    topology: QueueTopologySpec | None
    queue_items: list[QueueItem]
    shard_leases: list[ShardLease]
    backpressure_signals: list[BackpressureSignal]
    autoscaling_decisions: list[AutoscalingDecision]
    dead_letter_records: list[RetryDeadLetterRecord]
    report: ScaleRecoveryReport


def run_scale_hardening(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> ScaleHardeningResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:scale"]
    failures = {
        "stale-lease-without-recovery": (
            ScaleFailureType.STALE_LEASE_WITHOUT_RECOVERY,
            "recovery_action_refs",
        ),
        "unfair-site-starvation": (
            ScaleFailureType.UNFAIR_SITE_STARVATION,
            "fairness_scope_refs",
        ),
        "autoscale-without-policy": (
            ScaleFailureType.AUTOSCALE_WITHOUT_POLICY,
            "policy_decision_refs",
        ),
        "dead-letter-missing-failure-record": (
            ScaleFailureType.DEAD_LETTER_MISSING_FAILURE_RECORD,
            "failure_record_refs",
        ),
        "replay-missing-scale-refs": (
            ScaleFailureType.REPLAY_MISSING_SCALE_REFS,
            "queue_topology_ref",
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
    return _success_result(fixture_id=fixture_id, scenario=scenario, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
) -> ScaleHardeningResult:
    topology = _topology(fixture_id, policy_refs)
    item = _queue_item(fixture_id, status=ScaleQueueItemStatus.LEASED)
    lease = _lease(fixture_id, item.shard_key, policy_refs)
    signal_type = (
        BackpressureSignalType.EXPORT_LAG
        if scenario == "backpressure-autoscale-success"
        else BackpressureSignalType.QUEUE_LAG
    )
    signal = _backpressure_signal(fixture_id, signal_type, policy_refs)
    decision = _autoscaling_decision(fixture_id, signal.id, policy_refs)
    dead_letter = _dead_letter(fixture_id)
    report = ScaleRecoveryReport(
        id=f"scale-recovery-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        queue_topology_ref=topology.id,
        queue_item_refs=[item.id],
        shard_lease_refs=[lease.id],
        backpressure_signal_refs=[signal.id],
        autoscaling_decision_refs=[decision.id],
        dead_letter_record_refs=[dead_letter.id],
        failure_record_refs=[f"failure-record:{fixture_id}:dead-letter"],
        recovery_action_refs=[f"recovery-action:{fixture_id}:retry"],
        dr_restore_report_refs=[f"dr-restore-report:{fixture_id}:scale"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:scale"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:scale"],
        outbox_refs=[f"outbox:{fixture_id}:scale"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}",
        operator_status="scale_hardening_completed",
        completion_result=CompletenessResult.PASS,
    )
    return ScaleHardeningResult(
        topology=topology,
        queue_items=[item],
        shard_leases=[lease],
        backpressure_signals=[signal],
        autoscaling_decisions=[decision],
        dead_letter_records=[dead_letter],
        report=report,
    )


def _topology(fixture_id: str, policy_refs: list[Ref]) -> QueueTopologySpec:
    return QueueTopologySpec(
        id=f"queue-topology:{fixture_id}",
        project_id=f"project:{fixture_id}",
        queue_names=list(ScaleQueueName),
        shard_key_parts=["project_id", "site_id", "adapter_type", "priority_band"],
        fairness_scope_refs=[
            f"fairness-scope:{fixture_id}:project",
            f"fairness-scope:{fixture_id}:site",
        ],
        per_project_concurrency_limit=12,
        per_site_concurrency_limit=3,
        policy_decision_refs=policy_refs,
    )


def _queue_item(fixture_id: str, *, status: ScaleQueueItemStatus) -> QueueItem:
    now = datetime.now(tz=UTC)
    return QueueItem(
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
        lease_token=f"lease-token:{fixture_id}",
        lease_expires_at=now + timedelta(minutes=5),
        attempts=1,
        deadline_at=now + timedelta(minutes=30),
        status=status,
    )


def _lease(fixture_id: str, shard_key: str, policy_refs: list[Ref]) -> ShardLease:
    now = datetime.now(tz=UTC)
    return ShardLease(
        id=f"shard-lease:{fixture_id}:frontier",
        queue_name=ScaleQueueName.FRONTIER,
        shard_key=shard_key,
        worker_id=f"worker:{fixture_id}:fetch",
        lease_token=f"lease-token:{fixture_id}",
        acquired_at=now,
        heartbeat_at=now + timedelta(seconds=30),
        expires_at=now + timedelta(minutes=5),
        policy_decision_refs=policy_refs,
        status=ScaleShardLeaseStatus.ACTIVE,
    )


def _backpressure_signal(
    fixture_id: str,
    signal_type: BackpressureSignalType,
    policy_refs: list[Ref],
) -> BackpressureSignal:
    return BackpressureSignal(
        id=f"backpressure-signal:{fixture_id}:{signal_type.value}",
        project_id=f"project:{fixture_id}",
        site_id=f"site:{fixture_id}",
        signal_type=signal_type,
        value=120.0,
        threshold=60.0,
        severity=OpsSeverity.HIGH,
        policy_decision_refs=policy_refs,
    )


def _autoscaling_decision(
    fixture_id: str,
    signal_ref: Ref,
    policy_refs: list[Ref],
) -> AutoscalingDecision:
    return AutoscalingDecision(
        id=f"autoscaling-decision:{fixture_id}:fetch",
        worker_pool=WorkerPool.FETCH,
        reason_signal_refs=[signal_ref],
        from_capacity=2,
        to_capacity=4,
        cooldown_seconds=300,
        policy_decision_refs=policy_refs,
    )


def _dead_letter(fixture_id: str) -> RetryDeadLetterRecord:
    return RetryDeadLetterRecord(
        id=f"retry-dead-letter:{fixture_id}:frontier",
        queue_item_id=f"queue-item:{fixture_id}:frontier",
        run_id=f"run:{fixture_id}",
        retry_class=ScaleRetryClass.WORKER_CRASH,
        attempts=3,
        final_reason="worker_crash_retry_exhausted",
        failure_record_id=f"failure-record:{fixture_id}:dead-letter",
        recovery_action_refs=[f"recovery-action:{fixture_id}:retry"],
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: ScaleFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> ScaleHardeningResult:
    report = ScaleRecoveryReport(
        id=f"scale-recovery-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        failure_record_refs=[f"scale-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:scale"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:scale"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return ScaleHardeningResult(
        topology=None,
        queue_items=[],
        shard_leases=[],
        backpressure_signals=[],
        autoscaling_decisions=[],
        dead_letter_records=[],
        report=report,
    )
