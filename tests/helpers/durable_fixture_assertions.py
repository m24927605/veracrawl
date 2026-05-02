from __future__ import annotations

from veracrawl.cli.durable import DurableFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_durable_success(report: DurableFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status in {"durable_recovered", "duplicate_command_deduped"}
    assert report.command_record_refs
    assert report.command_result_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.frontier_item_refs
    assert report.lease_refs
    assert report.durable_recovery_report_ref
    assert report.reloaded is True
    assert report.missing_ref_fields == []


def assert_durable_negative(
    report: DurableFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult,
) -> None:
    assert report.operator_status == operator_status
    assert report.completion_result == completion_result
    assert report.durable_recovery_report_ref
    assert report.missing_ref_fields or report.diagnostics
