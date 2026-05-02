from __future__ import annotations

from veracrawl.review_replay.scale import missing_scale_replay_refs, scale_replay_passes
from veracrawl.scale.hardening import run_scale_hardening


def test_scale_replay_passes_for_complete_report() -> None:
    result = run_scale_hardening(
        fixture_id="unit-scale-replay",
        scenario="scale-sharding-success",
        policy_decision_refs=["policy:unit:scale"],
    )
    assert scale_replay_passes(result.report)
    assert not missing_scale_replay_refs(result.report)


def test_scale_replay_reports_missing_topology() -> None:
    result = run_scale_hardening(
        fixture_id="unit-scale-missing",
        scenario="replay-missing-scale-refs",
        policy_decision_refs=["policy:unit:scale"],
    )
    assert not scale_replay_passes(result.report)
    assert "queue_topology_ref" in missing_scale_replay_refs(result.report)
