from __future__ import annotations

from veracrawl.cli.observability import OperationalObservabilityFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_observability_success(report: OperationalObservabilityFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "operational_observability_completed"
    assert report.signal_refs
    assert report.metric_sample_refs
    assert report.trace_span_refs
    assert report.alert_record_refs
    assert report.runbook_action_refs
    assert report.quality_report_refs
    assert report.cost_metric_refs
    assert report.dashboard_snapshot_refs
    assert report.projection_watermark_refs
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert report.dr_restore_report_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.redaction_map_refs
    assert report.collector_handoff_refs
    assert report.telemetry_backend_refs
    assert report.replay_bundle_ref


def assert_observability_needs_review(
    report: OperationalObservabilityFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == operator_status
    assert report.contract_only_refs
    assert report.missing_ref_fields
    assert not report.telemetry_backend_refs


def assert_observability_negative(
    report: OperationalObservabilityFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert missing_field in report.missing_ref_fields
