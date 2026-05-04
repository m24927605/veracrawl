"""Production-grade crawler closure contracts."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult


class ProductionSourceProfile(TimestampedModel):
    id: str
    site_name: str
    allowed_origin: str
    entry_point_url: str
    discovery_methods: list[str] = Field(default_factory=list)
    required_evidence_types: list[str] = Field(default_factory=list)
    robots_policy_ref: Ref
    scope_policy_ref: Ref
    authorized_source_ref: Ref | None = None
    browser_required: bool = False
    official_api_available: bool = False
    source_limited: bool = False

    @model_validator(mode="after")
    def validate_source_profile(self) -> ProductionSourceProfile:
        if not self.allowed_origin.startswith(("http://", "https://")):
            raise ValueError("allowed_origin must be http(s)")
        if not self.entry_point_url.startswith(self.allowed_origin):
            raise ValueError("entry_point_url must stay inside allowed_origin")
        if not self.discovery_methods:
            raise ValueError("source profile requires discovery methods")
        if not self.required_evidence_types:
            raise ValueError("source profile requires evidence types")
        return self


class CrawlBound(TimestampedModel):
    id: str
    max_depth: int = 3
    max_pages: int = 50
    max_runtime_ms: int = 120000
    rate_limit_per_minute: int = 60
    browser_budget_ms: int = 30000

    @model_validator(mode="after")
    def validate_bounds(self) -> CrawlBound:
        for name, value in {
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "max_runtime_ms": self.max_runtime_ms,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "browser_budget_ms": self.browser_budget_ms,
        }.items():
            if value < 1:
                raise ValueError(f"{name} must be positive")
        return self


class ProductionGradeClosureManifest(TimestampedModel):
    id: str
    scenario: str
    gate_type: str
    profile_refs: list[str] = Field(default_factory=list)
    objective: str = ""
    source_profiles: list[ProductionSourceProfile] = Field(default_factory=list)
    crawl_bound: CrawlBound
    required_capability_refs: list[Ref] = Field(default_factory=list)
    input_report_refs: list[Ref] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_manifest(self) -> ProductionGradeClosureManifest:
        if "production" not in self.profile_refs:
            raise ValueError("production-grade fixture must support production profile")
        if self.gate_type not in {
            "discovery_planning",
            "acquisition_escalation",
            "authorized_source_access",
            "deep_crawl_production",
            "extraction_quality",
            "operations_reliability",
            "production_grade_release",
        }:
            raise ValueError("unsupported production-grade gate_type")
        if self.gate_type != "production_grade_release" and not self.source_profiles:
            raise ValueError("non-release production-grade gates require source profiles")
        if not self.objective:
            raise ValueError("production-grade fixture requires objective")
        return self


class CrawlDiscoveryPlan(TimestampedModel):
    id: str
    fixture_id: str
    objective_text: str
    source_profile_refs: list[Ref] = Field(default_factory=list)
    entry_point_refs: list[Ref] = Field(default_factory=list)
    crawl_bound_ref: Ref
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)
    approval_decision_ref: Ref
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_plan(self) -> CrawlDiscoveryPlan:
        if self.completion_result == CompletenessResult.PASS:
            _require_refs(
                self,
                {
                    "source_profile_refs": self.source_profile_refs,
                    "entry_point_refs": self.entry_point_refs,
                    "crawl_bound_ref": self.crawl_bound_ref,
                    "evidence_requirement_refs": self.evidence_requirement_refs,
                    "approval_decision_ref": self.approval_decision_ref,
                    "model_call_trace_refs": self.model_call_trace_refs,
                    "agent_action_trace_refs": self.agent_action_trace_refs,
                    "tool_call_trace_refs": self.tool_call_trace_refs,
                    "context_bundle_trace_refs": self.context_bundle_trace_refs,
                    "policy_decision_refs": self.policy_decision_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                },
            )
        return self


class DiscoveryEntryPoint(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    url: str
    discovery_method: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_entry_point(self) -> DiscoveryEntryPoint:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("discovery entry point URL must be http(s)")
        if not self.discovery_method:
            raise ValueError("discovery entry point requires method")
        if self.completion_result == CompletenessResult.PASS:
            _require_refs(
                self,
                {
                    "source_profile_ref": self.source_profile_ref,
                    "policy_decision_refs": self.policy_decision_refs,
                    "model_call_trace_refs": self.model_call_trace_refs,
                    "agent_action_trace_refs": self.agent_action_trace_refs,
                    "tool_call_trace_refs": self.tool_call_trace_refs,
                    "context_bundle_trace_refs": self.context_bundle_trace_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                },
            )
        return self


class CandidateSourceTarget(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    site_name: str
    allowed_origin: str
    entry_point_refs: list[Ref] = Field(default_factory=list)
    discovery_method_refs: list[Ref] = Field(default_factory=list)
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)
    crawl_bound_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_candidate_source_target(self) -> CandidateSourceTarget:
        if not self.allowed_origin.startswith(("http://", "https://")):
            raise ValueError("candidate source origin must be http(s)")
        if self.completion_result == CompletenessResult.PASS:
            _require_refs(
                self,
                {
                    "source_profile_ref": self.source_profile_ref,
                    "entry_point_refs": self.entry_point_refs,
                    "discovery_method_refs": self.discovery_method_refs,
                    "evidence_requirement_refs": self.evidence_requirement_refs,
                    "crawl_bound_ref": self.crawl_bound_ref,
                    "policy_decision_refs": self.policy_decision_refs,
                    "model_call_trace_refs": self.model_call_trace_refs,
                    "agent_action_trace_refs": self.agent_action_trace_refs,
                    "tool_call_trace_refs": self.tool_call_trace_refs,
                    "context_bundle_trace_refs": self.context_bundle_trace_refs,
                    "command_record_refs": self.command_record_refs,
                    "event_cursor_refs": self.event_cursor_refs,
                    "outbox_refs": self.outbox_refs,
                    "replay_bundle_ref": self.replay_bundle_ref,
                },
            )
        return self


class DiscoveryApprovalDecision(TimestampedModel):
    id: str
    fixture_id: str
    discovery_plan_ref: Ref
    approved: bool
    candidate_source_target_refs: list[Ref] = Field(default_factory=list)
    approval_policy_refs: list[Ref] = Field(default_factory=list)
    rejection_reason: str | None = None
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_approval_decision(self) -> DiscoveryApprovalDecision:
        _require_refs(
            self,
            {
                "discovery_plan_ref": self.discovery_plan_ref,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        if self.approved:
            _require_refs(
                self,
                {
                    "candidate_source_target_refs": self.candidate_source_target_refs,
                    "approval_policy_refs": self.approval_policy_refs,
                },
            )
        elif not self.rejection_reason:
            raise ValueError("rejected discovery approval requires rejection reason")
        return self


class AcquisitionAttemptRecord(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    acquisition_mode: str
    evidence_found: bool
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    source_limitation_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_attempt(self) -> AcquisitionAttemptRecord:
        _require_refs(
            self,
            {
                "source_profile_ref": self.source_profile_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        if self.evidence_found:
            _require_refs(
                self,
                {
                    "artifact_refs": self.artifact_refs,
                    "content_hash_refs": self.content_hash_refs,
                    "source_anchor_refs": self.source_anchor_refs,
                },
            )
        elif not self.source_limitation_ref:
            raise ValueError("missing evidence acquisition attempt requires limitation ref")
        return self


class AuthorizedSourceAccessRecord(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    access_kind: str
    credential_grant_ref: Ref
    credential_audit_ref: Ref
    redacted_artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_authorized_record(self) -> AuthorizedSourceAccessRecord:
        _require_refs(
            self,
            {
                "credential_grant_ref": self.credential_grant_ref,
                "credential_audit_ref": self.credential_audit_ref,
                "redacted_artifact_refs": self.redacted_artifact_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "content_hash_refs": self.content_hash_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        return self


class ProductionGateReport(TimestampedModel):
    id: str
    fixture_id: str
    gate_type: str
    run_ref: Ref
    capability_refs: list[Ref] = Field(default_factory=list)
    discovery_plan_refs: list[Ref] = Field(default_factory=list)
    acquisition_attempt_refs: list[Ref] = Field(default_factory=list)
    authorized_source_refs: list[Ref] = Field(default_factory=list)
    lower_gate_report_refs: list[Ref] = Field(default_factory=list)
    source_profile_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    release_blocker_refs: list[Ref] = Field(default_factory=list)
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self) -> ProductionGateReport:
        required = {
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_refs": self.replay_bundle_refs,
        }
        if self.completion_result == CompletenessResult.PASS:
            _require_refs(self, required)
            if self.release_blocker_refs:
                raise ValueError("passing production gate cannot include release blockers")
            if self.gate_type != "production_grade_release" and not self.source_profile_refs:
                raise ValueError("passing non-release production gate requires source profiles")
            if self.gate_type == "production_grade_release":
                if len(self.lower_gate_report_refs) < 6:
                    raise ValueError("production-grade release requires lower gate reports")
                if not self.capability_refs:
                    raise ValueError("production-grade release requires capability refs")
        else:
            if not self.release_blocker_refs or not self.diagnostics:
                raise ValueError("non-pass production gate requires blockers and diagnostics")
        return self


class ReleaseBlocker(TimestampedModel):
    id: str
    fixture_id: str
    blocker_type: str
    blocked_ref: Ref
    diagnostic: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_release_blocker(self) -> ReleaseBlocker:
        if not self.blocker_type or not self.diagnostic:
            raise ValueError("release blocker requires type and diagnostic")
        _require_refs(
            self,
            {
                "blocked_ref": self.blocked_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        return self


class FalseReadyGuard(TimestampedModel):
    id: str
    fixture_id: str
    guard_type: str
    checked_ref: Ref
    triggered: bool
    release_blocker_ref: Ref | None = None
    diagnostic_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_false_ready_guard(self) -> FalseReadyGuard:
        _require_refs(
            self,
            {
                "checked_ref": self.checked_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        if self.triggered and not self.release_blocker_ref:
            raise ValueError("triggered false-ready guard requires release blocker")
        return self


class ProductionGradeCapabilityMatrix(TimestampedModel):
    id: str
    fixture_id: str
    release_gate_report_ref: Ref
    required_gate_types: list[str] = Field(default_factory=list)
    passing_gate_report_refs: list[Ref] = Field(default_factory=list)
    missing_gate_types: list[str] = Field(default_factory=list)
    non_passing_gate_report_refs: list[Ref] = Field(default_factory=list)
    false_ready_guard_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_capability_matrix(self) -> ProductionGradeCapabilityMatrix:
        _require_refs(
            self,
            {
                "release_gate_report_ref": self.release_gate_report_ref,
                "required_gate_types": self.required_gate_types,
                "false_ready_guard_refs": self.false_ready_guard_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        if self.completion_result == CompletenessResult.PASS:
            if self.missing_gate_types or self.non_passing_gate_report_refs:
                raise ValueError("passing capability matrix cannot have missing gates")
            if len(self.passing_gate_report_refs) < len(self.required_gate_types):
                raise ValueError("passing capability matrix requires all gate reports")
        return self


class ReleaseDecision(TimestampedModel):
    id: str
    fixture_id: str
    release_gate_report_ref: Ref
    capability_matrix_ref: Ref
    decision: str
    release_blocker_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_release_decision(self) -> ReleaseDecision:
        if self.decision not in {"pass", "blocked"}:
            raise ValueError("release decision must be pass or blocked")
        _require_refs(
            self,
            {
                "release_gate_report_ref": self.release_gate_report_ref,
                "capability_matrix_ref": self.capability_matrix_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            },
        )
        if self.decision == "pass" and self.release_blocker_refs:
            raise ValueError("passing release decision cannot include blockers")
        if self.decision == "blocked" and (
            not self.release_blocker_refs or not self.diagnostics
        ):
            raise ValueError("blocked release decision requires blockers and diagnostics")
        return self


class ProductionGradeReleaseReport(TimestampedModel):
    id: str
    fixture_id: str
    release_gate_report_ref: Ref
    capability_matrix_ref: Ref
    release_decision_ref: Ref
    false_ready_guard_refs: list[Ref] = Field(default_factory=list)
    lower_gate_report_refs: list[Ref] = Field(default_factory=list)
    release_blocker_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_release_report(self) -> ProductionGradeReleaseReport:
        _require_refs(
            self,
            {
                "release_gate_report_ref": self.release_gate_report_ref,
                "capability_matrix_ref": self.capability_matrix_ref,
                "release_decision_ref": self.release_decision_ref,
                "false_ready_guard_refs": self.false_ready_guard_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            },
        )
        if self.completion_result == CompletenessResult.PASS:
            if len(self.lower_gate_report_refs) < 6:
                raise ValueError("passing release report requires lower gate reports")
            if self.release_blocker_refs:
                raise ValueError("passing release report cannot include blockers")
        elif not self.release_blocker_refs or not self.diagnostics:
            raise ValueError("non-pass release report requires blockers and diagnostics")
        return self


def _require_refs(model: TimestampedModel, refs: Mapping[str, object]) -> None:
    missing = [name for name, value in refs.items() if not value]
    if missing:
        raise ValueError(f"{model.__class__.__name__} missing refs: {missing}")
