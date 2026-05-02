from __future__ import annotations

from veracrawl.cli.export import ExportFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_export_success(report: ExportFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "export_reconciliation_completed"
    assert report.export_target_spec_refs
    assert report.export_job_refs
    assert report.export_attempt_refs
    assert report.delivery_receipt_refs
    assert report.withdrawal_job_refs
    assert report.withdrawal_attempt_refs
    assert report.correction_record_refs
    assert report.destination_object_mapping_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def assert_export_negative(
    report: ExportFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult = CompletenessResult.FAIL,
) -> None:
    assert report.completion_result == completion_result
    assert report.operator_status == operator_status
    assert report.failure_report_refs
    assert report.missing_ref_fields
