from __future__ import annotations

from veracrawl.agents.orchestration import run_multi_agent_repair
from veracrawl.review_replay.agents import (
    missing_multi_agent_replay_refs,
    multi_agent_replay_passes,
)


def test_multi_agent_replay_passes_for_complete_report() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-multi-agent-replay",
        scenario="multi-agent-repair-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert multi_agent_replay_passes(result.report)
    assert not missing_multi_agent_replay_refs(result.report)


def test_multi_agent_replay_reports_unresolved_conflict() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-unresolved-conflict",
        scenario="unresolved-coordination-conflict",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert not multi_agent_replay_passes(result.report)
    assert "unresolved_coordination_conflict" in missing_multi_agent_replay_refs(result.report)
