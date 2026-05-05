from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_runtime_wiring_contracts_registered() -> None:
    for name in {
        "RuntimeOptimizationSignalSet",
        "RuntimeFrontierOptimizationDecision",
        "RuntimeDomExtractionContext",
        "RuntimeDedupeRankingDecision",
        "RuntimeOptimizationAggregate",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_runtime_wiring_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_runtime_optimization_signal_set": "runtime_optimization_signal_set_recorded",
        "record_runtime_frontier_optimization_decision": (
            "runtime_frontier_optimization_decision_recorded"
        ),
        "record_runtime_dom_extraction_context": "runtime_dom_extraction_context_recorded",
        "record_runtime_dedupe_ranking_decision": "runtime_dedupe_ranking_decision_recorded",
        "record_runtime_optimization_aggregate": "runtime_optimization_aggregate_recorded",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    assert FIXTURE_ORACLES["runtime-optimization-wiring-success"].negative_case is False
    assert FIXTURE_ORACLES["runtime-optimization-missing-replay"].negative_case is True


def test_runtime_wiring_target_area_uses_existing_optimization_gate() -> None:
    area = TARGET_CONTRACT_AREAS["crawler_intelligence_optimization_gate"]
    assert "RuntimeFrontierOptimizationDecision" in area.materialized_contract_refs
    assert "RuntimeOptimizationAggregate" in area.materialized_contract_refs
    assert validate_registry().ok
