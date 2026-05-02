from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_object_store_contracts_are_registered() -> None:
    expected = {
        "ObjectStoreAdapterSpec",
        "ObjectStoreOperationRecord",
        "ObjectStoreConformanceReport",
        "ObjectStoreFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_object_store_commands_and_events_are_registered() -> None:
    expected = {
        "record_object_store_adapter": "object_store_adapter_recorded",
        "record_object_store_operation": "object_store_operation_recorded",
        "record_object_store_conformance_report": "object_store_conformance_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_object_store_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["operational_object_store_adapter"]
    assert area.coverage_status == "materialized"
    assert "ObjectStoreConformanceReport" in area.materialized_contract_refs
    assert "ObjectStoreOperationRecord" in area.materialized_contract_refs


def test_object_store_fixtures_are_registered() -> None:
    expected = {
        "s3-object-store-conformance-success",
        "s3-object-store-idempotency-success",
        "s3-object-store-delete-success",
        "s3-object-store-runtime-unavailable",
        "object-store-missing-digest",
        "object-store-missing-read-after-write",
        "object-store-missing-delete-marker",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["s3-object-store-runtime-unavailable"].negative_case
    assert FIXTURE_ORACLES["object-store-missing-digest"].negative_case
