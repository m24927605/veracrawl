from __future__ import annotations

from veracrawl.cli.dr import OperationalDRFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, DRRestoreRunStatus


def assert_dr_success(report: OperationalDRFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "operational_dr_restore_completed"
    assert report.run_status == DRRestoreRunStatus.COMPLETED
    assert report.dr_restore_plan_ref
    assert report.dr_restore_run_ref
    assert report.restore_scope_ref
    assert report.restore_point_ref
    assert report.backup_manifest_ref
    assert report.metadata_restore_ref
    assert report.artifact_reachability_report_ref
    assert report.event_replay_report_ref
    assert report.projection_rebuild_job_refs
    assert report.export_reconciliation_refs
    assert report.queue_recovery_refs
    assert report.runtime_infrastructure_report_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref
    assert report.validation_refs
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert not report.unresolved_refs
    assert report.data_loss_detected is False


def assert_dr_runtime_unavailable(report: OperationalDRFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "dr_restore_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_ref_fields == ["runtime_infrastructure_report_refs"]
    assert report.unresolved_refs
    assert not report.runtime_infrastructure_report_refs


def assert_dr_negative(
    report: OperationalDRFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert missing_field in report.missing_ref_fields
