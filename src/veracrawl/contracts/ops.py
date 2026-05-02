"""Review, replay, and operations contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, utc_now
from veracrawl.contracts.enums import (
    CompletenessResult,
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


class DRRestoreReport(TimestampedModel):
    id: str
    restore_scope_ref: Ref
    dr_restore_plan_id: str
    dr_restore_run_id: str
    metadata_restore_ref: Ref
    artifact_reachability_report_ref: Ref
    event_replay_report_ref: Ref
    projection_rebuild_job_refs: list[Ref] = Field(default_factory=list)
    export_reconciliation_refs: list[Ref] = Field(default_factory=list)
    validation_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    data_loss_detected: bool
    unresolved_refs: list[Ref] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_dr_restore_report(self) -> DRRestoreReport:
        if self.result == CompletenessResult.PASS:
            required = [
                self.restore_scope_ref,
                self.metadata_restore_ref,
                self.artifact_reachability_report_ref,
                self.event_replay_report_ref,
                self.projection_rebuild_job_refs,
                self.validation_refs,
            ]
            if not all(required) or self.data_loss_detected or self.unresolved_refs:
                raise ValueError(
                    "passing DR restore report requires complete refs and no data loss"
                )
        elif not (self.failure_record_refs or self.unresolved_refs):
            raise ValueError("non-pass DR restore report requires failure or unresolved refs")
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
