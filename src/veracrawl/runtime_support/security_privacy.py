"""Core security, privacy, and lifecycle gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    ArtifactLifecycleOperation,
    CompletenessResult,
    CredentialDeliveryMode,
    OpsFailureType,
    OpsRecoveryStatus,
    OpsSeverity,
    RecoveryActionType,
    SecurityActionSurface,
    SecurityCheckResult,
    SecurityPrivacyFailureType,
)
from veracrawl.contracts.ops import FailureRecord, RecoveryAction
from veracrawl.contracts.security_privacy import (
    ArtifactLifecycleAction,
    CredentialUseAudit,
    ProjectionCleanupRecord,
    PromptTaintBoundary,
    SecurityPolicyCheck,
    SecurityPrivacyReport,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_BACKEND = "security_privacy"


def _fail_closed_in_production(gate: str) -> None:
    if current_mode() is RuntimeMode.PRODUCTION:
        raise ProductionRuntimeNotImplemented(backend=_BACKEND, gate=gate)


@dataclass(frozen=True)
class SecurityPrivacyGateResult:
    report: SecurityPrivacyReport
    security_policy_checks: list[SecurityPolicyCheck]
    credential_use_audits: list[CredentialUseAudit]
    prompt_taint_boundaries: list[PromptTaintBoundary]
    artifact_lifecycle_actions: list[ArtifactLifecycleAction]
    projection_cleanup_records: list[ProjectionCleanupRecord]
    failure_records: list[FailureRecord]
    recovery_actions: list[RecoveryAction]


_FAILURES: dict[str, tuple[SecurityPrivacyFailureType, str, RecoveryActionType]] = {
    "security-privacy-unsafe-network": (
        SecurityPrivacyFailureType.UNSAFE_NETWORK,
        "security_policy_check_refs",
        RecoveryActionType.REQUEST_REVIEW,
    ),
    "security-privacy-prompt-injection": (
        SecurityPrivacyFailureType.PROMPT_INJECTION_TOOL_MISUSE,
        "prompt_taint_boundary_refs",
        RecoveryActionType.QUARANTINE_TAINTED_CONTEXT,
    ),
    "security-privacy-credential-leakage": (
        SecurityPrivacyFailureType.CREDENTIAL_LEAKAGE,
        "raw_secret_leak_refs",
        RecoveryActionType.REDACT_SENSITIVE_CONTEXT,
    ),
    "security-privacy-missing-lifecycle": (
        SecurityPrivacyFailureType.MISSING_LIFECYCLE_PROPAGATION,
        "artifact_lifecycle_action_refs",
        RecoveryActionType.REDACT_ARTIFACT,
    ),
    "security-privacy-legal-hold-delete": (
        SecurityPrivacyFailureType.LEGAL_HOLD_DELETE,
        "legal_hold_violation_refs",
        RecoveryActionType.REQUEST_REVIEW,
    ),
    "security-privacy-missing-projection-cleanup": (
        SecurityPrivacyFailureType.MISSING_PROJECTION_CLEANUP,
        "projection_cleanup_refs",
        RecoveryActionType.REBUILD_PROJECTION,
    ),
    "security-privacy-missing-redacted-replay": (
        SecurityPrivacyFailureType.MISSING_REDACTED_REPLAY,
        "redacted_replay_refs",
        RecoveryActionType.REPLAY_EVENTS,
    ),
    "security-privacy-missing-observability": (
        SecurityPrivacyFailureType.MISSING_OBSERVABILITY_REFS,
        "observability_report_refs",
        RecoveryActionType.RESTORE_OBSERVABILITY_SIGNAL,
    ),
}


def run_security_privacy_gate(*, fixture_id: str, scenario: str) -> SecurityPrivacyGateResult:
    _fail_closed_in_production("run_security_privacy_gate")
    if scenario == "security-privacy-policy-only":
        return _policy_only_result(fixture_id=fixture_id)
    if scenario in _FAILURES:
        failure, missing_field, action_type = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            action_type=action_type,
        )
    return _success_result(fixture_id=fixture_id)


def _success_result(*, fixture_id: str) -> SecurityPrivacyGateResult:
    policy_refs = [f"policy:{fixture_id}:security-privacy"]
    approval_refs = [f"approval:{fixture_id}:security-privacy"]
    replay_ref = f"replay-bundle:{fixture_id}:redacted"
    redaction_refs = [f"redaction-map:{fixture_id}:security-privacy"]
    command_ref = f"command:{fixture_id}:security-privacy"
    event_ref = f"event-cursor:{fixture_id}:security-privacy"
    outbox_ref = f"outbox:{fixture_id}:security-privacy"
    observability_ref = f"observability-report:{fixture_id}"
    failure_record = _failure_record(
        fixture_id,
        failure=SecurityPrivacyFailureType.PROMPT_INJECTION_TOOL_MISUSE,
        failed_ref=f"prompt-taint-boundary:{fixture_id}",
        policy_decision_refs=policy_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=RecoveryActionType.QUARANTINE_TAINTED_CONTEXT,
        policy_decision_refs=policy_refs,
        approval_decision_refs=approval_refs,
    )
    policy_checks = [
        SecurityPolicyCheck(
            id=f"security-policy-check:{fixture_id}:egress",
            action_surface=SecurityActionSurface.NETWORK,
            subject_ref=f"url:{fixture_id}:private-network",
            scope_ref=f"egress-scope:{fixture_id}",
            result=SecurityCheckResult.BLOCK,
            policy_decision_refs=policy_refs,
            blocked_reason_refs=[f"blocked-reason:{fixture_id}:private-network"],
            observability_signal_refs=[observability_ref],
            command_refs=[command_ref],
            event_refs=[event_ref],
            replay_bundle_ref=replay_ref,
        )
    ]
    credential_audits = [
        CredentialUseAudit(
            id=f"credential-use-audit:{fixture_id}:scoped-header",
            credential_scope_ref=f"credential-scope:{fixture_id}:readonly",
            authorized_origin_ref=f"origin:{fixture_id}:authorized",
            delivery_mode=CredentialDeliveryMode.SCOPED_HEADER,
            policy_decision_refs=policy_refs,
            approval_decision_refs=approval_refs,
            redaction_map_refs=redaction_refs,
            prompt_context_refs=[f"context-redacted:{fixture_id}:credential-use"],
            command_refs=[command_ref],
            event_refs=[event_ref],
            replay_bundle_ref=replay_ref,
        )
    ]
    prompt_boundaries = [
        PromptTaintBoundary(
            id=f"prompt-taint-boundary:{fixture_id}",
            tainted_source_refs=[f"source:{fixture_id}:untrusted"],
            taint_label_refs=[f"taint:{fixture_id}:web-content"],
            sanitized_context_refs=[f"context-sanitized:{fixture_id}:web-content"],
            blocked_tool_refs=[f"tool-call:{fixture_id}:unsafe-publication"],
            prompt_use_restriction_refs=[f"prompt-restriction:{fixture_id}:no-tools"],
            policy_decision_refs=policy_refs,
            replay_bundle_ref=replay_ref,
        )
    ]
    lifecycle_actions = [
        ArtifactLifecycleAction(
            id=f"artifact-lifecycle-action:{fixture_id}:redact",
            action_type=ArtifactLifecycleOperation.REDACT,
            artifact_ref=f"artifact:{fixture_id}:raw-source",
            lifecycle_state_ref=f"lifecycle:{fixture_id}:redacted",
            retention_policy_ref=f"retention:{fixture_id}:standard",
            privacy_policy_ref=f"privacy:{fixture_id}:restricted",
            projection_cleanup_refs=[f"projection-cleanup:{fixture_id}:all"],
            policy_decision_refs=policy_refs,
            approval_decision_refs=approval_refs,
            command_refs=[command_ref],
            event_refs=[event_ref],
            outbox_refs=[outbox_ref],
            replay_bundle_ref=replay_ref,
        )
    ]
    projection_cleanups = [
        ProjectionCleanupRecord(
            id=f"projection-cleanup:{fixture_id}:all",
            lifecycle_action_ref=lifecycle_actions[0].id,
            affected_projection_refs=[
                f"projection:{fixture_id}:search",
                f"projection:{fixture_id}:graph",
                f"projection:{fixture_id}:memory",
                f"projection:{fixture_id}:dashboard",
                f"projection:{fixture_id}:export",
            ],
            cleanup_event_refs=[f"event:{fixture_id}:projection_cleanup_recorded"],
            projection_watermark_refs=[f"projection-watermark:{fixture_id}:privacy"],
            policy_decision_refs=policy_refs,
            replay_bundle_ref=replay_ref,
        )
    ]
    report = SecurityPrivacyReport(
        id=f"security-privacy-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        security_policy_check_refs=[check.id for check in policy_checks],
        credential_use_audit_refs=[audit.id for audit in credential_audits],
        prompt_taint_boundary_refs=[boundary.id for boundary in prompt_boundaries],
        artifact_lifecycle_action_refs=[action.id for action in lifecycle_actions],
        projection_cleanup_refs=[record.id for record in projection_cleanups],
        redacted_replay_refs=[replay_ref],
        observability_report_refs=[observability_ref],
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        redaction_map_refs=redaction_refs,
        replay_bundle_ref=replay_ref,
        leakage_count=0,
        operator_status="security_privacy_lifecycle_completed",
        result=CompletenessResult.PASS,
    )
    return SecurityPrivacyGateResult(
        report=report,
        security_policy_checks=policy_checks,
        credential_use_audits=credential_audits,
        prompt_taint_boundaries=prompt_boundaries,
        artifact_lifecycle_actions=lifecycle_actions,
        projection_cleanup_records=projection_cleanups,
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
    )


def _policy_only_result(*, fixture_id: str) -> SecurityPrivacyGateResult:
    report = SecurityPrivacyReport(
        id=f"security-privacy-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=[f"policy:{fixture_id}:security-privacy"],
        contract_only_refs=["security-privacy:policy-refs-only"],
        missing_ref_fields=[
            "security_policy_check_refs",
            "credential_use_audit_refs",
            "prompt_taint_boundary_refs",
            "artifact_lifecycle_action_refs",
            "projection_cleanup_refs",
            "redacted_replay_refs",
            "observability_report_refs",
        ],
        operator_status="security_privacy_policy_only",
        result=CompletenessResult.NEEDS_REVIEW,
    )
    return SecurityPrivacyGateResult(
        report=report,
        security_policy_checks=[],
        credential_use_audits=[],
        prompt_taint_boundaries=[],
        artifact_lifecycle_actions=[],
        projection_cleanup_records=[],
        failure_records=[],
        recovery_actions=[],
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: SecurityPrivacyFailureType,
    missing_field: str,
    action_type: RecoveryActionType,
) -> SecurityPrivacyGateResult:
    policy_refs = [f"policy:{fixture_id}:security-privacy"]
    approval_refs = [f"approval:{fixture_id}:security-privacy"]
    failure_record = _failure_record(
        fixture_id,
        failure=failure,
        failed_ref=f"security-privacy-report:{fixture_id}",
        policy_decision_refs=policy_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=action_type,
        policy_decision_refs=policy_refs,
        approval_decision_refs=approval_refs,
    )
    report = SecurityPrivacyReport(
        id=f"security-privacy-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        security_policy_check_refs=[]
        if missing_field == "security_policy_check_refs"
        else [f"security-policy-check:{fixture_id}:network"],
        credential_use_audit_refs=[]
        if missing_field == "credential_use_audit_refs"
        else [f"credential-use-audit:{fixture_id}:scoped"],
        prompt_taint_boundary_refs=[]
        if missing_field == "prompt_taint_boundary_refs"
        else [f"prompt-taint-boundary:{fixture_id}"],
        artifact_lifecycle_action_refs=[]
        if missing_field == "artifact_lifecycle_action_refs"
        else [f"artifact-lifecycle-action:{fixture_id}:redact"],
        projection_cleanup_refs=[]
        if missing_field == "projection_cleanup_refs"
        else [f"projection-cleanup:{fixture_id}:all"],
        redacted_replay_refs=[]
        if missing_field == "redacted_replay_refs"
        else [f"replay-bundle:{fixture_id}:redacted"],
        observability_report_refs=[]
        if missing_field == "observability_report_refs"
        else [f"observability-report:{fixture_id}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command:{fixture_id}:security-privacy"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:security-privacy"],
        outbox_refs=[f"outbox:{fixture_id}:security-privacy"],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        redaction_map_refs=[f"redaction-map:{fixture_id}:security-privacy"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:security-privacy",
        leakage_count=1 if missing_field == "raw_secret_leak_refs" else 0,
        raw_secret_leak_refs=[f"raw-secret-leak:{fixture_id}:prompt"]
        if missing_field == "raw_secret_leak_refs"
        else [],
        unsafe_action_refs=[f"unsafe-action:{fixture_id}:legal-hold-delete"]
        if missing_field == "legal_hold_violation_refs"
        else [],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        result=CompletenessResult.FAIL,
    )
    return SecurityPrivacyGateResult(
        report=report,
        security_policy_checks=[],
        credential_use_audits=[],
        prompt_taint_boundaries=[],
        artifact_lifecycle_actions=[],
        projection_cleanup_records=[],
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
    )


def _failure_record(
    fixture_id: str,
    *,
    failure: SecurityPrivacyFailureType,
    failed_ref: Ref,
    policy_decision_refs: list[Ref],
) -> FailureRecord:
    return FailureRecord(
        id=f"failure-record:{fixture_id}:{failure.value}",
        run_id=f"run:{fixture_id}",
        failure_type=_ops_failure_type_for(failure),
        failed_ref=failed_ref,
        owner_service_ref="policy:security-privacy",
        severity=OpsSeverity.HIGH,
        retryable=True,
        diagnostic_ref=f"diagnostic:{fixture_id}:{failure.value}",
        policy_decision_refs=policy_decision_refs,
        replay_audit_refs=[f"replay-audit:{fixture_id}:security-privacy"],
    )


def _recovery_action(
    fixture_id: str,
    *,
    failure_record_id: str,
    action_type: RecoveryActionType,
    policy_decision_refs: list[Ref],
    approval_decision_refs: list[Ref],
) -> RecoveryAction:
    return RecoveryAction(
        id=f"recovery-action:{fixture_id}:{action_type.value}",
        failure_record_id=failure_record_id,
        action_type=action_type,
        command_refs=[f"command:{fixture_id}:{action_type.value}"]
        if action_type != RecoveryActionType.REQUEST_REVIEW
        else [],
        policy_decision_refs=policy_decision_refs,
        approval_decision_refs=approval_decision_refs
        if action_type != RecoveryActionType.REQUEST_REVIEW
        else [],
        review_item_refs=[f"review-item:{fixture_id}:security-privacy"],
        status=OpsRecoveryStatus.PROPOSED,
    )


def _ops_failure_type_for(failure: SecurityPrivacyFailureType) -> OpsFailureType:
    if failure == SecurityPrivacyFailureType.CREDENTIAL_LEAKAGE:
        return OpsFailureType.REDACTION_VIOLATION
    if failure in {
        SecurityPrivacyFailureType.MISSING_LIFECYCLE_PROPAGATION,
        SecurityPrivacyFailureType.LEGAL_HOLD_DELETE,
    }:
        return OpsFailureType.ARTIFACT_LIFECYCLE
    if failure == SecurityPrivacyFailureType.MISSING_PROJECTION_CLEANUP:
        return OpsFailureType.PROJECTION
    if failure == SecurityPrivacyFailureType.MISSING_OBSERVABILITY_REFS:
        return OpsFailureType.OBSERVABILITY_GAP
    return OpsFailureType.POLICY
