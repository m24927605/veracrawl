"""Deterministic production worker orchestration runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    ScaleQueueName,
    WorkerOrchestrationFailureType,
    WorkerPool,
)
from veracrawl.contracts.scale import WorkerOrchestrationRuntimeReport
from veracrawl.scale.hardening import ScaleHardeningResult, run_scale_hardening


@dataclass(frozen=True)
class WorkerOrchestrationRuntimeResult:
    report: WorkerOrchestrationRuntimeReport
    scale: ScaleHardeningResult | None = None


_FAILURES: dict[str, tuple[WorkerOrchestrationFailureType, str]] = {
    "worker-orchestration-missing-persistence": (
        WorkerOrchestrationFailureType.MISSING_PERSISTENCE,
        "production_persistence_runtime_report_ref",
    ),
    "worker-orchestration-missing-queue-broker": (
        WorkerOrchestrationFailureType.MISSING_QUEUE_BROKER,
        "queue_broker_conformance_report_ref",
    ),
    "worker-orchestration-missing-heartbeat": (
        WorkerOrchestrationFailureType.MISSING_HEARTBEAT,
        "lease_heartbeat_refs",
    ),
    "worker-orchestration-backpressure-without-policy": (
        WorkerOrchestrationFailureType.BACKPRESSURE_WITHOUT_POLICY,
        "policy_decision_refs",
    ),
    "worker-orchestration-replay-mismatch": (
        WorkerOrchestrationFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_worker_orchestration_runtime(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> WorkerOrchestrationRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:worker-orchestration"]
    scale = run_scale_hardening(
        fixture_id=fixture_id,
        scenario=_scale_scenario(scenario),
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:scale"],
    )
    if scenario == "worker-orchestration-stale-lease-unrecovered":
        return _boundary_failure(
            fixture_id=fixture_id,
            failure=WorkerOrchestrationFailureType.STALE_LEASE_UNRECOVERED,
            policy_refs=policy_refs,
            scale=scale,
            unrecovered_stale_lease_refs=[f"shard-lease:{fixture_id}:stale"],
        )
    if scenario == "worker-orchestration-dead-letter-hidden":
        return _boundary_failure(
            fixture_id=fixture_id,
            failure=WorkerOrchestrationFailureType.DEAD_LETTER_HIDDEN,
            policy_refs=policy_refs,
            scale=scale,
            hidden_dead_letter_refs=[f"retry-dead-letter:{fixture_id}:hidden"],
        )
    if scenario == "worker-orchestration-duplicate-pollution":
        return _boundary_failure(
            fixture_id=fixture_id,
            failure=WorkerOrchestrationFailureType.DUPLICATE_POLLUTION,
            policy_refs=policy_refs,
            scale=scale,
            duplicate_pollution_refs=[f"duplicate-output:{fixture_id}:pollution"],
        )
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return WorkerOrchestrationRuntimeResult(
            report=_failure_report(
                fixture_id=fixture_id,
                failure=failure,
                policy_refs=policy_refs,
                missing_ref_fields=[missing_field],
            ),
            scale=scale,
        )
    return WorkerOrchestrationRuntimeResult(
        report=_pass_report(
            fixture_id=fixture_id,
            scenario=scenario,
            policy_refs=policy_refs,
            scale=scale,
        ),
        scale=scale,
    )


def _pass_report(
    *,
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
    scale: ScaleHardeningResult,
) -> WorkerOrchestrationRuntimeReport:
    queue_refs = [f"queue-item:{fixture_id}:{queue.value}" for queue in ScaleQueueName]
    lease_refs = [f"shard-lease:{fixture_id}:{queue.value}" for queue in ScaleQueueName]
    return WorkerOrchestrationRuntimeReport(
        id=f"worker-orchestration-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        production_persistence_runtime_report_ref=(
            f"production-persistence-runtime-report:{fixture_id}"
        ),
        queue_broker_conformance_report_ref=f"queue-broker-conformance-report:{fixture_id}",
        live_http_acquisition_report_ref=f"live-http-acquisition-report:{fixture_id}",
        live_normalization_runtime_report_ref=(
            f"live-normalization-runtime-report:{fixture_id}"
        ),
        live_evidence_verification_runtime_report_ref=(
            f"live-evidence-verification-runtime-report:{fixture_id}"
        ),
        scale_recovery_report_ref=scale.report.id,
        worker_pool_refs=[f"worker-pool:{fixture_id}:{pool.value}" for pool in WorkerPool],
        worker_heartbeat_refs=[
            f"worker-heartbeat:{fixture_id}:{pool.value}" for pool in WorkerPool
        ],
        worker_capacity_refs=[
            f"worker-capacity:{fixture_id}:{pool.value}" for pool in WorkerPool
        ],
        queue_topology_ref=scale.report.queue_topology_ref,
        queue_item_refs=[*queue_refs, *scale.report.queue_item_refs],
        shard_lease_refs=[*lease_refs, *scale.report.shard_lease_refs],
        lease_heartbeat_refs=[
            f"lease-heartbeat:{fixture_id}:{queue.value}" for queue in ScaleQueueName
        ],
        fencing_token_refs=[
            f"fencing-token:{fixture_id}:{queue.value}" for queue in ScaleQueueName
        ],
        visibility_timeout_refs=[
            f"visibility-timeout:{fixture_id}:{queue.value}" for queue in ScaleQueueName
        ],
        fairness_scope_refs=[
            f"fairness-scope:{fixture_id}:project",
            f"fairness-scope:{fixture_id}:site",
        ],
        retry_refs=[f"retry:{fixture_id}:worker-crash", f"retry:{fixture_id}:stale-lease"],
        dead_letter_refs=scale.report.dead_letter_record_refs,
        failure_record_refs=scale.report.failure_record_refs,
        recovery_action_refs=[
            *scale.report.recovery_action_refs,
            f"recovery-action:{fixture_id}:stale-lease",
            f"recovery-action:{fixture_id}:pending-outbox",
        ],
        duplicate_suppression_refs=[
            f"dedupe:{fixture_id}:idempotency-key",
            f"dedupe:{fixture_id}:expected-version",
        ],
        backpressure_signal_refs=scale.report.backpressure_signal_refs,
        autoscaling_decision_refs=scale.report.autoscaling_decision_refs,
        pending_outbox_refs=[
            f"pending-outbox:{fixture_id}:recovered",
            *scale.report.outbox_refs,
        ],
        event_gap_refs=[
            f"event-gap:{fixture_id}:checked",
            *scale.report.event_cursor_refs,
        ],
        policy_decision_refs=[
            *policy_refs,
            *scale.report.policy_decision_refs,
            f"policy:{fixture_id}:fairness",
            f"policy:{fixture_id}:autoscaling",
        ],
        command_record_refs=[
            f"command-record:{fixture_id}:worker-orchestration",
            *scale.report.command_record_refs,
        ],
        event_cursor_refs=[
            f"event-cursor:{fixture_id}:worker-orchestration",
            *scale.report.event_cursor_refs,
        ],
        outbox_refs=[f"outbox:{fixture_id}:worker-orchestration", *scale.report.outbox_refs],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:worker-orchestration",
        operator_status=_operator_status(scenario),
        completion_result=CompletenessResult.PASS,
    )


def _boundary_failure(
    *,
    fixture_id: str,
    failure: WorkerOrchestrationFailureType,
    policy_refs: list[Ref],
    scale: ScaleHardeningResult,
    hidden_dead_letter_refs: list[Ref] | None = None,
    duplicate_pollution_refs: list[Ref] | None = None,
    unrecovered_stale_lease_refs: list[Ref] | None = None,
) -> WorkerOrchestrationRuntimeResult:
    return WorkerOrchestrationRuntimeResult(
        report=_failure_report(
            fixture_id=fixture_id,
            failure=failure,
            policy_refs=policy_refs,
            hidden_dead_letter_refs=hidden_dead_letter_refs,
            duplicate_pollution_refs=duplicate_pollution_refs,
            unrecovered_stale_lease_refs=unrecovered_stale_lease_refs,
        ),
        scale=scale,
    )


def _failure_report(
    *,
    fixture_id: str,
    failure: WorkerOrchestrationFailureType,
    policy_refs: list[Ref],
    missing_ref_fields: list[str] | None = None,
    hidden_dead_letter_refs: list[Ref] | None = None,
    duplicate_pollution_refs: list[Ref] | None = None,
    unrecovered_stale_lease_refs: list[Ref] | None = None,
) -> WorkerOrchestrationRuntimeReport:
    return WorkerOrchestrationRuntimeReport(
        id=f"worker-orchestration-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        failure_type=failure,
        failure_report_refs=[f"worker-orchestration-failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=missing_ref_fields or [failure.value],
        hidden_dead_letter_refs=hidden_dead_letter_refs or [],
        duplicate_pollution_refs=duplicate_pollution_refs or [],
        unrecovered_stale_lease_refs=unrecovered_stale_lease_refs or [],
        diagnostics=[failure.value],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _scale_scenario(scenario: str) -> str:
    if scenario == "worker-orchestration-backpressure-autoscale-success":
        return "backpressure-autoscale-success"
    if scenario == "worker-orchestration-worker-crash-recovered":
        return "dead-letter-recovery-success"
    return "scale-sharding-success"


def _operator_status(scenario: str) -> str:
    if scenario == "worker-orchestration-worker-crash-recovered":
        return "worker_orchestration_worker_crash_recovered"
    if scenario == "worker-orchestration-backpressure-autoscale-success":
        return "worker_orchestration_backpressure_autoscale_completed"
    return "worker_orchestration_completed"
