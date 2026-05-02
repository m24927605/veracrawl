from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_multi_agent_contracts_registered() -> None:
    for contract in [
        "MultiAgentWorkflow",
        "AgentHandoff",
        "CoordinationDecision",
        "DriftRepairSignal",
        "MultiAgentRepairReport",
        "MultiAgentFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_multi_agent_commands_events_fixtures_registered() -> None:
    assert {
        "start_multi_agent_workflow",
        "record_agent_handoff",
        "record_coordination_decision",
        "record_multi_agent_repair_report",
    }.issubset(COMMAND_TYPES)
    assert {
        "multi_agent_workflow_started",
        "multi_agent_workflow_completed",
        "agent_handoff_completed",
        "coordination_decision_recorded",
    }.issubset(EVENT_TYPES)
    assert TARGET_CONTRACT_AREAS["agent_runtime"].coverage_status == "materialized"
    assert {
        "multi-agent-repair-success",
        "coordination-arbitration-success",
        "repair-loop-evidence-success",
        "owner-service-bypass",
        "unresolved-coordination-conflict",
        "agent-reasoning-as-evidence",
    }.issubset(FIXTURE_ORACLES)


def test_multi_agent_registry_validation_passes() -> None:
    assert validate_registry().ok
