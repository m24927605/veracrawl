from __future__ import annotations

from veracrawl.ops.console import run_ops_console
from veracrawl.review_replay.ops import missing_ops_replay_refs, ops_console_replay_passes


def test_ops_replay_passes_for_complete_report() -> None:
    result = run_ops_console(
        fixture_id="unit-ops-replay",
        scenario="review-console-success",
        policy_decision_refs=["policy:unit:ops"],
    )
    assert ops_console_replay_passes(result.report)
    assert not missing_ops_replay_refs(result.report)


def test_ops_replay_reports_missing_review_evidence() -> None:
    result = run_ops_console(
        fixture_id="unit-missing-review-evidence",
        scenario="missing-review-evidence",
        policy_decision_refs=["policy:unit:ops"],
    )
    assert not ops_console_replay_passes(result.report)
    assert "review_item.input_refs" in missing_ops_replay_refs(result.report)
