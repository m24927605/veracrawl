from __future__ import annotations

from veracrawl.cli.output_coverage import OutputTypeCoverageFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, TargetOutputType


def assert_output_type_coverage_success(
    report: OutputTypeCoverageFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "output_type_coverage_completed"
    assert set(report.covered_output_types) == set(TargetOutputType)
    assert len(report.coverage_record_refs) == len(TargetOutputType)
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.missing_ref_fields


def assert_output_type_coverage_needs_review(
    report: OutputTypeCoverageFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "output_type_coverage_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_output_type_coverage_negative(
    report: OutputTypeCoverageFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type is not None
    assert missing_field in report.missing_ref_fields
