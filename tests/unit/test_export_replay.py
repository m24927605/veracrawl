from __future__ import annotations

from veracrawl.export.runtime import run_export_connector
from veracrawl.review_replay.export import export_replay_passes, missing_export_replay_refs


def test_export_replay_passes_for_complete_report() -> None:
    result = run_export_connector(
        fixture_id="unit-export-replay",
        scenario="export-file-success",
        policy_decision_refs=["policy:unit:export"],
    )
    assert export_replay_passes(result.report)
    assert not missing_export_replay_refs(result.report)


def test_export_replay_reports_missing_receipt() -> None:
    result = run_export_connector(
        fixture_id="unit-export-missing-receipt",
        scenario="export-missing-receipt",
        policy_decision_refs=["policy:unit:export"],
    )
    assert not export_replay_passes(result.report)
    assert "delivery_receipt_refs" in missing_export_replay_refs(result.report)
