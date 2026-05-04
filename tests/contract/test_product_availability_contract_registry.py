from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_product_availability_contracts_registered() -> None:
    for name in {
        "ProductAvailabilityTargetSpec",
        "ProductAvailabilityFieldEvidence",
        "ProductAvailabilitySiteResult",
        "ProductAvailabilityBenchmarkReport",
        "ProductAvailabilityBenchmarkManifest",
        "SortableProductOfferRecord",
        "ProductOfferProjectionReport",
        "ProductOfferProjectionManifest",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_product_availability_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_product_availability_field_evidence": (
            "product_availability_field_evidence_recorded"
        ),
        "record_product_availability_site_result": ("product_availability_site_result_recorded"),
        "record_product_availability_benchmark_report": ("product_availability_benchmark_reported"),
        "record_product_availability_benchmark_manifest": (
            "product_availability_benchmark_manifest_recorded"
        ),
        "record_product_offer_record": "product_offer_record_recorded",
        "record_product_offer_projection_report": "product_offer_projection_reported",
        "record_product_offer_projection_manifest": ("product_offer_projection_manifest_recorded"),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    fixture = FIXTURE_ORACLES["us-top-ecommerce-product-availability"]
    assert fixture.expected_product_availability_ref
    assert fixture.expected_replay_ref
    assert not fixture.negative_case
    assert FIXTURE_ORACLES["product-availability-missing-price"].negative_case


def test_product_availability_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["product_availability_benchmark_gate"]
    assert "ProductAvailabilityBenchmarkReport" in area.materialized_contract_refs
    assert "ProductAvailabilityFieldEvidence" in area.materialized_contract_refs
    assert "SortableProductOfferRecord" in area.materialized_contract_refs
    assert "ProductOfferProjectionReport" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
    assert validate_registry().ok
