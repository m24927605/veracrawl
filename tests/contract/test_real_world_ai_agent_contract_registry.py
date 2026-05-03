from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_real_world_ai_agent_contracts_registered() -> None:
    for name in {
        "RealWorldAIAgentDecisionTrace",
        "RealWorldAIAgentExtractionCandidate",
        "RealWorldAIAgentBenchmarkRunReport",
        "RealWorldAIAgentBenchmarkManifest",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_real_world_ai_agent_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_real_world_ai_agent_decision": (
            "real_world_ai_agent_decision_recorded"
        ),
        "record_real_world_ai_agent_extraction_candidate": (
            "real_world_ai_agent_extraction_candidate_recorded"
        ),
        "record_real_world_ai_agent_benchmark_report": (
            "real_world_ai_agent_benchmark_reported"
        ),
        "record_real_world_ai_agent_benchmark_manifest": (
            "real_world_ai_agent_benchmark_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        command = COMMAND_TYPES[command_type]
        assert event_type in command.emitted_event_types

    fixture = FIXTURE_ORACLES["real-world-ai-agent-public-corpus"]
    assert fixture.expected_real_world_ai_agent_benchmark_ref
    assert not fixture.negative_case
    assert FIXTURE_ORACLES["real-world-ai-agent-publication-bypass"].negative_case


def test_real_world_ai_agent_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["real_world_ai_agent_benchmark_gate"]
    assert "RealWorldAIAgentBenchmarkRunReport" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
    assert "AgentActionTrace" in area.materialized_contract_refs
