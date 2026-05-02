from __future__ import annotations

from veracrawl.cli.projection import AdvancedGraphFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_advanced_graph_success(report: AdvancedGraphFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "advanced_graph_projection_completed"
    assert report.projection_spec_ref
    assert report.rebuild_job_ref
    assert report.delta_report_ref
    assert report.quality_report_ref
    assert report.signal_refs
    assert report.temporal_record_refs
    assert report.watermark_ref
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs


def assert_advanced_graph_negative(
    report: AdvancedGraphFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_report_refs or report.mismatch_report_ref
    assert report.missing_ref_fields
    assert not report.delta_report_ref
