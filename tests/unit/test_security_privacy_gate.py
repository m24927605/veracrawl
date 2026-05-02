from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, SecurityPrivacyFailureType
from veracrawl.runtime_support.security_privacy import run_security_privacy_gate


def test_security_privacy_gate_success_requires_canonical_refs() -> None:
    result = run_security_privacy_gate(
        fixture_id="unit",
        scenario="security-privacy-success",
    )
    report = result.report
    assert report.result == CompletenessResult.PASS
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
    assert report.redaction_map_refs
    assert result.security_policy_checks
    assert result.credential_use_audits
    assert result.prompt_taint_boundaries
    assert result.artifact_lifecycle_actions
    assert result.projection_cleanup_records
    assert result.failure_records
    assert result.recovery_actions


def test_security_privacy_policy_only_needs_review() -> None:
    result = run_security_privacy_gate(
        fixture_id="unit-policy-only",
        scenario="security-privacy-policy-only",
    )
    assert result.report.result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert "security_policy_check_refs" in result.report.missing_ref_fields
    assert not result.report.security_policy_check_refs


def test_security_privacy_negative_scenarios_fail_with_recovery_refs() -> None:
    expectations = {
        "security-privacy-unsafe-network": SecurityPrivacyFailureType.UNSAFE_NETWORK,
        "security-privacy-prompt-injection": (
            SecurityPrivacyFailureType.PROMPT_INJECTION_TOOL_MISUSE
        ),
        "security-privacy-credential-leakage": (
            SecurityPrivacyFailureType.CREDENTIAL_LEAKAGE
        ),
        "security-privacy-missing-lifecycle": (
            SecurityPrivacyFailureType.MISSING_LIFECYCLE_PROPAGATION
        ),
        "security-privacy-legal-hold-delete": SecurityPrivacyFailureType.LEGAL_HOLD_DELETE,
        "security-privacy-missing-projection-cleanup": (
            SecurityPrivacyFailureType.MISSING_PROJECTION_CLEANUP
        ),
        "security-privacy-missing-redacted-replay": (
            SecurityPrivacyFailureType.MISSING_REDACTED_REPLAY
        ),
        "security-privacy-missing-observability": (
            SecurityPrivacyFailureType.MISSING_OBSERVABILITY_REFS
        ),
    }
    for scenario, failure in expectations.items():
        result = run_security_privacy_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
        assert result.failure_records
        assert result.recovery_actions
