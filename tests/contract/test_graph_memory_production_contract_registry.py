from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_graph_memory_contracts_are_registered() -> None:
    assert "GraphMemoryProductionRuntimeReport" in FOUNDATION_CONTRACTS
    assert "GraphMemoryProductionFixtureManifest" in FOUNDATION_CONTRACTS
    assert (
        FOUNDATION_CONTRACTS[
            "GraphMemoryProductionRuntimeReport"
        ].python_model
        == "veracrawl.contracts.graph_memory.GraphMemoryProductionRuntimeReport"
    )


def test_graph_memory_commands_and_events_are_registered() -> None:
    assert "record_graph_memory_production_runtime_report" in COMMAND_TYPES
    assert "record_graph_memory_production_fixture_manifest" in COMMAND_TYPES
    assert "graph_memory_production_runtime_reported" in EVENT_TYPES
    assert "graph_memory_production_fixture_manifest_recorded" in EVENT_TYPES


def test_graph_memory_fixtures_are_registered() -> None:
    assert "graph-memory-production-success" in FIXTURE_ORACLES
    assert "graph-memory-replay-mismatch" in FIXTURE_ORACLES
    assert FIXTURE_ORACLES["graph-memory-production-success"].expected_graph_memory_ref
    assert FIXTURE_ORACLES["graph-memory-replay-mismatch"].negative_case


def test_graph_memory_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["graph_memory_production_runtime"]
    assert area.coverage_status == "materialized"
    assert "GraphMemoryProductionRuntimeReport" in area.materialized_contract_refs
    assert area.followup_spec_gate is None
