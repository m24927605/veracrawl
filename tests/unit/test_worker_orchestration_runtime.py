from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    WorkerOrchestrationFailureType,
    WorkerPool,
)
from veracrawl.scale.worker_orchestration import run_worker_orchestration_runtime


def test_worker_orchestration_success_has_required_runtime_refs() -> None:
    result = run_worker_orchestration_runtime(
        fixture_id="unit-worker-orchestration",
        scenario="worker-orchestration-production-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert result.scale is not None
    assert report.production_persistence_runtime_report_ref
    assert report.queue_broker_conformance_report_ref
    assert report.live_http_acquisition_report_ref
    assert report.live_normalization_runtime_report_ref
    assert report.live_evidence_verification_runtime_report_ref
    assert report.scale_recovery_report_ref
    assert len(set(report.worker_pool_refs)) == len(WorkerPool)
    assert report.worker_heartbeat_refs
    assert report.worker_capacity_refs
    assert report.queue_topology_ref
    assert report.queue_item_refs
    assert report.shard_lease_refs
    assert report.lease_heartbeat_refs
    assert report.fencing_token_refs
    assert report.visibility_timeout_refs
    assert report.fairness_scope_refs
    assert report.retry_refs
    assert report.dead_letter_refs
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert report.duplicate_suppression_refs
    assert report.backpressure_signal_refs
    assert report.autoscaling_decision_refs
    assert report.pending_outbox_refs
    assert report.event_gap_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def test_worker_orchestration_success_variants_have_operator_statuses() -> None:
    crash = run_worker_orchestration_runtime(
        fixture_id="unit-worker-crash",
        scenario="worker-orchestration-worker-crash-recovered",
    ).report
    autoscale = run_worker_orchestration_runtime(
        fixture_id="unit-autoscale",
        scenario="worker-orchestration-backpressure-autoscale-success",
    ).report
    assert crash.operator_status == "worker_orchestration_worker_crash_recovered"
    assert autoscale.operator_status == "worker_orchestration_backpressure_autoscale_completed"


def test_worker_orchestration_dependency_failures_are_typed() -> None:
    expectations = {
        "worker-orchestration-missing-persistence": (
            WorkerOrchestrationFailureType.MISSING_PERSISTENCE
        ),
        "worker-orchestration-missing-queue-broker": (
            WorkerOrchestrationFailureType.MISSING_QUEUE_BROKER
        ),
        "worker-orchestration-missing-heartbeat": (
            WorkerOrchestrationFailureType.MISSING_HEARTBEAT
        ),
        "worker-orchestration-backpressure-without-policy": (
            WorkerOrchestrationFailureType.BACKPRESSURE_WITHOUT_POLICY
        ),
        "worker-orchestration-replay-mismatch": (
            WorkerOrchestrationFailureType.REPLAY_MISMATCH
        ),
    }
    for scenario, failure in expectations.items():
        report = run_worker_orchestration_runtime(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert report.operator_status == failure.value
        assert report.failure_report_refs
        assert report.missing_ref_fields


def test_worker_orchestration_boundary_failures_are_typed() -> None:
    stale = run_worker_orchestration_runtime(
        fixture_id="unit-stale-lease",
        scenario="worker-orchestration-stale-lease-unrecovered",
    ).report
    hidden = run_worker_orchestration_runtime(
        fixture_id="unit-hidden-dead-letter",
        scenario="worker-orchestration-dead-letter-hidden",
    ).report
    duplicate = run_worker_orchestration_runtime(
        fixture_id="unit-duplicate-pollution",
        scenario="worker-orchestration-duplicate-pollution",
    ).report
    assert stale.failure_type == WorkerOrchestrationFailureType.STALE_LEASE_UNRECOVERED
    assert stale.unrecovered_stale_lease_refs
    assert hidden.failure_type == WorkerOrchestrationFailureType.DEAD_LETTER_HIDDEN
    assert hidden.hidden_dead_letter_refs
    assert duplicate.failure_type == WorkerOrchestrationFailureType.DUPLICATE_POLLUTION
    assert duplicate.duplicate_pollution_refs
