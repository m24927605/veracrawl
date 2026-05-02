from __future__ import annotations

from veracrawl.cli.source import SourceFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_source_success(report: SourceFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "source_acquired"
    assert report.source_adapter_result_ref
    assert report.fetch_attempt_refs
    assert report.fetch_result_refs
    assert report.artifact_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.recovery_report_refs
    assert not report.missing_ref_fields


def assert_source_negative(
    report: SourceFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult,
) -> None:
    assert report.operator_status == operator_status
    assert report.completion_result == completion_result
    assert report.failure_report_refs or report.missing_ref_fields
