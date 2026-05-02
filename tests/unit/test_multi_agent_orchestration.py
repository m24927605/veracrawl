from __future__ import annotations

from veracrawl.agents.orchestration import run_multi_agent_repair
from veracrawl.contracts.enums import CompletenessResult, CoordinationDecisionType


def test_multi_agent_repair_builds_workflow_handoffs_and_decision() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-multi-agent",
        scenario="multi-agent-repair-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.workflow
    assert result.handoffs
    assert result.coordination_decisions
    assert result.repair_signals


def test_coordination_arbitration_resolves_conflict_explicitly() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-arbitration",
        scenario="coordination-arbitration-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    decision = result.coordination_decisions[0]
    assert decision.decision_type == CoordinationDecisionType.RESOLVE_RECOMMENDATION_CONFLICT
    assert decision.selected_ref in decision.candidate_refs
    assert decision.owner_command_ref
