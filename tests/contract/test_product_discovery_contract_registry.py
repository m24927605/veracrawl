from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_product_discovery_contracts_registered() -> None:
    for name in {
        "ProductDiscoverySourceSpec",
        "ProductDiscoveryCandidate",
        "ProductDiscoveryRunReport",
        "ProductDiscoveryBenchmarkManifest",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_product_discovery_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_product_discovery_candidate": "product_discovery_candidate_recorded",
        "record_product_discovery_run_report": "product_discovery_run_reported",
        "record_product_discovery_manifest": "product_discovery_manifest_recorded",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    fixture = FIXTURE_ORACLES["query-product-discovery-success"]
    assert fixture.expected_product_discovery_ref
    assert fixture.expected_replay_ref
    assert not fixture.negative_case
    assert FIXTURE_ORACLES["query-product-discovery-no-candidates"].negative_case


def test_product_discovery_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["product_discovery_benchmark_gate"]
    assert "ProductDiscoveryCandidate" in area.materialized_contract_refs
    assert "ProductAvailabilityBenchmarkReport" in area.materialized_contract_refs
    assert "ProductOfferProjectionReport" in area.materialized_contract_refs
    assert validate_registry().ok
