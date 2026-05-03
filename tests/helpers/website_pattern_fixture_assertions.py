from __future__ import annotations

from veracrawl.cli.website_patterns import WebsitePatternCoverageFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, TargetWebsitePattern


def assert_website_pattern_coverage_success(
    report: WebsitePatternCoverageFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "website_pattern_coverage_completed"
    assert set(report.covered_patterns) == set(TargetWebsitePattern)
    assert len(report.coverage_record_refs) == len(TargetWebsitePattern)
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.missing_ref_fields


def assert_website_pattern_coverage_needs_review(
    report: WebsitePatternCoverageFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "website_pattern_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_website_pattern_coverage_negative(
    report: WebsitePatternCoverageFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type is not None
    assert missing_field in report.missing_ref_fields
