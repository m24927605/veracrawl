from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    ArtifactLifecycleOperation,
    CompletenessResult,
    CredentialDeliveryMode,
    SecurityActionSurface,
    SecurityCheckResult,
)
from veracrawl.contracts.security_privacy import (
    ArtifactLifecycleAction,
    CredentialUseAudit,
    PromptTaintBoundary,
    SecurityPolicyCheck,
    SecurityPrivacyFixtureManifest,
    SecurityPrivacyReport,
)


def test_security_policy_check_block_requires_block_reason() -> None:
    with pytest.raises(ValidationError):
        SecurityPolicyCheck(
            id="security-policy-check:bad",
            action_surface=SecurityActionSurface.NETWORK,
            subject_ref="url:private-network",
            scope_ref="egress-scope:target",
            result=SecurityCheckResult.BLOCK,
            policy_decision_refs=["policy:target:security"],
            observability_signal_refs=["observability-signal:target"],
            command_refs=["command:target:security"],
            event_refs=["event:target:security"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_credential_use_audit_rejects_raw_secret_exposure() -> None:
    with pytest.raises(ValidationError):
        CredentialUseAudit(
            id="credential-use-audit:bad",
            credential_scope_ref="credential-scope:target",
            authorized_origin_ref="origin:target",
            delivery_mode=CredentialDeliveryMode.SCOPED_HEADER,
            policy_decision_refs=["policy:target:credential"],
            approval_decision_refs=["approval:target:credential"],
            redaction_map_refs=["redaction-map:target"],
            prompt_context_refs=["context-redacted:target"],
            raw_secret_exposed=True,
            command_refs=["command:target:credential"],
            event_refs=["event:target:credential"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_credential_use_audit_rejects_sensitive_prompt_context_refs() -> None:
    with pytest.raises(ValidationError):
        CredentialUseAudit(
            id="credential-use-audit:bad-context",
            credential_scope_ref="credential-scope:target",
            authorized_origin_ref="origin:target",
            delivery_mode=CredentialDeliveryMode.SCOPED_COOKIE,
            policy_decision_refs=["policy:target:credential"],
            approval_decision_refs=["approval:target:credential"],
            redaction_map_refs=["redaction-map:target"],
            prompt_context_refs=["raw_secret:leaked-token"],
            command_refs=["command:target:credential"],
            event_refs=["event:target:credential"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_prompt_taint_boundary_rejects_unsanitized_context_refs() -> None:
    with pytest.raises(ValidationError):
        PromptTaintBoundary(
            id="prompt-taint-boundary:bad",
            tainted_source_refs=["source:target:untrusted"],
            taint_label_refs=["taint:target:web-content"],
            sanitized_context_refs=["raw_prompt:ignore-policy"],
            blocked_tool_refs=["tool-call:target:unsafe"],
            prompt_use_restriction_refs=["prompt-restriction:target:no-tools"],
            policy_decision_refs=["policy:target:prompt"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_artifact_lifecycle_delete_is_blocked_under_legal_hold() -> None:
    with pytest.raises(ValidationError):
        ArtifactLifecycleAction(
            id="artifact-lifecycle-action:bad-delete",
            action_type=ArtifactLifecycleOperation.DELETE,
            artifact_ref="artifact:target:raw-source",
            lifecycle_state_ref="lifecycle:target:delete",
            retention_policy_ref="retention:target:standard",
            privacy_policy_ref="privacy:target:restricted",
            legal_hold_ref="legal-hold:target:case",
            legal_hold_active=True,
            projection_cleanup_refs=["projection-cleanup:target:all"],
            policy_decision_refs=["policy:target:lifecycle"],
            approval_decision_refs=["approval:target:lifecycle"],
            command_refs=["command:target:lifecycle"],
            event_refs=["event:target:lifecycle"],
            outbox_refs=["outbox:target:lifecycle"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_side_effecting_lifecycle_action_requires_approval_refs() -> None:
    with pytest.raises(ValidationError):
        ArtifactLifecycleAction(
            id="artifact-lifecycle-action:bad-approval",
            action_type=ArtifactLifecycleOperation.REDACT,
            artifact_ref="artifact:target:raw-source",
            lifecycle_state_ref="lifecycle:target:redacted",
            retention_policy_ref="retention:target:standard",
            privacy_policy_ref="privacy:target:restricted",
            projection_cleanup_refs=["projection-cleanup:target:all"],
            policy_decision_refs=["policy:target:lifecycle"],
            command_refs=["command:target:lifecycle"],
            event_refs=["event:target:lifecycle"],
            outbox_refs=["outbox:target:lifecycle"],
            replay_bundle_ref="replay-bundle:target:redacted",
        )


def test_security_privacy_report_pass_requires_integrated_refs() -> None:
    with pytest.raises(ValidationError):
        SecurityPrivacyReport(
            id="security-privacy-report:bad",
            run_ref="run:target",
            security_policy_check_refs=["security-policy-check:target"],
            credential_use_audit_refs=["credential-use-audit:target"],
            prompt_taint_boundary_refs=["prompt-taint-boundary:target"],
            artifact_lifecycle_action_refs=["artifact-lifecycle-action:target"],
            projection_cleanup_refs=["projection-cleanup:target"],
            redacted_replay_refs=["replay-bundle:target:redacted"],
            policy_decision_refs=["policy:target:security"],
            command_record_refs=["command:target:security"],
            event_cursor_refs=["event-cursor:target:security"],
            outbox_refs=["outbox:target:security"],
            failure_record_refs=["failure-record:target"],
            recovery_action_refs=["recovery-action:target"],
            redaction_map_refs=["redaction-map:target"],
            replay_bundle_ref="replay-bundle:target:redacted",
            operator_status="security_privacy_lifecycle_completed",
            result=CompletenessResult.PASS,
        )


def test_security_privacy_report_accepts_complete_zero_leak_pass() -> None:
    report = SecurityPrivacyReport(
        id="security-privacy-report:target",
        run_ref="run:target",
        security_policy_check_refs=["security-policy-check:target"],
        credential_use_audit_refs=["credential-use-audit:target"],
        prompt_taint_boundary_refs=["prompt-taint-boundary:target"],
        artifact_lifecycle_action_refs=["artifact-lifecycle-action:target"],
        projection_cleanup_refs=["projection-cleanup:target"],
        redacted_replay_refs=["replay-bundle:target:redacted"],
        observability_report_refs=["observability-report:target"],
        policy_decision_refs=["policy:target:security"],
        command_record_refs=["command:target:security"],
        event_cursor_refs=["event-cursor:target:security"],
        outbox_refs=["outbox:target:security"],
        failure_record_refs=["failure-record:target"],
        recovery_action_refs=["recovery-action:target"],
        redaction_map_refs=["redaction-map:target"],
        replay_bundle_ref="replay-bundle:target:redacted",
        operator_status="security_privacy_lifecycle_completed",
        result=CompletenessResult.PASS,
    )
    assert report.leakage_count == 0


def test_security_privacy_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        SecurityPrivacyFixtureManifest(
            id="security-privacy-bad",
            scenario="security-privacy-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            negative_case=True,
        )
