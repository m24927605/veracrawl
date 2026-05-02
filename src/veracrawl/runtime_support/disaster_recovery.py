"""Core operational disaster recovery gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    DRRestoreFailureType,
    DRRestorePhase,
    DRRestorePhaseStatus,
    DRRestoreRunStatus,
    OpsFailureType,
    OpsRecoveryStatus,
    OpsSeverity,
    RecoveryActionType,
)
from veracrawl.contracts.infrastructure import RuntimeInfrastructureReport
from veracrawl.contracts.ops import (
    DRRestorePhaseResult,
    DRRestorePlan,
    DRRestorePlanPhase,
    DRRestoreReport,
    DRRestoreRun,
    FailureRecord,
    RecoveryAction,
)


@dataclass(frozen=True)
class OperationalDRGateResult:
    plan: DRRestorePlan
    run: DRRestoreRun
    report: DRRestoreReport
    failure_records: list[FailureRecord]
    recovery_actions: list[RecoveryAction]
    runtime_infrastructure_report: RuntimeInfrastructureReport | None = None


_REQUIRED_PHASES: tuple[DRRestorePhase, ...] = (
    DRRestorePhase.RESTORE_METADATA,
    DRRestorePhase.RESTORE_ARTIFACTS,
    DRRestorePhase.REPLAY_EVENTS,
    DRRestorePhase.REBUILD_PROJECTIONS,
    DRRestorePhase.RECONCILE_EXPORTS,
    DRRestorePhase.VALIDATE_REFERENCES,
    DRRestorePhase.PUBLISH_REPORT,
)

_FAILURES: dict[str, tuple[DRRestoreFailureType, str, RecoveryActionType]] = {
    "dr-restore-missing-metadata": (
        DRRestoreFailureType.MISSING_METADATA_RESTORE_REFS,
        "metadata_restore_ref",
        RecoveryActionType.RESTORE_FROM_BACKUP,
    ),
    "dr-restore-missing-artifact-reachability": (
        DRRestoreFailureType.MISSING_ARTIFACT_REACHABILITY_REFS,
        "artifact_reachability_report_ref",
        RecoveryActionType.RESTORE_FROM_BACKUP,
    ),
    "dr-restore-missing-event-replay": (
        DRRestoreFailureType.MISSING_EVENT_REPLAY_REFS,
        "event_replay_report_ref",
        RecoveryActionType.REPLAY_EVENTS,
    ),
    "dr-restore-missing-projection-rebuild": (
        DRRestoreFailureType.MISSING_PROJECTION_REBUILD_REFS,
        "projection_rebuild_job_refs",
        RecoveryActionType.REBUILD_PROJECTION,
    ),
    "dr-restore-missing-export-reconciliation": (
        DRRestoreFailureType.MISSING_EXPORT_RECONCILIATION_REFS,
        "export_reconciliation_refs",
        RecoveryActionType.RECONCILE_EXPORT,
    ),
    "dr-restore-unresolved-refs": (
        DRRestoreFailureType.UNRESOLVED_REFS,
        "unresolved_refs",
        RecoveryActionType.REQUEST_REVIEW,
    ),
    "dr-restore-data-loss": (
        DRRestoreFailureType.DATA_LOSS_DETECTED,
        "data_loss_detected",
        RecoveryActionType.RESTORE_FROM_BACKUP,
    ),
    "dr-restore-unsafe-recovery-without-approval": (
        DRRestoreFailureType.UNSAFE_RECOVERY_WITHOUT_APPROVAL,
        "approval_decision_refs",
        RecoveryActionType.REQUEST_REVIEW,
    ),
}


def dr_restore_plan(
    fixture_id: str,
    *,
    policy_decision_refs: list[Ref],
    approval_decision_refs: list[Ref],
) -> DRRestorePlan:
    validation_gate_refs = [
        f"dr-validation-gate:{fixture_id}:{phase.value}" for phase in _REQUIRED_PHASES
    ]
    return DRRestorePlan(
        id=f"dr-restore-plan:{fixture_id}",
        restore_scope_ref=f"restore-scope:{fixture_id}",
        restore_point_ref=f"restore-point:{fixture_id}",
        backup_manifest_ref=f"backup-manifest:{fixture_id}",
        metadata_snapshot_ref=f"metadata-snapshot:{fixture_id}",
        artifact_snapshot_refs=[f"artifact-snapshot:{fixture_id}:raw"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:restore-point"],
        ordered_phases=[
            DRRestorePlanPhase(
                phase_name=phase,
                phase_order=index,
                input_refs=[f"dr-phase-input:{fixture_id}:{phase.value}"],
                output_contract_refs=[f"dr-phase-output-contract:{fixture_id}:{phase.value}"],
                validation_gate_refs=[validation_gate_refs[index - 1]],
                rollback_behavior="manual_review",
            )
            for index, phase in enumerate(_REQUIRED_PHASES, start=1)
        ],
        required_validation_gate_refs=validation_gate_refs,
        policy_decision_refs=policy_decision_refs,
        approval_decision_refs=approval_decision_refs,
    )


def run_operational_dr_gate(
    *,
    fixture_id: str,
    scenario: str,
    plan: DRRestorePlan,
    runtime_infrastructure_report: RuntimeInfrastructureReport | None,
) -> OperationalDRGateResult:
    if scenario == "dr-restore-runtime-unavailable":
        return run_operational_dr_runtime_unavailable_gate(fixture_id=fixture_id, plan=plan)
    if scenario in _FAILURES:
        failure, missing_field, action_type = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            plan=plan,
            failure=failure,
            missing_field=missing_field,
            action_type=action_type,
        )
    if (
        runtime_infrastructure_report is None
        or runtime_infrastructure_report.completion_result != CompletenessResult.PASS
    ):
        return run_operational_dr_runtime_unavailable_gate(fixture_id=fixture_id, plan=plan)
    return _success_result(
        fixture_id=fixture_id,
        plan=plan,
        runtime_infrastructure_report=runtime_infrastructure_report,
    )


def run_operational_dr_runtime_unavailable_gate(
    *,
    fixture_id: str,
    plan: DRRestorePlan,
) -> OperationalDRGateResult:
    run = DRRestoreRun(
        id=f"dr-restore-run:{fixture_id}",
        dr_restore_plan_id=plan.id,
        restore_scope_ref=plan.restore_scope_ref,
        current_phase=DRRestorePhase.RESTORE_METADATA,
        status=DRRestoreRunStatus.NEEDS_REVIEW,
        unresolved_refs=["runtime-infrastructure:live-substrate-required"],
        policy_decision_refs=plan.policy_decision_refs,
    )
    report = DRRestoreReport(
        id=f"dr-restore-report:{fixture_id}",
        restore_scope_ref=plan.restore_scope_ref,
        dr_restore_plan_id=plan.id,
        dr_restore_run_id=run.id,
        restore_point_ref=plan.restore_point_ref,
        backup_manifest_ref=plan.backup_manifest_ref,
        policy_decision_refs=plan.policy_decision_refs,
        contract_only_refs=[
            "runtime:postgres:dsn-required",
            "runtime:redis:url-required",
            "runtime:s3:endpoint-required",
            "runtime:dr-restore:live-infrastructure-not-executed",
        ],
        missing_ref_fields=["runtime_infrastructure_report_refs"],
        unresolved_refs=run.unresolved_refs,
        data_loss_detected=False,
        operator_status="dr_restore_runtime_unavailable",
        result=CompletenessResult.NEEDS_REVIEW,
    )
    return OperationalDRGateResult(
        plan=plan,
        run=run,
        report=report,
        failure_records=[],
        recovery_actions=[],
    )


def _success_result(
    *,
    fixture_id: str,
    plan: DRRestorePlan,
    runtime_infrastructure_report: RuntimeInfrastructureReport,
) -> OperationalDRGateResult:
    phase_results = [
        DRRestorePhaseResult(
            phase_name=phase,
            status=DRRestorePhaseStatus.COMPLETED,
            input_refs=[f"dr-phase-input:{fixture_id}:{phase.value}"],
            output_refs=[f"dr-phase-output:{fixture_id}:{phase.value}"],
            validation_result_refs=[f"dr-validation:{fixture_id}:{phase.value}:pass"],
        )
        for phase in _REQUIRED_PHASES
    ]
    failure_record = _failure_record(
        fixture_id,
        failure=DRRestoreFailureType.UNRESOLVED_REFS,
        failed_ref=f"dr-restore-run:{fixture_id}:rehearsal",
        policy_decision_refs=plan.policy_decision_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=RecoveryActionType.REQUEST_REVIEW,
        policy_decision_refs=plan.policy_decision_refs,
        approval_decision_refs=plan.approval_decision_refs,
    )
    run = DRRestoreRun(
        id=f"dr-restore-run:{fixture_id}",
        dr_restore_plan_id=plan.id,
        restore_scope_ref=plan.restore_scope_ref,
        phase_results=phase_results,
        current_phase=DRRestorePhase.PUBLISH_REPORT,
        status=DRRestoreRunStatus.COMPLETED,
        emitted_event_refs=[f"event:{fixture_id}:dr_restore_reported"],
        policy_decision_refs=plan.policy_decision_refs,
    )
    report = DRRestoreReport(
        id=f"dr-restore-report:{fixture_id}",
        restore_scope_ref=plan.restore_scope_ref,
        dr_restore_plan_id=plan.id,
        dr_restore_run_id=run.id,
        restore_point_ref=plan.restore_point_ref,
        backup_manifest_ref=plan.backup_manifest_ref,
        metadata_restore_ref=_first_or(
            runtime_infrastructure_report.transaction_refs,
            fixture_id,
            "metadata",
        ),
        artifact_reachability_report_ref=_first_or(
            runtime_infrastructure_report.object_operation_refs,
            fixture_id,
            "artifact-reachability",
        ),
        event_replay_report_ref=_first_or(
            runtime_infrastructure_report.event_cursor_refs,
            fixture_id,
            "event-replay",
        ),
        projection_rebuild_job_refs=[f"projection-rebuild-job:{fixture_id}:restored"],
        export_reconciliation_refs=[f"export-reconciliation:{fixture_id}:restored"],
        queue_recovery_refs=_unique(
            runtime_infrastructure_report.queue_operation_refs
            + runtime_infrastructure_report.lease_refs
            + runtime_infrastructure_report.heartbeat_refs
            + runtime_infrastructure_report.dead_letter_refs
        ),
        runtime_infrastructure_report_refs=[runtime_infrastructure_report.id],
        command_record_refs=runtime_infrastructure_report.command_record_refs,
        event_cursor_refs=runtime_infrastructure_report.event_cursor_refs,
        outbox_refs=runtime_infrastructure_report.outbox_refs,
        policy_decision_refs=_unique(
            plan.policy_decision_refs + runtime_infrastructure_report.policy_decision_refs
        ),
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dr-restore",
        validation_refs=[result.validation_result_refs[0] for result in phase_results],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        data_loss_detected=False,
        operator_status="operational_dr_restore_completed",
        result=CompletenessResult.PASS,
    )
    return OperationalDRGateResult(
        plan=plan,
        run=run,
        report=report,
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
        runtime_infrastructure_report=runtime_infrastructure_report,
    )


def _failure_result(
    *,
    fixture_id: str,
    plan: DRRestorePlan,
    failure: DRRestoreFailureType,
    missing_field: str,
    action_type: RecoveryActionType,
) -> OperationalDRGateResult:
    failure_record = _failure_record(
        fixture_id,
        failure=failure,
        failed_ref=f"dr-restore-run:{fixture_id}",
        policy_decision_refs=plan.policy_decision_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=action_type,
        policy_decision_refs=plan.policy_decision_refs,
        approval_decision_refs=plan.approval_decision_refs,
    )
    phase_results = [
        DRRestorePhaseResult(
            phase_name=DRRestorePhase.VALIDATE_REFERENCES,
            status=DRRestorePhaseStatus.FAILED,
            input_refs=[f"dr-phase-input:{fixture_id}:validate_references"],
            validation_result_refs=[f"dr-validation:{fixture_id}:{missing_field}:fail"],
            failure_record_ref=failure_record.id,
        )
    ]
    unresolved_refs = (
        [f"unresolved-ref:{fixture_id}:restore"]
        if failure == DRRestoreFailureType.UNRESOLVED_REFS
        else []
    )
    data_loss = failure == DRRestoreFailureType.DATA_LOSS_DETECTED
    run = DRRestoreRun(
        id=f"dr-restore-run:{fixture_id}",
        dr_restore_plan_id=plan.id,
        restore_scope_ref=plan.restore_scope_ref,
        phase_results=phase_results,
        current_phase=DRRestorePhase.VALIDATE_REFERENCES,
        status=DRRestoreRunStatus.FAILED,
        failure_record_refs=[failure_record.id],
        unresolved_refs=unresolved_refs,
        policy_decision_refs=plan.policy_decision_refs,
    )
    report = DRRestoreReport(
        id=f"dr-restore-report:{fixture_id}",
        restore_scope_ref=plan.restore_scope_ref,
        dr_restore_plan_id=plan.id,
        dr_restore_run_id=run.id,
        restore_point_ref=plan.restore_point_ref,
        backup_manifest_ref=plan.backup_manifest_ref,
        metadata_restore_ref=None
        if missing_field == "metadata_restore_ref"
        else f"metadata-restore:{fixture_id}",
        artifact_reachability_report_ref=None
        if missing_field == "artifact_reachability_report_ref"
        else f"artifact-reachability:{fixture_id}",
        event_replay_report_ref=None
        if missing_field == "event_replay_report_ref"
        else f"event-replay:{fixture_id}",
        projection_rebuild_job_refs=[]
        if missing_field == "projection_rebuild_job_refs"
        else [f"projection-rebuild-job:{fixture_id}"],
        export_reconciliation_refs=[]
        if missing_field == "export_reconciliation_refs"
        else [f"export-reconciliation:{fixture_id}"],
        queue_recovery_refs=[f"queue-recovery:{fixture_id}"],
        runtime_infrastructure_report_refs=[f"runtime-infrastructure-report:{fixture_id}:negative"],
        command_record_refs=[f"command:{fixture_id}:dr-restore"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:dr-restore"],
        outbox_refs=[f"outbox:{fixture_id}:dr-restore"],
        policy_decision_refs=plan.policy_decision_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dr-restore",
        validation_refs=[f"dr-validation:{fixture_id}:fail"],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        missing_ref_fields=[missing_field],
        data_loss_detected=data_loss,
        unresolved_refs=unresolved_refs,
        operator_status=failure.value,
        result=CompletenessResult.FAIL,
    )
    return OperationalDRGateResult(
        plan=plan,
        run=run,
        report=report,
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
    )


def _failure_record(
    fixture_id: str,
    *,
    failure: DRRestoreFailureType,
    failed_ref: Ref,
    policy_decision_refs: list[Ref],
) -> FailureRecord:
    failure_type = (
        OpsFailureType.UNSAFE_RECOVERY_WITHOUT_REVIEW
        if failure == DRRestoreFailureType.UNSAFE_RECOVERY_WITHOUT_APPROVAL
        else OpsFailureType.DISASTER_RECOVERY
    )
    return FailureRecord(
        id=f"failure-record:{fixture_id}:{failure.value}",
        run_id=f"run:{fixture_id}",
        failure_type=failure_type,
        failed_ref=failed_ref,
        owner_service_ref="ops:disaster-recovery",
        severity=OpsSeverity.HIGH,
        retryable=True,
        diagnostic_ref=f"diagnostic:{fixture_id}:{failure.value}",
        policy_decision_refs=policy_decision_refs,
        replay_audit_refs=[f"replay-audit:{fixture_id}:dr-restore"],
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
        review_item_refs=[f"review-item:{fixture_id}:dr-restore"],
        status=OpsRecoveryStatus.PROPOSED,
    )


def _first_or(values: list[Ref], fixture_id: str, suffix: str) -> Ref:
    return values[0] if values else f"{suffix}:{fixture_id}:missing"


def _unique(values: list[Ref]) -> list[Ref]:
    seen: set[str] = set()
    result: list[Ref] = []
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result
