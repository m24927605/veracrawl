"""Runtime objective, plan, run, snapshot, and completion gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    ObjectiveStatus,
    PlanStatus,
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
