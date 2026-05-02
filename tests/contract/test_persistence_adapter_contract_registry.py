from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_persistence_adapter_contracts_are_registered() -> None:
    expected = {
        "PersistenceAdapterSpec",
        "PersistenceMigrationRecord",
        "PersistenceAdapterConformanceReport",
        "PersistenceAdapterFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_persistence_adapter_commands_and_events_are_registered() -> None:
    expected = {
        "record_persistence_migration": "persistence_migration_recorded",
        "record_persistence_adapter_conformance_report": (
            "persistence_adapter_conformance_reported"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_persistence_adapter_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["concrete_persistence_adapters"]
    assert area.coverage_status == "materialized"
    assert "PersistenceAdapterConformanceReport" in area.materialized_contract_refs
    assert "PersistenceMigrationRecord" in area.materialized_contract_refs


def test_persistence_adapter_fixtures_are_registered() -> None:
    expected = {
        "sqlite-adapter-conformance-success",
        "sqlite-reopen-idempotency-success",
        "sqlite-queue-recovery-success",
        "postgres-adapter-contract-harness",
        "adapter-missing-capability",
        "sqlite-idempotency-gap",
        "sqlite-event-cursor-gap",
        "sqlite-outbox-gap",
        "sqlite-migration-missing",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["sqlite-adapter-conformance-success"].negative_case
    assert not FIXTURE_ORACLES["postgres-adapter-contract-harness"].negative_case
    assert FIXTURE_ORACLES["adapter-missing-capability"].negative_case
