from __future__ import annotations

from veracrawl.cli.process import ProcessFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_process_success(report: ProcessFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "process_completed"
    assert report.network_acquisition_report_ref
    assert report.normalized_document_ref
    assert report.normalization_manifest_ref
    assert report.anchor_map_ref
    assert report.page_type_classification_ref
    assert report.site_model_ref
    assert report.extraction_strategy_ref
    assert report.extraction_candidate_ref
    assert report.artifact_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert not report.publication_refs


def assert_process_negative(
    report: ProcessFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult,
) -> None:
    assert report.operator_status == operator_status
    assert report.completion_result == completion_result
    assert report.failure_report_refs or report.missing_ref_fields
    assert not report.publication_refs
