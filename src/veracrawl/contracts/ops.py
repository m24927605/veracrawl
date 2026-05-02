"""Review, replay, and operations contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, utc_now
from veracrawl.contracts.enums import (
    CompletenessResult,
    DRRestoreFailureType,
    DRRestorePhase,
    DRRestorePhaseStatus,
    DRRestoreRunStatus,
    OpsDashboardType,
    OpsFailureType,
    OpsRecoveryStatus,
    OpsSeverity,
    RecoveryActionType,
    ReplayMode,
    ReviewItemStatus,
    ReviewItemType,
    ReviewPriority,
)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class ReviewItem(TimestampedModel):
    id: str
    run_id: str
    objective_id: str
    item_type: ReviewItemType
    input_refs: list[Ref] = Field(default_factory=list)
    reason: str
    priority: ReviewPriority
    status: ReviewItemStatus
    reviewer_id: str = "unassigned"
    decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_audit_refs: list[Ref] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("updated_at")
    @classmethod
    def require_updated_at_utc(cls, value: datetime) -> datetime:
        return _require_utc(value)

    @model_validator(mode="after")
    def validate_review_item(self) -> ReviewItem:
        if not self.input_refs:
            raise ValueError("review item requires input refs")
        if not self.reason:
            raise ValueError("review item requires reason")
        if not self.policy_decision_refs:
            raise ValueError("review item requires policy refs")
        if self.status in {
            ReviewItemStatus.ACCEPTED,
            ReviewItemStatus.REJECTED,
            ReviewItemStatus.RESOLVED,
        } and not self.decision_refs:
            raise ValueError("closed review item requires decision refs")
        return self


class ReplayAuditView(TimestampedModel):
    id: str
    run_id: str
    replay_bundle_ref: Ref
    replay_mode: ReplayMode
    replay_validation_report_ref: Ref
    command_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    artifact_hash_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    redaction_map_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    completeness_result: CompletenessResult

    @model_validator(mode="after")
    def validate_replay_audit_view(self) -> ReplayAuditView:
        if self.completeness_result == CompletenessResult.PASS:
            required = {
                "command_refs": self.command_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "artifact_hash_refs": self.artifact_hash_refs,
                "projection_watermark_refs": self.projection_watermark_refs,
                "policy_decision_refs": self.policy_decision_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing replay audit view missing refs: {missing}")
        elif not (self.failure_report_refs or self.missing_ref_fields):
            raise ValueError("non-pass replay audit view requires failure or missing refs")
        return self


class FailureRecord(TimestampedModel):
    id: str
    run_id: str
    failure_type: OpsFailureType
    failed_ref: Ref
    owner_service_ref: Ref
    severity: OpsSeverity
    retryable: bool
    orphan_artifact_refs: list[Ref] = Field(default_factory=list)
    partial_side_effect_refs: list[Ref] = Field(default_factory=list)
    dead_letter_reason: str = ""
    diagnostic_ref: Ref | None = None
    evidence_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_audit_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_failure_record(self) -> FailureRecord:
        if not self.failed_ref or not self.owner_service_ref:
            raise ValueError("failure record requires failed and owner refs")
        if not self.policy_decision_refs:
            raise ValueError("failure record requires policy refs")
        if self.failure_type == OpsFailureType.DEAD_LETTER and not self.dead_letter_reason:
            raise ValueError("dead letter failure requires reason")
        return self


class RecoveryAction(TimestampedModel):
    id: str
    failure_record_id: str
    action_type: RecoveryActionType
    command_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    status: OpsRecoveryStatus
    result_refs: list[Ref] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("updated_at")
    @classmethod
    def require_updated_at_utc(cls, value: datetime) -> datetime:
        return _require_utc(value)

    @model_validator(mode="after")
    def validate_recovery_action(self) -> RecoveryAction:
        if not self.failure_record_id:
            raise ValueError("recovery action requires failure record id")
        side_effecting = {
            RecoveryActionType.TOMBSTONE_ARTIFACT,
            RecoveryActionType.REDACT_ARTIFACT,
            RecoveryActionType.DELETE_ARTIFACT,
            RecoveryActionType.RELEASE_LEGAL_HOLD,
            RecoveryActionType.WITHDRAW_OUTPUT,
            RecoveryActionType.RECONCILE_EXPORT,
            RecoveryActionType.REBUILD_PROJECTION,
            RecoveryActionType.RERUN_MIGRATION,
            RecoveryActionType.RERUN_BACKFILL,
            RecoveryActionType.INVALIDATE_MEMORY,
            RecoveryActionType.QUARANTINE_TAINTED_CONTEXT,
            RecoveryActionType.PAUSE_SITE,
            RecoveryActionType.SCALE_WORKER_POOL,
            RecoveryActionType.RESTORE_FROM_BACKUP,
        }
        if self.action_type in side_effecting:
            if not self.policy_decision_refs or not self.approval_decision_refs:
                raise ValueError("side-effecting recovery requires policy and approval refs")
        if self.action_type not in {RecoveryActionType.REQUEST_REVIEW, RecoveryActionType.IGNORE}:
            if not self.command_refs:
                raise ValueError("executable recovery action requires command refs")
        if self.status == OpsRecoveryStatus.COMPLETED and not self.result_refs:
            raise ValueError("completed recovery action requires result refs")
        if self.status == OpsRecoveryStatus.FAILED and not self.result_refs:
            raise ValueError("failed recovery action requires failure result refs")
        return self


class DRRestorePlanPhase(TimestampedModel):
    phase_name: DRRestorePhase
    phase_order: int
    input_refs: list[Ref] = Field(default_factory=list)
    output_contract_refs: list[Ref] = Field(default_factory=list)
    validation_gate_refs: list[Ref] = Field(default_factory=list)
    rollback_behavior: str = "manual_review"

    @model_validator(mode="after")
    def validate_plan_phase(self) -> DRRestorePlanPhase:
        if self.phase_order < 1:
            raise ValueError("DR restore phase order must be positive")
        if not self.input_refs:
            raise ValueError("DR restore plan phase requires input refs")
        if not self.output_contract_refs:
            raise ValueError("DR restore plan phase requires output contract refs")
        if not self.validation_gate_refs:
            raise ValueError("DR restore plan phase requires validation gates")
        return self


class DRRestorePlan(TimestampedModel):
    id: str
    restore_scope_ref: Ref
    restore_point_ref: Ref
    backup_manifest_ref: Ref
    metadata_snapshot_ref: Ref
    artifact_snapshot_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    ordered_phases: list[DRRestorePlanPhase] = Field(default_factory=list)
    required_validation_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    approval_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dr_restore_plan(self) -> DRRestorePlan:
        if not self.artifact_snapshot_refs:
            raise ValueError("DR restore plan requires artifact snapshot refs")
        if not self.event_cursor_refs:
            raise ValueError("DR restore plan requires event cursor refs")
        if not self.policy_decision_refs:
            raise ValueError("DR restore plan requires policy refs")
        if not self.approval_decision_refs:
            raise ValueError("DR restore plan requires approval refs")
        required_phases = set(DRRestorePhase)
        present_phases = {phase.phase_name for phase in self.ordered_phases}
        if present_phases != required_phases:
            raise ValueError("DR restore plan must include every required phase exactly once")
        orders = [phase.phase_order for phase in self.ordered_phases]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            raise ValueError("DR restore plan phases must be strictly ordered")
        phase_gate_refs = {
            ref for phase in self.ordered_phases for ref in phase.validation_gate_refs
        }
        if not set(self.required_validation_gate_refs).issubset(phase_gate_refs):
            raise ValueError("DR restore plan required gates must be declared on phases")
        return self


class DRRestorePhaseResult(TimestampedModel):
    phase_name: DRRestorePhase
    status: DRRestorePhaseStatus
    input_refs: list[Ref] = Field(default_factory=list)
    output_refs: list[Ref] = Field(default_factory=list)
    validation_result_refs: list[Ref] = Field(default_factory=list)
    failure_record_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_phase_result(self) -> DRRestorePhaseResult:
        if self.status == DRRestorePhaseStatus.COMPLETED:
            if not self.output_refs or not self.validation_result_refs:
                raise ValueError("completed DR phase requires output and validation refs")
        if self.status == DRRestorePhaseStatus.FAILED and not self.failure_record_ref:
            raise ValueError("failed DR phase requires failure ref")
        return self


class DRRestoreRun(TimestampedModel):
    id: str
    dr_restore_plan_id: str
    restore_scope_ref: Ref
    phase_results: list[DRRestorePhaseResult] = Field(default_factory=list)
    current_phase: DRRestorePhase
    status: DRRestoreRunStatus
    emitted_event_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    unresolved_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("updated_at")
    @classmethod
    def require_updated_at_utc(cls, value: datetime) -> datetime:
        return _require_utc(value)

    @model_validator(mode="after")
    def validate_dr_restore_run(self) -> DRRestoreRun:
        if not self.dr_restore_plan_id:
            raise ValueError("DR restore run requires plan id")
        if not self.policy_decision_refs:
            raise ValueError("DR restore run requires policy refs")
        if self.status == DRRestoreRunStatus.COMPLETED:
            required_phases = set(DRRestorePhase)
            completed_phases = {
                result.phase_name
                for result in self.phase_results
                if result.status == DRRestorePhaseStatus.COMPLETED
            }
            if completed_phases != required_phases:
                raise ValueError("completed DR restore run requires all phases completed")
            if not self.emitted_event_refs:
                raise ValueError("completed DR restore run requires emitted event refs")
        if self.status == DRRestoreRunStatus.FAILED and not self.failure_record_refs:
            raise ValueError("failed DR restore run requires failure refs")
        if self.status == DRRestoreRunStatus.NEEDS_REVIEW and not self.unresolved_refs:
            raise ValueError("needs-review DR restore run requires unresolved refs")
        return self


class DRRestoreReport(TimestampedModel):
    id: str
    restore_scope_ref: Ref
    dr_restore_plan_id: str
    dr_restore_run_id: str
    restore_point_ref: Ref | None = None
    backup_manifest_ref: Ref | None = None
    metadata_restore_ref: Ref | None = None
    artifact_reachability_report_ref: Ref | None = None
    event_replay_report_ref: Ref | None = None
    projection_rebuild_job_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    queue_recovery_refs: list[Ref] = Field(default_factory=list)
    runtime_infrastructure_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    validation_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    data_loss_detected: bool
    unresolved_refs: list[Ref] = Field(default_factory=list)
    operator_status: str = ""
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_dr_restore_report(self) -> DRRestoreReport:
        if self.result == CompletenessResult.PASS:
            required = {
                "restore_scope_ref": self.restore_scope_ref,
                "restore_point_ref": self.restore_point_ref,
                "backup_manifest_ref": self.backup_manifest_ref,
                "metadata_restore_ref": self.metadata_restore_ref,
                "artifact_reachability_report_ref": self.artifact_reachability_report_ref,
                "event_replay_report_ref": self.event_replay_report_ref,
                "projection_rebuild_job_refs": self.projection_rebuild_job_refs,
                "export_reconciliation_refs": self.export_reconciliation_refs,
                "queue_recovery_refs": self.queue_recovery_refs,
                "runtime_infrastructure_report_refs": self.runtime_infrastructure_report_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
                "validation_refs": self.validation_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.missing_ref_fields
                or self.contract_only_refs
                or self.data_loss_detected
                or self.unresolved_refs
            ):
                raise ValueError(
                    f"passing DR restore report requires complete refs: {missing}"
                )
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.unresolved_refs or self.missing_ref_fields):
                raise ValueError("needs-review DR restore report requires review refs")
        elif not (self.failure_record_refs or self.unresolved_refs):
            raise ValueError("non-pass DR restore report requires failure or unresolved refs")
        return self


class DRRestoreFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: DRRestoreFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> DRRestoreFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("DR restore fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative DR restore fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self


class QualityReport(TimestampedModel):
    id: str
    run_id: str
    pages_fetched: int
    candidates_created: int
    outputs_published: int
    verification_decisions_accepted: int
    verification_decisions_rejected: int
    factual_outputs_published: int
    conflicts_detected: int
    drift_events: int
    freshness_lag_seconds: int
    extraction_success_rate: float
    verification_acceptance_rate: float
    cost_summary: dict[str, object] = Field(default_factory=dict)
    open_review_items: list[Ref] = Field(default_factory=list)
    replay_audit_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_quality_report(self) -> QualityReport:
        counters = [
            self.pages_fetched,
            self.candidates_created,
            self.outputs_published,
            self.verification_decisions_accepted,
            self.verification_decisions_rejected,
            self.factual_outputs_published,
            self.conflicts_detected,
            self.drift_events,
            self.freshness_lag_seconds,
        ]
        if any(value < 0 for value in counters):
            raise ValueError("quality counters must be non-negative")
        for field_name, value in {
            "extraction_success_rate": self.extraction_success_rate,
            "verification_acceptance_rate": self.verification_acceptance_rate,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
        if not self.policy_decision_refs:
            raise ValueError("quality report requires policy refs")
        if not self.projection_watermark_refs:
            raise ValueError("quality report requires projection watermark refs")
        return self


class OpsDashboardSnapshot(TimestampedModel):
    id: str
    run_id: str
    dashboard_type: OpsDashboardType
    as_of_event_cursor_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    replay_audit_view_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    alert_refs: list[Ref] = Field(default_factory=list)
    cost_summary_ref: Ref | None = None
    freshness_lag_seconds: int
    stale_projection_refs: list[Ref] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_dashboard_snapshot(self) -> OpsDashboardSnapshot:
        if self.freshness_lag_seconds < 0:
            raise ValueError("dashboard freshness lag must be non-negative")
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "as_of_event_cursor_refs": self.as_of_event_cursor_refs,
                "projection_watermark_refs": self.projection_watermark_refs,
                "quality_report_refs": self.quality_report_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.stale_projection_refs:
                raise ValueError(f"passing dashboard snapshot missing or stale refs: {missing}")
        elif not (
            self.failure_record_refs or self.stale_projection_refs or self.alert_refs
        ):
            raise ValueError("non-pass dashboard snapshot requires failure, stale, or alert refs")
        return self


class OpsConsoleReport(TimestampedModel):
    id: str
    run_ref: Ref
    review_item_refs: list[Ref] = Field(default_factory=list)
    replay_audit_view_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    dashboard_snapshot_ref: Ref | None = None
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_console_report(self) -> OpsConsoleReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "review_item_refs": self.review_item_refs,
                "replay_audit_view_refs": self.replay_audit_view_refs,
                "quality_report_refs": self.quality_report_refs,
                "dashboard_snapshot_ref": self.dashboard_snapshot_ref,
                "dr_restore_report_refs": self.dr_restore_report_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing ops console report missing refs: {missing}")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("non-pass ops console report requires failures")
        return self


class OpsFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> OpsFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("ops fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative ops fixture must not expect pass")
        return self
