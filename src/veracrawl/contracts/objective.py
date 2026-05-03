"""Runtime objective, plan, run, snapshot, and completion gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ObjectiveStatus,
    PlanStatus,
    ProductionPersistenceFailureType,
    ProductionRunControlFailureType,
    RunLifecycleAction,
    RunStatus,
    RuntimeCompletionGateType,
    RuntimeGateStatus,
)


class CrawlObjective(TimestampedModel):
    id: str
    project_ref: Ref
    site_scope_refs: list[Ref] = Field(default_factory=list)
    objective_text_ref: Ref
    target_schema_refs: list[Ref] = Field(default_factory=list)
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)
    freshness_policy_ref: Ref
    source_policy_refs: list[Ref] = Field(default_factory=list)
    publication_policy_refs: list[Ref] = Field(default_factory=list)
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    created_by_ref: Ref

    @model_validator(mode="after")
    def validate_approval_requirements(self) -> CrawlObjective:
        if self.status == ObjectiveStatus.APPROVED:
            if not self.site_scope_refs or not self.source_policy_refs:
                raise ValueError("approved objective requires scope and source policy refs")
            if not self.target_schema_refs or not self.evidence_requirement_refs:
                raise ValueError("approved objective requires schema and evidence refs")
        return self


class CrawlPlan(TimestampedModel):
    id: str
    objective_ref: Ref
    plan_version: str
    adapter_plan: list[dict[str, object]] = Field(default_factory=list)
    seed_refs: list[Ref] = Field(default_factory=list)
    assumption_refs: list[Ref] = Field(default_factory=list)
    alternative_refs: list[Ref] = Field(default_factory=list)
    risk_refs: list[Ref] = Field(default_factory=list)
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)
    budget_ref: Ref
    approval_decision_ref: Ref | None = None
    status: PlanStatus = PlanStatus.PROPOSED

    @model_validator(mode="after")
    def validate_approved_plan(self) -> CrawlPlan:
        if self.status == PlanStatus.APPROVED:
            if not self.approval_decision_ref:
                raise ValueError("approved plan requires approval_decision_ref")
            if not self.adapter_plan:
                raise ValueError("approved plan requires adapter_plan")
        return self


class RuntimeCompletionGate(TimestampedModel):
    id: str
    run_ref: Ref
    gate_type: RuntimeCompletionGateType
    status: RuntimeGateStatus = RuntimeGateStatus.PENDING
    required_ref_fields: list[str] = Field(default_factory=list)
    present_ref_fields: list[str] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    blocking_reason_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_gate(self) -> RuntimeCompletionGate:
        if self.status == RuntimeGateStatus.PASS and self.missing_ref_fields:
            raise ValueError("passing completion gate cannot have missing refs")
        if self.status in {
            RuntimeGateStatus.FAIL,
            RuntimeGateStatus.BLOCKED,
            RuntimeGateStatus.CONFLICT,
            RuntimeGateStatus.NEEDS_REVIEW,
        } and not (self.missing_ref_fields or self.blocking_reason_refs):
            raise ValueError("non-pass completion gate requires missing refs or reasons")
        return self


class CrawlRun(TimestampedModel):
    id: str
    objective_ref: Ref
    plan_ref: Ref
    run_plan_snapshot_ref: Ref
    status: RunStatus = RunStatus.QUEUED
    completion_gate_refs: list[Ref] = Field(default_factory=list)
    policy_snapshot_ref: Ref
    budget_ref: Ref
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_terminal_state(self) -> CrawlRun:
        if self.status == RunStatus.FAILED and not self.failure_record_refs:
            raise ValueError("failed run requires failure_record_refs")
        return self


class RunPlanSnapshot(TimestampedModel):
    id: str
    objective_ref: Ref
    plan_ref: Ref
    plan_hash: str
    policy_refs: list[Ref] = Field(default_factory=list)
    schema_refs: list[Ref] = Field(default_factory=list)
    adapter_spec_refs: list[Ref] = Field(default_factory=list)
    tool_refs: list[Ref] = Field(default_factory=list)
    model_refs: list[Ref] = Field(default_factory=list)
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)
    replay_config_ref: Ref

    @model_validator(mode="after")
    def validate_snapshot_refs(self) -> RunPlanSnapshot:
        if not self.plan_hash:
            raise ValueError("run plan snapshot requires plan_hash")
        if not self.policy_refs or not self.schema_refs or not self.adapter_spec_refs:
            raise ValueError("run plan snapshot requires policy, schema, and adapter refs")
        return self


class ProductionProject(TimestampedModel):
    id: str
    owner_ref: Ref
    project_policy_refs: list[Ref] = Field(default_factory=list)
    default_budget_ref: Ref
    status: str = "active"

    @model_validator(mode="after")
    def validate_project(self) -> ProductionProject:
        if self.status != "active":
            raise ValueError("production project must be active for run control")
        if not (self.owner_ref and self.project_policy_refs and self.default_budget_ref):
            raise ValueError("production project requires owner, policy, and budget refs")
        return self


class ProductionSiteScope(TimestampedModel):
    id: str
    project_ref: Ref
    allowed_scope_refs: list[Ref] = Field(default_factory=list)
    source_policy_refs: list[Ref] = Field(default_factory=list)
    robots_policy_ref: Ref
    egress_policy_ref: Ref
    credential_policy_ref: Ref | None = None
    status: str = "active"

    @model_validator(mode="after")
    def validate_site_scope(self) -> ProductionSiteScope:
        if self.status != "active":
            raise ValueError("production site scope must be active")
        if not self.allowed_scope_refs:
            raise ValueError("production site scope requires allowed scope refs")
        if not (self.source_policy_refs and self.robots_policy_ref and self.egress_policy_ref):
            raise ValueError(
                "production site scope requires source, robots, and egress policy refs"
            )
        return self


class RunBudget(TimestampedModel):
    id: str
    project_ref: Ref
    crawl_limit_refs: list[Ref] = Field(default_factory=list)
    max_pages: int
    max_depth: int
    max_runtime_seconds: int
    max_browser_minutes: int = 0
    max_model_tokens: int = 0
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_budget(self) -> RunBudget:
        numeric_fields = {
            "max_pages": self.max_pages,
            "max_depth": self.max_depth,
            "max_runtime_seconds": self.max_runtime_seconds,
        }
        invalid = [field for field, value in numeric_fields.items() if value <= 0]
        if invalid:
            raise ValueError(f"run budget requires positive limits: {invalid}")
        if self.max_browser_minutes < 0 or self.max_model_tokens < 0:
            raise ValueError("run budget optional limits cannot be negative")
        if not (self.crawl_limit_refs and self.policy_decision_refs):
            raise ValueError("run budget requires limit and policy decision refs")
        return self


class RunPolicySnapshot(TimestampedModel):
    id: str
    run_ref: Ref
    project_ref: Ref
    site_scope_ref: Ref
    source_policy_refs: list[Ref] = Field(default_factory=list)
    publication_policy_refs: list[Ref] = Field(default_factory=list)
    privacy_policy_ref: Ref
    egress_policy_ref: Ref
    credential_policy_ref: Ref | None = None
    prompt_taint_policy_ref: Ref
    budget_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_policy_snapshot(self) -> RunPolicySnapshot:
        required: dict[str, object] = {
            "source_policy_refs": self.source_policy_refs,
            "publication_policy_refs": self.publication_policy_refs,
            "privacy_policy_ref": self.privacy_policy_ref,
            "egress_policy_ref": self.egress_policy_ref,
            "prompt_taint_policy_ref": self.prompt_taint_policy_ref,
            "budget_ref": self.budget_ref,
            "policy_decision_refs": self.policy_decision_refs,
        }
        missing = [field for field, value in required.items() if not value]
        if missing:
            raise ValueError(f"run policy snapshot missing refs: {missing}")
        return self


class RunApprovalRecord(TimestampedModel):
    id: str
    objective_ref: Ref
    plan_ref: Ref
    actor_ref: Ref
    approved: bool
    approval_decision_ref: Ref | None = None
    rejection_reason_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_approval_record(self) -> RunApprovalRecord:
        if self.approved:
            if not (self.approval_decision_ref and self.policy_decision_refs):
                raise ValueError("approved run approval requires decision and policy refs")
            if self.rejection_reason_refs:
                raise ValueError("approved run approval cannot carry rejection refs")
        elif not self.rejection_reason_refs:
            raise ValueError("rejected run approval requires rejection refs")
        return self


class RunLifecycleRecord(TimestampedModel):
    id: str
    run_ref: Ref
    action: RunLifecycleAction
    status_before: RunStatus
    status_after: RunStatus
    command_result_ref: Ref
    event_ref: Ref
    actor_ref: Ref
    policy_snapshot_ref: Ref
    budget_ref: Ref
    approval_record_ref: Ref | None = None
    failure_record_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lifecycle_record(self) -> RunLifecycleRecord:
        allowed: dict[RunLifecycleAction, set[tuple[RunStatus, RunStatus]]] = {
            RunLifecycleAction.START_RUN: {
                (RunStatus.QUEUED, RunStatus.RUNNING),
                (RunStatus.RUNNING, RunStatus.RUNNING),
            },
            RunLifecycleAction.PAUSE_RUN: {(RunStatus.RUNNING, RunStatus.PAUSED)},
            RunLifecycleAction.RESUME_RUN: {(RunStatus.PAUSED, RunStatus.RUNNING)},
            RunLifecycleAction.CANCEL_RUN: {
                (RunStatus.QUEUED, RunStatus.CANCELLED),
                (RunStatus.RUNNING, RunStatus.CANCELLED),
                (RunStatus.PAUSED, RunStatus.CANCELLED),
            },
            RunLifecycleAction.FAIL_RUN: {
                (RunStatus.QUEUED, RunStatus.FAILED),
                (RunStatus.RUNNING, RunStatus.FAILED),
                (RunStatus.PAUSED, RunStatus.FAILED),
            },
            RunLifecycleAction.COMPLETE_RUN: {(RunStatus.RUNNING, RunStatus.COMPLETED)},
            RunLifecycleAction.CREATE_OBJECTIVE: set(),
            RunLifecycleAction.APPROVE_PLAN: set(),
        }
        if (self.status_before, self.status_after) not in allowed[self.action]:
            raise ValueError(
                "invalid run lifecycle transition "
                f"{self.action.value}: {self.status_before.value}->{self.status_after.value}"
            )
        if self.action == RunLifecycleAction.FAIL_RUN and not self.failure_record_refs:
            raise ValueError("failed run lifecycle requires failure refs")
        if not self.replay_refs:
            raise ValueError("run lifecycle record requires replay refs")
        return self


class ProductionRunControlReport(TimestampedModel):
    id: str
    fixture_id: str
    project_ref: Ref
    site_scope_ref: Ref
    objective_ref: Ref
    plan_ref: Ref
    run_ref: Ref
    status: RunStatus
    completion_result: CompletenessResult
    operator_status: str
    command_result_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_refs: list[Ref] = Field(default_factory=list)
    budget_ref: Ref | None = None
    policy_snapshot_ref: Ref | None = None
    lifecycle_record_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)
    failure_type: ProductionRunControlFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_run_control_report(self) -> ProductionRunControlReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "command_result_refs": self.command_result_refs,
                "event_refs": self.event_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "approval_refs": self.approval_refs,
                "budget_ref": self.budget_ref,
                "policy_snapshot_ref": self.policy_snapshot_ref,
                "lifecycle_record_refs": self.lifecycle_record_refs,
                "replay_refs": self.replay_refs,
            }
            missing = [field for field, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing run-control report missing refs: {missing}")
        elif not (self.failure_type and self.failure_report_refs and self.diagnostics):
            raise ValueError("failing run-control report requires typed diagnostics")
        return self


class ProductionRunControlFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_status: RunStatus
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ProductionRunControlFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_run_control_fixture(self) -> ProductionRunControlFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("production run-control fixture must support target profile")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative production run-control fixture requires failure type")
        return self


class ProductionPersistenceRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    project_ref: Ref
    site_scope_ref: Ref
    objective_ref: Ref
    plan_ref: Ref
    run_control_report_ref: Ref | None = None
    status: RunStatus
    completion_result: CompletenessResult
    operator_status: str
    adapter_ref: Ref | None = None
    transaction_ref: Ref | None = None
    canonical_state_refs: list[Ref] = Field(default_factory=list)
    run_control_command_result_refs: list[Ref] = Field(default_factory=list)
    persistence_command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    event_cursor_ref: Ref | None = None
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ProductionPersistenceFailureType | None = None
    duplicate_deduped: bool = False
    reloaded: bool = False
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_production_persistence_report(self) -> ProductionPersistenceRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "adapter_ref": self.adapter_ref,
                "transaction_ref": self.transaction_ref,
                "run_control_report_ref": self.run_control_report_ref,
                "canonical_state_refs": self.canonical_state_refs,
                "run_control_command_result_refs": self.run_control_command_result_refs,
                "persistence_command_record_refs": self.persistence_command_record_refs,
                "idempotency_record_refs": self.idempotency_record_refs,
                "event_refs": self.event_refs,
                "event_cursor_ref": self.event_cursor_ref,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "queue_operation_refs": self.queue_operation_refs,
                "lease_refs": self.lease_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [field for field, value in required.items() if not value]
            if missing or self.missing_ref_fields or self.failure_type:
                raise ValueError(
                    f"passing production persistence report missing refs: {missing}"
                )
            if not self.reloaded:
                raise ValueError("passing production persistence report requires adapter reopen")
        elif not (self.failure_type and self.failure_record_refs and self.missing_ref_fields):
            raise ValueError("non-pass production persistence report requires typed failures")
        return self


class ProductionPersistenceFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ProductionPersistenceFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_production_persistence_fixture(
        self,
    ) -> ProductionPersistenceFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("production persistence fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("production persistence fixture requires ref expectations")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative production persistence fixture requires failure type")
        return self
