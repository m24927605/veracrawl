"""Security, privacy, and lifecycle gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    ArtifactLifecycleOperation,
    CompletenessResult,
    CredentialDeliveryMode,
    SecurityActionSurface,
    SecurityCheckResult,
    SecurityPrivacyFailureType,
)

_SENSITIVE_MARKERS = (
    "password",
    "secret",
    "token=",
    "api_key",
    "aws_access_key",
    "aws_secret",
    "postgres://",
    "redis://:",
    "raw_prompt:",
    "raw_secret:",
    "raw_artifact:",
)


def _ensure_no_sensitive_values(values: list[str], field_name: str) -> None:
    for value in values:
        lowered = value.lower()
        if any(marker in lowered for marker in _SENSITIVE_MARKERS):
            raise ValueError(f"{field_name} contains unredacted sensitive value")


class SecurityPolicyCheck(TimestampedModel):
    id: str
    action_surface: SecurityActionSurface
    subject_ref: Ref
    scope_ref: Ref
    result: SecurityCheckResult
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    blocked_reason_refs: list[Ref] = Field(default_factory=list)
    observability_signal_refs: list[Ref] = Field(default_factory=list)
    command_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_security_policy_check(self) -> SecurityPolicyCheck:
        if not self.subject_ref or not self.scope_ref:
            raise ValueError("security policy check requires subject and scope refs")
        if not self.policy_decision_refs:
            raise ValueError("security policy check requires policy refs")
        if self.result == SecurityCheckResult.BLOCK and not self.blocked_reason_refs:
            raise ValueError("blocked security check requires blocked reason refs")
        if not self.observability_signal_refs:
            raise ValueError("security policy check requires observability refs")
        if not self.command_refs or not self.event_refs:
            raise ValueError("security policy check requires command and event refs")
        return self


class CredentialUseAudit(TimestampedModel):
    id: str
    credential_scope_ref: Ref
    authorized_origin_ref: Ref
    delivery_mode: CredentialDeliveryMode
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    prompt_context_refs: list[Ref] = Field(default_factory=list)
    raw_secret_exposed: bool = False
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    command_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_credential_use_audit(self) -> CredentialUseAudit:
        if not self.credential_scope_ref or not self.authorized_origin_ref:
            raise ValueError("credential use audit requires scope and origin refs")
        if not self.policy_decision_refs or not self.approval_decision_refs:
            raise ValueError("credential use audit requires policy and approval refs")
        if not self.redaction_map_refs:
            raise ValueError("credential use audit requires redaction refs")
        if self.raw_secret_exposed or self.raw_secret_leak_refs:
            raise ValueError("credential use audit cannot expose raw secrets")
        _ensure_no_sensitive_values(self.prompt_context_refs, "credential prompt context refs")
        if not self.command_refs or not self.event_refs:
            raise ValueError("credential use audit requires command and event refs")
        return self


class PromptTaintBoundary(TimestampedModel):
    id: str
    tainted_source_refs: list[Ref] = Field(default_factory=list)
    taint_label_refs: list[Ref] = Field(default_factory=list)
    sanitized_context_refs: list[Ref] = Field(default_factory=list)
    blocked_tool_refs: list[Ref] = Field(default_factory=list)
    prompt_use_restriction_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_prompt_taint_boundary(self) -> PromptTaintBoundary:
        if not self.tainted_source_refs or not self.taint_label_refs:
            raise ValueError("prompt taint boundary requires tainted source and label refs")
        if not self.sanitized_context_refs:
            raise ValueError("prompt taint boundary requires sanitized context refs")
        if not self.blocked_tool_refs:
            raise ValueError("prompt taint boundary requires blocked unsafe tool refs")
        if not self.prompt_use_restriction_refs or not self.policy_decision_refs:
            raise ValueError("prompt taint boundary requires restriction and policy refs")
        _ensure_no_sensitive_values(self.sanitized_context_refs, "sanitized context refs")
        return self


class ArtifactLifecycleAction(TimestampedModel):
    id: str
    action_type: ArtifactLifecycleOperation
    artifact_ref: Ref
    lifecycle_state_ref: Ref
    retention_policy_ref: Ref
    privacy_policy_ref: Ref
    legal_hold_ref: Ref | None = None
    legal_hold_active: bool = False
    projection_cleanup_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    command_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_artifact_lifecycle_action(self) -> ArtifactLifecycleAction:
        if not self.artifact_ref or not self.lifecycle_state_ref:
            raise ValueError("artifact lifecycle action requires artifact and lifecycle refs")
        if not self.retention_policy_ref or not self.privacy_policy_ref:
            raise ValueError("artifact lifecycle action requires retention and privacy refs")
        if self.action_type == ArtifactLifecycleOperation.DELETE and self.legal_hold_active:
            raise ValueError("delete is blocked while legal hold is active")
        if not self.projection_cleanup_refs:
            raise ValueError("artifact lifecycle action requires projection cleanup refs")
        if not self.policy_decision_refs or not self.command_refs or not self.event_refs:
            raise ValueError("artifact lifecycle action requires policy, command, and event refs")
        if self.action_type in {
            ArtifactLifecycleOperation.REDACT,
            ArtifactLifecycleOperation.TOMBSTONE,
            ArtifactLifecycleOperation.DELETE,
            ArtifactLifecycleOperation.LEGAL_HOLD,
            ArtifactLifecycleOperation.RELEASE_LEGAL_HOLD,
        } and not self.approval_decision_refs:
            raise ValueError("side-effecting lifecycle action requires approval refs")
        if not self.outbox_refs:
            raise ValueError("artifact lifecycle action requires outbox refs")
        return self


class ProjectionCleanupRecord(TimestampedModel):
    id: str
    lifecycle_action_ref: Ref
    affected_projection_refs: list[Ref] = Field(default_factory=list)
    cleanup_event_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_projection_cleanup_record(self) -> ProjectionCleanupRecord:
        if not self.lifecycle_action_ref:
            raise ValueError("projection cleanup requires lifecycle action ref")
        if not self.affected_projection_refs or not self.cleanup_event_refs:
            raise ValueError("projection cleanup requires affected projection and event refs")
        if not self.projection_watermark_refs:
            raise ValueError("projection cleanup requires watermark refs")
        if not self.policy_decision_refs:
            raise ValueError("projection cleanup requires policy refs")
        return self


class SecurityPrivacyReport(TimestampedModel):
    id: str
    run_ref: Ref
    security_policy_check_refs: list[Ref] = Field(default_factory=list)
    credential_use_audit_refs: list[Ref] = Field(default_factory=list)
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    artifact_lifecycle_action_refs: list[Ref] = Field(default_factory=list)
    projection_cleanup_refs: list[Ref] = Field(default_factory=list)
    redacted_replay_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    leakage_count: int = 0
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    unsafe_action_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_security_privacy_report(self) -> SecurityPrivacyReport:
        if self.leakage_count < 0:
            raise ValueError("leakage count must be non-negative")
        if self.result == CompletenessResult.PASS:
            required = {
                "security_policy_check_refs": self.security_policy_check_refs,
                "credential_use_audit_refs": self.credential_use_audit_refs,
                "prompt_taint_boundary_refs": self.prompt_taint_boundary_refs,
                "artifact_lifecycle_action_refs": self.artifact_lifecycle_action_refs,
                "projection_cleanup_refs": self.projection_cleanup_refs,
                "redacted_replay_refs": self.redacted_replay_refs,
                "observability_report_refs": self.observability_report_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "failure_record_refs": self.failure_record_refs,
                "recovery_action_refs": self.recovery_action_refs,
                "redaction_map_refs": self.redaction_map_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.missing_ref_fields
                or self.contract_only_refs
                or self.leakage_count != 0
                or self.raw_secret_leak_refs
                or self.unsafe_action_refs
            ):
                raise ValueError(f"passing security privacy report missing refs: {missing}")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_ref_fields):
                raise ValueError("needs-review security privacy report requires review refs")
        elif not (
            self.failure_record_refs
            or self.raw_secret_leak_refs
            or self.unsafe_action_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed security privacy report requires failure details")
        return self


class SecurityPrivacyFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: SecurityPrivacyFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> SecurityPrivacyFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("security privacy fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative security privacy fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
