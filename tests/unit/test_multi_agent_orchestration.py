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
    assert result.report.agent_model_adapter_runtime_report_ref
    assert result.report.live_evidence_verification_runtime_report_ref
    assert result.report.controlled_tool_call_refs
    assert result.report.owner_command_refs
    assert result.report.replay_bundle_ref
    assert len(result.workflow.agent_role_sequence) >= 8


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


def test_crawl_and_extraction_repair_have_distinct_workflow_types() -> None:
    crawl = run_multi_agent_repair(
        fixture_id="unit-crawl-repair",
        scenario="crawl-repair-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    extraction = run_multi_agent_repair(
        fixture_id="unit-extraction-repair",
        scenario="extraction-repair-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert crawl.workflow is not None
    assert extraction.workflow is not None
    assert crawl.workflow.workflow_type == "crawl_repair"
    assert extraction.workflow.workflow_type == "extraction_repair"
