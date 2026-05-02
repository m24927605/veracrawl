from __future__ import annotations

from veracrawl.cli.security_privacy import SecurityPrivacyFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_security_privacy_success(report: SecurityPrivacyFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "security_privacy_lifecycle_completed"
    assert report.leakage_count == 0
    assert report.security_policy_check_refs
    assert report.credential_use_audit_refs
    assert report.prompt_taint_boundary_refs
    assert report.artifact_lifecycle_action_refs
    assert report.projection_cleanup_refs
    assert report.redacted_replay_refs
    assert report.observability_report_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert report.redaction_map_refs
    assert report.replay_bundle_ref
    assert not report.raw_secret_leak_refs
    assert not report.unsafe_action_refs
    assert not report.contract_only_refs
    assert not report.missing_ref_fields


def assert_security_privacy_needs_review(
    report: SecurityPrivacyFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == operator_status
    assert report.contract_only_refs
    assert report.missing_ref_fields
    assert not report.security_policy_check_refs


def assert_security_privacy_negative(
    report: SecurityPrivacyFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert missing_field in report.missing_ref_fields
