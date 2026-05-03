from __future__ import annotations

from veracrawl.cli.source_runtime import DynamicSourceRuntimeFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.source_runtime import REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS


def assert_dynamic_source_runtime_success(
    report: DynamicSourceRuntimeFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "dynamic_source_runtime_completed"
    assert set(report.verified_adapter_types) == set(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS)
    assert report.adapter_record_refs
    assert report.source_adapter_result_refs
    assert report.natural_result_refs
    assert report.fetch_attempt_refs
    assert report.page_snapshot_refs
    assert report.browser_interaction_refs
    assert report.credential_audit_refs
    assert report.document_artifact_refs
    assert report.api_payload_refs
    assert report.file_artifact_refs
    assert report.seed_plan_refs
    assert report.prior_snapshot_refs
    assert report.command_record_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.runtime_adapter_refs
    assert report.replay_bundle_ref
    assert not report.contract_only_refs
    assert not report.missing_ref_fields


def assert_dynamic_source_runtime_needs_review(
    report: DynamicSourceRuntimeFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "dynamic_source_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_dynamic_source_runtime_negative(
    report: DynamicSourceRuntimeFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert missing_field in report.missing_ref_fields
