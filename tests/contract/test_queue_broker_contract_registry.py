from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_queue_broker_contracts_are_registered() -> None:
    expected = {
        "QueueBrokerAdapterSpec",
        "QueueBrokerOperationRecord",
        "QueueBrokerConformanceReport",
        "QueueBrokerFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_queue_broker_commands_and_events_are_registered() -> None:
    expected = {
        "record_queue_broker_adapter": "queue_broker_adapter_recorded",
        "record_queue_broker_operation": "queue_broker_operation_recorded",
        "record_queue_broker_conformance_report": "queue_broker_conformance_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_queue_broker_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["operational_queue_broker_adapter"]
    assert area.coverage_status == "materialized"
    assert "QueueBrokerConformanceReport" in area.materialized_contract_refs
    assert "QueueBrokerOperationRecord" in area.materialized_contract_refs


def test_queue_broker_fixtures_are_registered() -> None:
    expected = {
        "redis-broker-conformance-success",
        "redis-broker-idempotency-success",
        "redis-broker-dead-letter-success",
        "redis-broker-runtime-unavailable",
        "broker-missing-fencing-token",
        "broker-missing-heartbeat",
        "broker-missing-dead-letter",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["redis-broker-runtime-unavailable"].negative_case
    assert FIXTURE_ORACLES["broker-missing-fencing-token"].negative_case
