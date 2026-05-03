"""Worker orchestration replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.scale import WorkerOrchestrationRuntimeReport


def missing_worker_orchestration_replay_refs(
    report: WorkerOrchestrationRuntimeReport,
) -> list[str]:
    required = {
        "production_persistence_runtime_report_ref": (
            report.production_persistence_runtime_report_ref
        ),
        "queue_broker_conformance_report_ref": report.queue_broker_conformance_report_ref,
        "live_http_acquisition_report_ref": report.live_http_acquisition_report_ref,
        "live_normalization_runtime_report_ref": (
            report.live_normalization_runtime_report_ref
        ),
        "live_evidence_verification_runtime_report_ref": (
            report.live_evidence_verification_runtime_report_ref
        ),
        "scale_recovery_report_ref": report.scale_recovery_report_ref,
        "worker_pool_refs": report.worker_pool_refs,
        "worker_heartbeat_refs": report.worker_heartbeat_refs,
        "worker_capacity_refs": report.worker_capacity_refs,
        "queue_topology_ref": report.queue_topology_ref,
        "queue_item_refs": report.queue_item_refs,
        "shard_lease_refs": report.shard_lease_refs,
        "lease_heartbeat_refs": report.lease_heartbeat_refs,
        "fencing_token_refs": report.fencing_token_refs,
        "visibility_timeout_refs": report.visibility_timeout_refs,
        "fairness_scope_refs": report.fairness_scope_refs,
        "retry_refs": report.retry_refs,
        "dead_letter_refs": report.dead_letter_refs,
        "failure_record_refs": report.failure_record_refs,
        "recovery_action_refs": report.recovery_action_refs,
        "duplicate_suppression_refs": report.duplicate_suppression_refs,
        "backpressure_signal_refs": report.backpressure_signal_refs,
        "autoscaling_decision_refs": report.autoscaling_decision_refs,
        "pending_outbox_refs": report.pending_outbox_refs,
        "event_gap_refs": report.event_gap_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def worker_orchestration_replay_passes(
    report: WorkerOrchestrationRuntimeReport,
) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_worker_orchestration_replay_refs(report)
        or report.hidden_dead_letter_refs
        or report.duplicate_pollution_refs
        or report.unrecovered_stale_lease_refs
    )
