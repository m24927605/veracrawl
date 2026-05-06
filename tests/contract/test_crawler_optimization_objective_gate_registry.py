from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_objective_gate_contracts_registered() -> None:
    for name in {
        "OptimizationObjectiveScore",
        "AgentDecisionLoopEvidence",
        "OptimizationObjectiveReleaseGate",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_objective_gate_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_optimization_objective_score": (
            "optimization_objective_score_recorded"
        ),
        "record_agent_decision_loop_evidence": (
            "agent_decision_loop_evidence_recorded"
        ),
        "record_optimization_objective_release_gate": (
            "optimization_objective_release_gated"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    assert FIXTURE_ORACLES["optimization-objective-gate-success"].negative_case is False
    for fixture_id in [
        "optimization-objective-low-score",
        "optimization-objective-formula-mismatch",
        "optimization-objective-missing-policy",
        "optimization-objective-missing-replay",
        "optimization-objective-missing-algorithms",
        "agent-decision-missing-phase",
        "agent-decision-low-confidence",
        "agent-decision-missing-stop",
        "agent-decision-llm-output-as-evidence",
        "objective-release-missing-lower-gate",
        "objective-release-failed-lower-gate",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True


def test_objective_gate_extends_existing_optimization_target_area() -> None:
    area = TARGET_CONTRACT_AREAS["crawler_intelligence_optimization_gate"]
    assert "OptimizationObjectiveScore" in area.materialized_contract_refs
    assert "AgentDecisionLoopEvidence" in area.materialized_contract_refs
    assert "OptimizationObjectiveReleaseGate" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
    assert "ToolCallTrace" in area.materialized_contract_refs
    assert validate_registry().ok
