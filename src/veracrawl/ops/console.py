"""Deterministic review/replay/ops console runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
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
from veracrawl.contracts.ops import (
    DRRestoreReport,
    FailureRecord,
    OpsConsoleReport,
    OpsDashboardSnapshot,
    QualityReport,
    RecoveryAction,
    ReplayAuditView,
    ReviewItem,
)


@dataclass(frozen=True)
class OpsConsoleResult:
    review_items: list[ReviewItem]
    replay_audit_views: list[ReplayAuditView]
    failure_records: list[FailureRecord]
    recovery_actions: list[RecoveryAction]
    dr_restore_reports: list[DRRestoreReport]
    quality_reports: list[QualityReport]
    dashboard_snapshots: list[OpsDashboardSnapshot]
    report: OpsConsoleReport


def run_ops_console(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> OpsConsoleResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:ops"]
    failures = {
        "missing-review-evidence": (
            OpsFailureType.MISSING_REVIEW_EVIDENCE,
            "review_item.input_refs",
        ),
        "unresolved-failure-without-recovery": (
            OpsFailureType.UNRESOLVED_FAILURE_WITHOUT_RECOVERY,
            "recovery_action_refs",
        ),
        "stale-dashboard-projection": (
            OpsFailureType.STALE_DASHBOARD_PROJECTION,
            "projection_watermark_refs",
        ),
        "unsafe-recovery-without-review": (
            OpsFailureType.UNSAFE_RECOVERY_WITHOUT_REVIEW,
            "approval_decision_refs",
        ),
    }
    if scenario in failures:
        failure, missing = failures[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing,
            policy_refs=policy_refs,
        )
    return _success_result(fixture_id=fixture_id, scenario=scenario, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
) -> OpsConsoleResult:
    review_item = _review_item(fixture_id, policy_refs)
    replay_audit = _replay_audit(fixture_id, policy_refs)
    failure_record = _resolved_failure(fixture_id, policy_refs, replay_audit.id)
    recovery_action = _recovery_action(fixture_id, failure_record.id, review_item.id, policy_refs)
    failure_record.recovery_action_refs.append(recovery_action.id)
    dr_restore = _dr_restore(fixture_id, failure_record.id, recovery_action.id)
    quality_report = _quality_report(fixture_id, policy_refs, replay_audit.id, review_item.id)
    dashboard_type = {
        "review-console-success": OpsDashboardType.REVIEW,
        "replay-audit-success": OpsDashboardType.REPLAY,
        "quality-dashboard-success": OpsDashboardType.QUALITY,
    }.get(scenario, OpsDashboardType.RUN)
    dashboard = _dashboard(
        fixture_id=fixture_id,
        dashboard_type=dashboard_type,
        review_item_ref=review_item.id,
        replay_audit_ref=replay_audit.id,
        quality_report_ref=quality_report.id,
        failure_record_ref=failure_record.id,
        recovery_action_ref=recovery_action.id,
        dr_restore_report_ref=dr_restore.id,
    )
    report = OpsConsoleReport(
        id=f"ops-console-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        review_item_refs=[review_item.id],
        replay_audit_view_refs=[replay_audit.id],
        quality_report_refs=[quality_report.id],
        dashboard_snapshot_ref=dashboard.id,
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        dr_restore_report_refs=[dr_restore.id],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:ops"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:ops"],
        outbox_refs=[f"outbox:{fixture_id}:ops"],
        operator_status="ops_console_completed",
        completion_result=CompletenessResult.PASS,
    )
    return OpsConsoleResult(
        review_items=[review_item],
        replay_audit_views=[replay_audit],
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
        dr_restore_reports=[dr_restore],
        quality_reports=[quality_report],
        dashboard_snapshots=[dashboard],
        report=report,
    )


def _review_item(fixture_id: str, policy_refs: list[Ref]) -> ReviewItem:
    return ReviewItem(
        id=f"review-item:{fixture_id}:evidence",
        run_id=f"run:{fixture_id}",
        objective_id=f"objective:{fixture_id}",
        item_type=ReviewItemType.EVIDENCE_PACKET,
        input_refs=[
            f"evidence-packet:{fixture_id}:field",
            f"verification-decision:{fixture_id}:review",
        ],
        reason="evidence_packet_requires_operator_visibility",
        priority=ReviewPriority.HIGH,
        status=ReviewItemStatus.OPEN,
        policy_decision_refs=policy_refs,
        replay_audit_refs=[f"replay-audit-view:{fixture_id}"],
    )


def _replay_audit(fixture_id: str, policy_refs: list[Ref]) -> ReplayAuditView:
    return ReplayAuditView(
        id=f"replay-audit-view:{fixture_id}",
        run_id=f"run:{fixture_id}",
        replay_bundle_ref=f"replay-bundle:{fixture_id}",
        replay_mode=ReplayMode.STRUCTURAL,
        replay_validation_report_ref=f"replay-validation:{fixture_id}",
        command_refs=[f"command:{fixture_id}:ops"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:ops"],
        artifact_hash_refs=[f"artifact-hash:{fixture_id}:ops"],
        projection_watermark_refs=[f"projection-watermark:{fixture_id}:ops"],
        redaction_map_ref=f"redaction-map:{fixture_id}",
        policy_decision_refs=policy_refs,
        completeness_result=CompletenessResult.PASS,
    )


def _resolved_failure(
    fixture_id: str,
    policy_refs: list[Ref],
    replay_audit_ref: Ref,
) -> FailureRecord:
    return FailureRecord(
        id=f"failure-record:{fixture_id}:projection",
        run_id=f"run:{fixture_id}",
        failure_type=OpsFailureType.PROJECTION_MISMATCH,
        failed_ref=f"projection:{fixture_id}:quality",
        owner_service_ref="owner-service:projection",
        severity=OpsSeverity.MEDIUM,
        retryable=True,
        dead_letter_reason="",
        diagnostic_ref=f"diagnostic:{fixture_id}:projection-mismatch",
        evidence_refs=[f"evidence-packet:{fixture_id}:field"],
        policy_decision_refs=policy_refs,
        replay_audit_refs=[replay_audit_ref],
    )


def _recovery_action(
    fixture_id: str,
    failure_record_ref: Ref,
    review_item_ref: Ref,
    policy_refs: list[Ref],
) -> RecoveryAction:
    return RecoveryAction(
        id=f"recovery-action:{fixture_id}:rebuild-projection",
        failure_record_id=failure_record_ref,
        action_type=RecoveryActionType.REBUILD_PROJECTION,
        command_refs=[f"command:{fixture_id}:rebuild-projection"],
        policy_decision_refs=policy_refs,
        approval_decision_refs=[f"approval:{fixture_id}:ops-recovery"],
        review_item_refs=[review_item_ref],
        status=OpsRecoveryStatus.COMPLETED,
        result_refs=[f"projection-rebuild-result:{fixture_id}:pass"],
    )


def _dr_restore(
    fixture_id: str,
    failure_record_ref: Ref,
    recovery_action_ref: Ref,
) -> DRRestoreReport:
    return DRRestoreReport(
        id=f"dr-restore-report:{fixture_id}",
        restore_scope_ref=f"restore-scope:{fixture_id}",
        dr_restore_plan_id=f"dr-restore-plan:{fixture_id}",
        dr_restore_run_id=f"dr-restore-run:{fixture_id}",
        restore_point_ref=f"restore-point:{fixture_id}",
        backup_manifest_ref=f"backup-manifest:{fixture_id}",
        metadata_restore_ref=f"metadata-restore:{fixture_id}",
        artifact_reachability_report_ref=f"artifact-reachability:{fixture_id}",
        event_replay_report_ref=f"event-replay:{fixture_id}",
        projection_rebuild_job_refs=[f"projection-rebuild-job:{fixture_id}"],
        export_reconciliation_refs=[f"export-reconciliation:{fixture_id}:dry-run"],
        queue_recovery_refs=[f"queue-recovery:{fixture_id}:ops"],
        runtime_infrastructure_report_refs=[f"runtime-infrastructure-report:{fixture_id}:ops"],
        command_record_refs=[f"command:{fixture_id}:dr-restore"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:dr-restore"],
        outbox_refs=[f"outbox:{fixture_id}:dr-restore"],
        policy_decision_refs=[f"policy:{fixture_id}:dr-restore"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:dr-restore",
        validation_refs=[f"dr-validation:{fixture_id}:pass"],
        failure_record_refs=[failure_record_ref],
        recovery_action_refs=[recovery_action_ref],
        operator_status="dr_restore_completed",
        data_loss_detected=False,
        result=CompletenessResult.PASS,
    )


def _quality_report(
    fixture_id: str,
    policy_refs: list[Ref],
    replay_audit_ref: Ref,
    review_item_ref: Ref,
) -> QualityReport:
    return QualityReport(
        id=f"quality-report:{fixture_id}",
        run_id=f"run:{fixture_id}",
        pages_fetched=12,
        candidates_created=9,
        outputs_published=4,
        verification_decisions_accepted=4,
        verification_decisions_rejected=1,
        factual_outputs_published=4,
        conflicts_detected=1,
        drift_events=1,
        freshness_lag_seconds=12,
        extraction_success_rate=0.86,
        verification_acceptance_rate=0.8,
        cost_summary={"token_units": 42, "browser_seconds": 0},
        open_review_items=[review_item_ref],
        replay_audit_refs=[replay_audit_ref],
        policy_decision_refs=policy_refs,
        projection_watermark_refs=[f"projection-watermark:{fixture_id}:ops"],
    )


def _dashboard(
    *,
    fixture_id: str,
    dashboard_type: OpsDashboardType,
    review_item_ref: Ref,
    replay_audit_ref: Ref,
    quality_report_ref: Ref,
    failure_record_ref: Ref,
    recovery_action_ref: Ref,
    dr_restore_report_ref: Ref,
) -> OpsDashboardSnapshot:
    return OpsDashboardSnapshot(
        id=f"ops-dashboard-snapshot:{fixture_id}",
        run_id=f"run:{fixture_id}",
        dashboard_type=dashboard_type,
        as_of_event_cursor_refs=[f"event-cursor:{fixture_id}:ops"],
        projection_watermark_refs=[f"projection-watermark:{fixture_id}:ops"],
        review_item_refs=[review_item_ref],
        replay_audit_view_refs=[replay_audit_ref],
        quality_report_refs=[quality_report_ref],
        failure_record_refs=[failure_record_ref],
        recovery_action_refs=[recovery_action_ref],
        dr_restore_report_refs=[dr_restore_report_ref],
        alert_refs=[f"alert:{fixture_id}:resolved-projection-mismatch"],
        cost_summary_ref=f"cost-summary:{fixture_id}",
        freshness_lag_seconds=12,
        completion_result=CompletenessResult.PASS,
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: OpsFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> OpsConsoleResult:
    failure_record = FailureRecord(
        id=f"failure-record:{fixture_id}:{failure.value}",
        run_id=f"run:{fixture_id}",
        failure_type=failure,
        failed_ref=f"ops-console:{fixture_id}",
        owner_service_ref="owner-service:ops",
        severity=OpsSeverity.HIGH,
        retryable=failure
        in {
            OpsFailureType.UNRESOLVED_FAILURE_WITHOUT_RECOVERY,
            OpsFailureType.STALE_DASHBOARD_PROJECTION,
        },
        dead_letter_reason="",
        diagnostic_ref=f"diagnostic:{fixture_id}:{failure.value}",
        policy_decision_refs=policy_refs,
    )
    dashboard_snapshots: list[OpsDashboardSnapshot] = []
    if failure == OpsFailureType.STALE_DASHBOARD_PROJECTION:
        dashboard_snapshots.append(
            OpsDashboardSnapshot(
                id=f"ops-dashboard-snapshot:{fixture_id}",
                run_id=f"run:{fixture_id}",
                dashboard_type=OpsDashboardType.QUALITY,
                as_of_event_cursor_refs=[f"event-cursor:{fixture_id}:ops"],
                failure_record_refs=[failure_record.id],
                alert_refs=[f"alert:{fixture_id}:stale-projection"],
                freshness_lag_seconds=600,
                stale_projection_refs=[f"projection-watermark:{fixture_id}:stale"],
                completion_result=CompletenessResult.FAIL,
            )
        )
    report = OpsConsoleReport(
        id=f"ops-console-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        dashboard_snapshot_ref=dashboard_snapshots[0].id if dashboard_snapshots else None,
        failure_record_refs=[failure_record.id],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:ops"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:ops"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return OpsConsoleResult(
        review_items=[],
        replay_audit_views=[],
        failure_records=[failure_record],
        recovery_actions=[],
        dr_restore_reports=[],
        quality_reports=[],
        dashboard_snapshots=dashboard_snapshots,
        report=report,
    )
