from __future__ import annotations

from veracrawl.cli.ops_runtime import OpsReplayObservabilityFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_ops_runtime_success(
    report: OpsReplayObservabilityFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == operator_status
    assert report.result_publication_export_report_ref
    assert report.worker_orchestration_runtime_report_ref
    assert report.ops_console_report_ref
    assert report.observability_report_ref
    assert report.run_control_action_refs
    assert report.review_item_refs
    assert report.evidence_review_refs
    assert report.replay_audit_view_refs
    assert report.graph_debug_refs
    assert report.export_status_refs
    assert report.withdrawal_status_refs
    assert report.recovery_action_refs
    assert report.failure_record_refs
    assert report.dr_restore_report_refs
    assert report.quality_report_refs
    assert report.dashboard_snapshot_refs
    assert report.alert_record_refs
    assert report.runbook_action_refs
    assert report.cost_metric_refs
    assert report.observability_signal_refs
    assert report.metric_sample_refs
    assert report.trace_span_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.redaction_map_refs
    assert report.replay_bundle_ref
    assert report.failure_type is None


def assert_ops_runtime_negative(
    report: OpsReplayObservabilityFixtureRunReport,
    *,
    operator_status: str,
    failure_type: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type == failure_type
    assert report.failure_report_refs
    assert report.missing_ref_fields
