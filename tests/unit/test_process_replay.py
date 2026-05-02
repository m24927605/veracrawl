from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.processing import NormalizeExtractReport
from veracrawl.review_replay.processing import missing_process_replay_refs, process_replay_passes


def _passing_report() -> NormalizeExtractReport:
    return NormalizeExtractReport(
        id="process-report:ok",
        run_ref="run:ok",
        network_acquisition_report_ref="network:ok",
        normalized_document_ref="normalized:ok",
        normalization_manifest_ref="manifest:ok",
        anchor_map_ref="anchor-map:ok",
        page_type_classification_ref="page-type:ok",
        site_model_ref="site-model:ok",
        extraction_strategy_ref="strategy:ok",
        extraction_candidate_ref="candidate:ok",
        artifact_refs=["artifact:normalized", "anchor-map:ok"],
        policy_decision_refs=["policy:process"],
        command_record_refs=["command:process"],
        event_cursor_refs=["cursor:process"],
        outbox_refs=["outbox:process"],
        operator_status="process_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_process_replay_passes_with_all_refs() -> None:
    report = _passing_report()
    assert missing_process_replay_refs(report) == []
    assert process_replay_passes(report)


def test_process_replay_reports_missing_refs() -> None:
    report = _passing_report().model_copy(update={"anchor_map_ref": None})
    assert "anchor_map_ref" in missing_process_replay_refs(report)
    assert not process_replay_passes(report)
