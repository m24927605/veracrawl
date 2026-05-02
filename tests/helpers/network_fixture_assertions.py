from __future__ import annotations

from veracrawl.cli.network import NetworkFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_network_success(report: NetworkFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status in {"network_acquired", "browser_observed"}
    assert report.source_acquisition_report_ref
    assert report.artifact_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.recovery_report_refs
    assert not report.missing_ref_fields


def assert_network_negative(
    report: NetworkFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult,
) -> None:
    assert report.operator_status == operator_status
    assert report.completion_result == completion_result
    assert report.failure_report_refs or report.missing_ref_fields
    if operator_status not in {"size_budget_exceeded"}:
        assert not report.artifact_refs
