"""Replay validation for row 053 ops replay and observability runtime."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.ops import OpsReplayObservabilityRuntimeReport


def missing_ops_replay_observability_refs(
    report: OpsReplayObservabilityRuntimeReport,
) -> list[str]:
    required = {
        "result_publication_export_report_ref": report.result_publication_export_report_ref,
        "worker_orchestration_runtime_report_ref": (
            report.worker_orchestration_runtime_report_ref
        ),
        "ops_console_report_ref": report.ops_console_report_ref,
        "observability_report_ref": report.observability_report_ref,
        "run_control_action_refs": report.run_control_action_refs,
        "review_item_refs": report.review_item_refs,
        "evidence_review_refs": report.evidence_review_refs,
        "replay_audit_view_refs": report.replay_audit_view_refs,
        "graph_debug_refs": report.graph_debug_refs,
        "export_status_refs": report.export_status_refs,
        "withdrawal_status_refs": report.withdrawal_status_refs,
        "recovery_action_refs": report.recovery_action_refs,
        "failure_record_refs": report.failure_record_refs,
        "dr_restore_report_refs": report.dr_restore_report_refs,
        "quality_report_refs": report.quality_report_refs,
        "dashboard_snapshot_refs": report.dashboard_snapshot_refs,
        "alert_record_refs": report.alert_record_refs,
        "runbook_action_refs": report.runbook_action_refs,
        "cost_metric_refs": report.cost_metric_refs,
        "observability_signal_refs": report.observability_signal_refs,
        "metric_sample_refs": report.metric_sample_refs,
        "trace_span_refs": report.trace_span_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "redaction_map_refs": report.redaction_map_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def ops_replay_observability_replay_passes(
    report: OpsReplayObservabilityRuntimeReport,
) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_ops_replay_observability_refs(report)
        or report.stale_dashboard_refs
        or report.unresolved_recovery_refs
        or report.unsafe_operator_action_refs
        or report.observability_gap_refs
        or report.replay_gap_refs
    )
