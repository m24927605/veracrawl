from __future__ import annotations

from veracrawl.cli.ops import OpsFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_ops_success(report: OpsFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "ops_console_completed"
    assert report.review_item_refs
    assert report.replay_audit_view_refs
    assert report.quality_report_refs
    assert report.dashboard_snapshot_ref
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert report.dr_restore_report_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs


def assert_ops_negative(
    report: OpsFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
    assert not report.review_item_refs
