from __future__ import annotations

from veracrawl.agents.orchestration import run_multi_agent_repair
from veracrawl.contracts.enums import CompletenessResult


def test_repair_signal_requires_before_after_evidence() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-repair-evidence",
        scenario="repair-loop-evidence-success",
        policy_decision_refs=["policy:unit:agents"],
    )
    signal = result.repair_signals[0]
    assert signal.before_evidence_refs
    assert signal.after_evidence_refs
    assert signal.rollback_ref


def test_owner_service_bypass_is_rejected() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-owner-bypass",
        scenario="owner-service-bypass",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "owner_service_bypass"


def test_agent_reasoning_as_evidence_is_rejected() -> None:
    result = run_multi_agent_repair(
        fixture_id="unit-agent-evidence",
        scenario="agent-reasoning-as-evidence",
        policy_decision_refs=["policy:unit:agents"],
    )
    assert result.report.operator_status == "agent_reasoning_as_evidence"
