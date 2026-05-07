"""Security, privacy, and lifecycle gate contracts."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    ArtifactLifecycleOperation,
    CompletenessResult,
    CredentialDeliveryMode,
    CredentialedSessionFailureType,
    SecurityActionSurface,
    SecurityCheckResult,
    SecurityPrivacyFailureType,
)

_ALLOWED_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_valid_origin(value: str) -> bool:
    """Origin-only URL: ``scheme://host[:port]``.

    Stricter than ``_is_http_url``: rejects URLs that carry a path
    other than ``/``, a query, a fragment, or userinfo. This is the
    shape ``StrictAllowlistScope`` (Phase 2) needs so origin checks
    don't accidentally match arbitrary URLs that share a prefix —
    the route policy is expressed separately via
    ``allowed_route_patterns``.
    """
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    if parsed.path not in ("", "/"):
        return False
    if parsed.query or parsed.fragment:
        return False
    if parsed.username or parsed.password:
        return False
    return True


def _is_valid_http_status(value: int) -> bool:
    return 100 <= value <= 599


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


def _value_looks_like_secret(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SENSITIVE_MARKERS)


def _ensure_no_sensitive_values(values: list[str], field_name: str) -> None:
    for value in values:
        if _value_looks_like_secret(value):
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


class CredentialedSessionRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    live_http_acquisition_report_ref: Ref | None = None
    browser_snapshot_runtime_report_ref: Ref | None = None
    credential_scope_refs: list[Ref] = Field(default_factory=list)
    authorized_origin_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    credential_use_audit_refs: list[Ref] = Field(default_factory=list)
    session_adapter_result_refs: list[Ref] = Field(default_factory=list)
    session_state_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    redacted_artifact_refs: list[Ref] = Field(default_factory=list)
    redacted_replay_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    adapter_native_state_canonical_refs: list[Ref] = Field(default_factory=list)
    failure_type: CredentialedSessionFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_credentialed_session_report(self) -> CredentialedSessionRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_http_acquisition_report_ref": self.live_http_acquisition_report_ref,
                "browser_snapshot_runtime_report_ref": self.browser_snapshot_runtime_report_ref,
                "credential_scope_refs": self.credential_scope_refs,
                "authorized_origin_refs": self.authorized_origin_refs,
                "approval_decision_refs": self.approval_decision_refs,
                "credential_use_audit_refs": self.credential_use_audit_refs,
                "session_adapter_result_refs": self.session_adapter_result_refs,
                "session_state_refs": self.session_state_refs,
                "redaction_map_refs": self.redaction_map_refs,
                "redacted_artifact_refs": self.redacted_artifact_refs,
                "redacted_replay_refs": self.redacted_replay_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.raw_secret_leak_refs
                or self.adapter_native_state_canonical_refs
            ):
                raise ValueError(f"passing credentialed session report missing refs: {missing}")
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.raw_secret_leak_refs
                or self.adapter_native_state_canonical_refs
            )
        ):
            raise ValueError("failed credentialed session report requires typed diagnostics")
        return self


class CredentialedSessionFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str = "/browser"
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: CredentialedSessionFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_credentialed_session_fixture(self) -> CredentialedSessionFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("credentialed session fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("credentialed session fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative credentialed session fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative credentialed session fixture requires failure type")
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
        if (
            self.action_type
            in {
                ArtifactLifecycleOperation.REDACT,
                ArtifactLifecycleOperation.TOMBSTONE,
                ArtifactLifecycleOperation.DELETE,
                ArtifactLifecycleOperation.LEGAL_HOLD,
                ArtifactLifecycleOperation.RELEASE_LEGAL_HOLD,
            }
            and not self.approval_decision_refs
        ):
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


# ---------------------------------------------------------------------------
# v2 contracts (production-authorized-source-crawler design §3.5).
#
# Phase 2 ships the authorized session subsystem the V1 implementation
# of ``docs/09 §Capability Areas`` missed. ``CredentialScope`` declares
# *where* a credential is allowed to flow (origin / route / method /
# expiry); the Phase 2 ``StrictAllowlistScope`` policy enforces the
# scope at request build time. ``CredentialUseRecord`` is the per-use
# outbox row the ``AuthorizedSessionAdapter`` writes whenever it
# attaches a credential, providing the audit trail the
# ``CredentialUseAudit`` aggregate (above) summarises.
#
# Charter rule (``docs/09:116``): neither contract may carry the
# credential value itself — only a *handle* into the credential
# vault. Producers that violate this should fail validation in the
# vault adapter (Phase 2 step 2.1), not here; these contracts are
# the data shape, not the runtime enforcement point.
# ---------------------------------------------------------------------------


class CredentialScope(TimestampedModel):
    """Scope spec the Phase 2 ``StrictAllowlistScope`` enforces.

    ``credential_handle_ref`` is an opaque reference into the
    credential vault — never the secret itself. The orchestrator
    builds requests against the scope; the
    ``StrictAllowlistScope`` policy rejects any request whose
    origin, route pattern, or method falls outside the allowlist.
    ``expires_at`` is required to be timezone-aware (replay
    determinism) and in the future at construction time (a
    pre-expired scope admits no requests and is almost certainly
    a wiring bug).
    """

    id: str
    credential_handle_ref: Ref
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_route_patterns: list[str] = Field(default_factory=list)
    allowed_methods: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> CredentialScope:
        if not self.credential_handle_ref.strip():
            raise ValueError("credential scope credential_handle_ref must be non-blank")
        if _value_looks_like_secret(self.credential_handle_ref):
            raise ValueError(
                "credential scope credential_handle_ref must be an opaque vault "
                "handle, not a credential value (matched a sensitive marker)"
            )
        if not self.allowed_origins:
            raise ValueError("credential scope requires at least one allowed origin")
        for origin in self.allowed_origins:
            if not _is_valid_origin(origin):
                raise ValueError(
                    "credential scope allowed origin must be a bare http(s) origin "
                    "(scheme://host[:port], no path/query/fragment/userinfo): "
                    f"{origin!r}"
                )
        if not self.allowed_route_patterns:
            raise ValueError(
                "credential scope requires at least one allowed_route_pattern; "
                "an origin-only scope would let StrictAllowlistScope admit any "
                "path under the origin"
            )
        for pattern in self.allowed_route_patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    f"credential scope allowed_route_pattern {pattern!r} is not a "
                    f"compilable regex: {exc.msg}"
                ) from exc
        if not self.allowed_methods:
            raise ValueError("credential scope requires at least one allowed method")
        for method in self.allowed_methods:
            if method != method.upper():
                raise ValueError(f"credential scope allowed method must be upper-case: {method!r}")
            if method not in _ALLOWED_HTTP_METHODS:
                raise ValueError(
                    f"credential scope allowed method {method!r} is not in the allowed set "
                    f"{sorted(_ALLOWED_HTTP_METHODS)}"
                )
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
                raise ValueError(
                    "credential scope expires_at must be timezone-aware for replay determinism"
                )
        # NOTE: deliberately do NOT reject already-past ``expires_at`` here.
        # Contracts validate shape, not time-of-day truth — a scope
        # serialized while valid must still be loadable after expiry so
        # replay, audit, and registry round-trips stay deterministic.
        # Runtime policy (``StrictAllowlistScope``, Phase 2 step 2.2)
        # decides whether an already-expired scope may be used at
        # request build time.
        return self


class CredentialUseRecord(TimestampedModel):
    """Per-use outbox row written by the ``AuthorizedSessionAdapter``.

    Records WHO was used (``credential_scope_ref``) for WHICH
    request (``request_url`` / ``request_method``), the response
    status (or None for transport failures, paired with an
    ``attempt_evidence_ref``), and WHEN. The ``CredentialUseAudit``
    (above) aggregates these records into the authorized-session
    audit at the end of a run.

    No credential value lives here — the producer must reference
    the credential by ``credential_scope_ref`` only.
    """

    id: str
    run_ref: Ref
    credential_scope_ref: Ref
    request_url: str
    request_method: str
    response_status: int | None = None
    timestamp_used: datetime
    attempt_evidence_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_use_record(self) -> CredentialUseRecord:
        if not _is_http_url(self.request_url):
            raise ValueError("credential use record request_url must be absolute http(s)")
        if not self.request_method.strip():
            raise ValueError("credential use record request_method must be non-blank")
        if self.response_status is not None and not _is_valid_http_status(self.response_status):
            raise ValueError("credential use record response_status must be valid HTTP")
        if self.response_status is None and self.attempt_evidence_ref is None:
            raise ValueError(
                "credential use record with no response_status (transport failure) requires "
                "attempt_evidence_ref so the audit trail can replay the failure"
            )
        if self.timestamp_used.tzinfo is None or self.timestamp_used.utcoffset() is None:
            raise ValueError("credential use record timestamp_used must be timezone-aware")
        return self
