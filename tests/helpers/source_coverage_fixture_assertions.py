from __future__ import annotations

from veracrawl.cli.source_coverage import SourceCoverageAdapterFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.source_coverage import REQUIRED_SOURCE_COVERAGE_ADAPTERS


def assert_source_coverage_success(report: SourceCoverageAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "source_coverage_adapter_mapping_completed"
    assert set(report.verified_adapter_types) == set(REQUIRED_SOURCE_COVERAGE_ADAPTERS)
    assert report.adapter_execution_refs
    assert report.source_adapter_result_refs
    assert report.natural_result_refs
    assert report.fetch_attempt_refs
    assert report.page_snapshot_refs
    assert report.browser_interaction_refs
    assert report.credential_audit_refs
    assert report.document_artifact_refs
    assert report.api_payload_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.contract_only_refs
    assert not report.missing_ref_fields


def assert_source_coverage_needs_review(
    report: SourceCoverageAdapterFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "source_coverage_adapter_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_source_coverage_negative(
    report: SourceCoverageAdapterFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert missing_field in report.missing_ref_fields
