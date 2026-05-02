from __future__ import annotations

from veracrawl.memory.kernel import run_memory_kernel
from veracrawl.review_replay.memory import memory_replay_passes, missing_memory_replay_refs


def test_memory_replay_passes_for_complete_report() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory-replay",
        scenario="memory-write-retrieve-success",
        evidence_refs=["evidence:unit"],
        policy_decision_refs=["policy:unit:memory"],
    )
    assert memory_replay_passes(result.report)
    assert not missing_memory_replay_refs(result.report)


def test_memory_replay_reports_memory_as_evidence_failure() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory-as-evidence",
        scenario="memory-as-evidence",
        policy_decision_refs=["policy:unit:memory"],
    )
    assert not memory_replay_passes(result.report)
    assert "missing_reanchor_evidence" in missing_memory_replay_refs(result.report)
