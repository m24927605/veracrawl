from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_persistence_contracts_are_registered() -> None:
    expected = {
        "PersistenceAdapterSpec",
        "PersistenceTransactionRecord",
        "IdempotencyPersistenceRecord",
        "PersistentQueueOperationRecord",
        "PersistenceRuntimeReport",
        "PersistenceFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_persistence_commands_and_events_are_registered() -> None:
    expected = {
        "record_persistence_adapter": "persistence_adapter_recorded",
        "record_persistence_transaction": "persistence_transaction_recorded",
        "record_idempotency_persistence": "idempotency_persisted",
        "record_persistent_queue_operation": "persistent_queue_operation_recorded",
        "record_persistence_runtime_report": "persistence_runtime_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_persistence_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["production_persistence_queue_runtime"]
    assert area.coverage_status == "materialized"
    assert "PersistenceRuntimeReport" in area.materialized_contract_refs


def test_persistence_fixtures_are_registered() -> None:
    expected = {
        "persistence-transaction-success",
        "idempotent-replay-success",
        "queue-lease-recovery-success",
        "non-atomic-commit",
        "idempotency-not-persisted",
        "event-log-gap",
        "outbox-dispatch-missing",
        "artifact-index-missing",
        "lease-heartbeat-missing",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["persistence-transaction-success"].negative_case
    assert FIXTURE_ORACLES["non-atomic-commit"].negative_case
