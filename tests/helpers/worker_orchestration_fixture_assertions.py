from __future__ import annotations

from veracrawl.cli.worker_orchestration import WorkerOrchestrationFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_worker_orchestration_success(
    report: WorkerOrchestrationFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == operator_status
    assert report.production_persistence_runtime_report_ref
    assert report.queue_broker_conformance_report_ref
    assert report.live_http_acquisition_report_ref
    assert report.live_normalization_runtime_report_ref
    assert report.live_evidence_verification_runtime_report_ref
    assert report.scale_recovery_report_ref
    assert report.worker_pool_refs
    assert report.worker_heartbeat_refs
    assert report.worker_capacity_refs
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
    assert report.failure_type is None
    assert not report.missing_ref_fields


def assert_worker_orchestration_negative(
    report: WorkerOrchestrationFixtureRunReport,
    *,
    operator_status: str,
    failure_type: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type == failure_type
    assert report.failure_report_refs
    assert report.missing_ref_fields
