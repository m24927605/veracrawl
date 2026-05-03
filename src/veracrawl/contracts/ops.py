"""Review, replay, and operations contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, utc_now
from veracrawl.contracts.enums import (
    AlertStatus,
    CompletenessResult,
    DRRestoreFailureType,
    DRRestorePhase,
    DRRestorePhaseStatus,
    DRRestoreRunStatus,
    ObservabilityFailureType,
    ObservabilityMetricKind,
    ObservabilitySignalType,
    OpsDashboardType,
    OpsFailureType,
    OpsRecoveryStatus,
    OpsReplayObservabilityFailureType,
    OpsSeverity,
    RecoveryActionType,
    ReplayMode,
    ReviewItemStatus,
    ReviewItemType,
    ReviewPriority,
    RunbookActionStatus,
    TraceSpanKind,
    TraceSpanStatus,
)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


_SENSITIVE_MARKERS = (
    "password",
    "secret",
    "token=",
    "api_key",
    "aws_access_key",
    "aws_secret",
    "postgres://",
    "redis://:",
    "s3://",
    "raw_prompt:",
    "raw_artifact:",
)


def _ensure_no_sensitive_values(values: list[str], field_name: str) -> None:
    for value in values:
        lowered = value.lower()
        if any(marker in lowered for marker in _SENSITIVE_MARKERS):
            raise ValueError(f"{field_name} contains unredacted sensitive value")


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
            RecoveryActionType.REFRESH_DASHBOARD_PROJECTION,
            RecoveryActionType.REDACT_SENSITIVE_CONTEXT,
            RecoveryActionType.RUN_OBSERVABILITY_RUNBOOK,
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


class ObservabilitySignal(TimestampedModel):
    id: str
    signal_type: ObservabilitySignalType
    owner_service_ref: Ref
    severity: OpsSeverity
    run_ref: Ref
    source_ref: Ref
    metric_refs: list[Ref] = Field(default_factory=list)
    trace_refs: list[Ref] = Field(default_factory=list)
    alert_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    payload_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_observability_signal(self) -> ObservabilitySignal:
        if not self.owner_service_ref or not self.run_ref or not self.source_ref:
            raise ValueError("observability signal requires owner, run, and source refs")
        if not self.policy_decision_refs:
            raise ValueError("observability signal requires policy refs")
        if not self.redaction_map_refs:
            raise ValueError("observability signal requires redaction refs")
        if self.severity in {OpsSeverity.HIGH, OpsSeverity.CRITICAL}:
            required = {
                "metric_refs": self.metric_refs,
                "trace_refs": self.trace_refs,
                "alert_refs": self.alert_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"high-severity signal missing refs: {missing}")
        _ensure_no_sensitive_values(self.payload_refs, "observability signal payload refs")
        return self


class MetricSample(TimestampedModel):
    id: str
    metric_name: str
    metric_kind: ObservabilityMetricKind
    value: float
    unit: str
    run_ref: Ref
    owner_service_ref: Ref
    timestamp_ref: Ref
    threshold_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    trace_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_metric_sample(self) -> MetricSample:
        if not self.metric_name or not self.unit:
            raise ValueError("metric sample requires name and unit")
        if not self.run_ref or not self.owner_service_ref or not self.timestamp_ref:
            raise ValueError("metric sample requires run, owner, and timestamp refs")
        if not self.threshold_ref:
            raise ValueError("metric sample requires threshold ref")
        if not self.policy_decision_refs:
            raise ValueError("metric sample requires policy refs")
        if not self.trace_refs:
            raise ValueError("metric sample requires trace refs")
        return self


class TraceSpan(TimestampedModel):
    id: str
    span_name: str
    span_kind: TraceSpanKind
    run_ref: Ref
    parent_span_ref: Ref | None = None
    command_ref: Ref | None = None
    event_ref: Ref | None = None
    owner_service_ref: Ref
    status: TraceSpanStatus
    duration_ms: int
    redacted_attribute_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_trace_span(self) -> TraceSpan:
        if self.duration_ms < 0:
            raise ValueError("trace span duration must be non-negative")
        if not self.span_name or not self.run_ref or not self.owner_service_ref:
            raise ValueError("trace span requires name, run, and owner refs")
        if self.span_kind == TraceSpanKind.COMMAND and not self.command_ref:
            raise ValueError("command span requires command ref")
        if self.span_kind == TraceSpanKind.EVENT and not self.event_ref:
            raise ValueError("event span requires event ref")
        if self.status == TraceSpanStatus.ERROR and not self.failure_record_refs:
            raise ValueError("error trace span requires failure refs")
        if not self.redacted_attribute_refs:
            raise ValueError("trace span requires redacted attribute refs")
        if not self.policy_decision_refs:
            raise ValueError("trace span requires policy refs")
        _ensure_no_sensitive_values(self.redacted_attribute_refs, "trace span attributes")
        return self


class AlertRecord(TimestampedModel):
    id: str
    alert_type: str
    severity: OpsSeverity
    status: AlertStatus
    run_ref: Ref
    metric_refs: list[Ref] = Field(default_factory=list)
    trace_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    runbook_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    resolution_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_alert_record(self) -> AlertRecord:
        if not self.alert_type or not self.run_ref:
            raise ValueError("alert record requires type and run ref")
        if not self.metric_refs or not self.trace_refs:
            raise ValueError("alert record requires metric and trace refs")
        if not self.policy_decision_refs:
            raise ValueError("alert record requires policy refs")
        if self.status in {AlertStatus.FIRING, AlertStatus.NEEDS_REVIEW}:
            if not self.failure_record_refs or not self.runbook_action_refs:
                raise ValueError("firing alert requires failure and runbook refs")
        if "recovery" in self.alert_type and not self.dr_restore_report_refs:
            raise ValueError("recovery alert requires DR refs")
        if self.status == AlertStatus.RESOLVED and not self.resolution_refs:
            raise ValueError("resolved alert requires resolution refs")
        return self


class RunbookAction(TimestampedModel):
    id: str
    action_type: str
    status: RunbookActionStatus
    run_ref: Ref
    alert_ref: Ref
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    side_effecting: bool = False
    approval_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_runbook_action(self) -> RunbookAction:
        if not self.action_type or not self.run_ref or not self.alert_ref:
            raise ValueError("runbook action requires action, run, and alert refs")
        if not self.policy_decision_refs:
            raise ValueError("runbook action requires policy refs")
        if self.side_effecting and not self.approval_decision_refs:
            raise ValueError("side-effecting runbook action requires approval refs")
        if self.status == RunbookActionStatus.EXECUTED:
            if not self.command_refs or not self.event_refs:
                raise ValueError("executed runbook action requires command and event refs")
        if self.status == RunbookActionStatus.RECOMMENDED:
            if not (
                self.failure_record_refs
                or self.recovery_action_refs
                or self.dr_restore_report_refs
            ):
                raise ValueError("recommended runbook action requires incident refs")
        return self


class ObservabilityReport(TimestampedModel):
    id: str
    run_ref: Ref
    signal_refs: list[Ref] = Field(default_factory=list)
    metric_sample_refs: list[Ref] = Field(default_factory=list)
    trace_span_refs: list[Ref] = Field(default_factory=list)
    alert_record_refs: list[Ref] = Field(default_factory=list)
    runbook_action_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    cost_metric_refs: list[Ref] = Field(default_factory=list)
    dashboard_snapshot_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    collector_handoff_refs: list[Ref] = Field(default_factory=list)
    telemetry_backend_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    stale_projection_refs: list[Ref] = Field(default_factory=list)
    unredacted_sensitive_fields: list[str] = Field(default_factory=list)
    unsafe_runbook_action_refs: list[Ref] = Field(default_factory=list)
    operator_status: str
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_observability_report(self) -> ObservabilityReport:
        if self.result == CompletenessResult.PASS:
            required = {
                "signal_refs": self.signal_refs,
                "metric_sample_refs": self.metric_sample_refs,
                "trace_span_refs": self.trace_span_refs,
                "alert_record_refs": self.alert_record_refs,
                "runbook_action_refs": self.runbook_action_refs,
                "quality_report_refs": self.quality_report_refs,
                "cost_metric_refs": self.cost_metric_refs,
                "dashboard_snapshot_refs": self.dashboard_snapshot_refs,
                "projection_watermark_refs": self.projection_watermark_refs,
                "failure_record_refs": self.failure_record_refs,
                "recovery_action_refs": self.recovery_action_refs,
                "dr_restore_report_refs": self.dr_restore_report_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "redaction_map_refs": self.redaction_map_refs,
                "collector_handoff_refs": self.collector_handoff_refs,
                "telemetry_backend_refs": self.telemetry_backend_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.contract_only_refs
                or self.missing_ref_fields
                or self.stale_projection_refs
                or self.unredacted_sensitive_fields
                or self.unsafe_runbook_action_refs
            ):
                raise ValueError(f"passing observability report missing refs: {missing}")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_ref_fields):
                raise ValueError("needs-review observability report requires review refs")
        elif not (
            self.failure_record_refs
            or self.missing_ref_fields
            or self.stale_projection_refs
            or self.unredacted_sensitive_fields
            or self.unsafe_runbook_action_refs
        ):
            raise ValueError("failed observability report requires failure details")
        return self


class ObservabilityFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ObservabilityFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ObservabilityFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("observability fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative observability fixture must expect fail")
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


class OpsReplayObservabilityRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    result_publication_export_report_ref: Ref | None = None
    worker_orchestration_runtime_report_ref: Ref | None = None
    ops_console_report_ref: Ref | None = None
    observability_report_ref: Ref | None = None
    run_control_action_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    evidence_review_refs: list[Ref] = Field(default_factory=list)
    replay_audit_view_refs: list[Ref] = Field(default_factory=list)
    graph_debug_refs: list[Ref] = Field(default_factory=list)
    export_status_refs: list[Ref] = Field(default_factory=list)
    withdrawal_status_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    quality_report_refs: list[Ref] = Field(default_factory=list)
    dashboard_snapshot_refs: list[Ref] = Field(default_factory=list)
    alert_record_refs: list[Ref] = Field(default_factory=list)
    runbook_action_refs: list[Ref] = Field(default_factory=list)
    cost_metric_refs: list[Ref] = Field(default_factory=list)
    observability_signal_refs: list[Ref] = Field(default_factory=list)
    metric_sample_refs: list[Ref] = Field(default_factory=list)
    trace_span_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: OpsReplayObservabilityFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    stale_dashboard_refs: list[Ref] = Field(default_factory=list)
    unresolved_recovery_refs: list[Ref] = Field(default_factory=list)
    unsafe_operator_action_refs: list[Ref] = Field(default_factory=list)
    observability_gap_refs: list[Ref] = Field(default_factory=list)
    replay_gap_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_ops_replay_observability_report(
        self,
    ) -> OpsReplayObservabilityRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "result_publication_export_report_ref": (
                    self.result_publication_export_report_ref
                ),
                "worker_orchestration_runtime_report_ref": (
                    self.worker_orchestration_runtime_report_ref
                ),
                "ops_console_report_ref": self.ops_console_report_ref,
                "observability_report_ref": self.observability_report_ref,
                "run_control_action_refs": self.run_control_action_refs,
                "review_item_refs": self.review_item_refs,
                "evidence_review_refs": self.evidence_review_refs,
                "replay_audit_view_refs": self.replay_audit_view_refs,
                "graph_debug_refs": self.graph_debug_refs,
                "export_status_refs": self.export_status_refs,
                "withdrawal_status_refs": self.withdrawal_status_refs,
                "recovery_action_refs": self.recovery_action_refs,
                "failure_record_refs": self.failure_record_refs,
                "dr_restore_report_refs": self.dr_restore_report_refs,
                "quality_report_refs": self.quality_report_refs,
                "dashboard_snapshot_refs": self.dashboard_snapshot_refs,
                "alert_record_refs": self.alert_record_refs,
                "runbook_action_refs": self.runbook_action_refs,
                "cost_metric_refs": self.cost_metric_refs,
                "observability_signal_refs": self.observability_signal_refs,
                "metric_sample_refs": self.metric_sample_refs,
                "trace_span_refs": self.trace_span_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "redaction_map_refs": self.redaction_map_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.stale_dashboard_refs
                or self.unresolved_recovery_refs
                or self.unsafe_operator_action_refs
                or self.observability_gap_refs
                or self.replay_gap_refs
            ):
                raise ValueError(
                    f"passing ops replay observability report missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.stale_dashboard_refs
                or self.unresolved_recovery_refs
                or self.unsafe_operator_action_refs
                or self.observability_gap_refs
                or self.replay_gap_refs
            )
        ):
            raise ValueError("non-pass ops replay observability report requires diagnostics")
        return self


class OpsReplayObservabilityFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: OpsReplayObservabilityFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ops_replay_observability_fixture(
        self,
    ) -> OpsReplayObservabilityFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("ops replay observability fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("ops replay observability fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative ops replay observability fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError(
                    "negative ops replay observability fixture requires failure type"
                )
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
