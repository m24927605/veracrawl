from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_scale_contracts_are_registered() -> None:
    expected = {
        "QueueTopologySpec",
        "QueueItem",
        "ShardLease",
        "RetryDeadLetterRecord",
        "BackpressureSignal",
        "AutoscalingDecision",
        "ScaleRecoveryReport",
        "ScaleFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_scale_commands_and_events_are_registered() -> None:
    expected = {
        "record_queue_topology": "queue_topology_recorded",
        "record_queue_item": "queue_item_recorded",
        "record_shard_lease": "shard_lease_recorded",
        "record_backpressure_signal": "backpressure_signal_recorded",
        "record_autoscaling_decision": "autoscaling_decided",
        "record_retry_dead_letter": "retry_dead_letter_recorded",
        "record_scale_recovery_report": "scale_recovery_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_scale_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["scale_reliability"]
    assert area.coverage_status == "materialized"
    assert "BackpressureSignal" in area.materialized_contract_refs
    assert "AutoscalingDecision" in area.materialized_contract_refs


def test_scale_fixtures_are_registered() -> None:
    expected = {
        "scale-sharding-success",
        "backpressure-autoscale-success",
        "dead-letter-recovery-success",
        "stale-lease-without-recovery",
        "unfair-site-starvation",
        "autoscale-without-policy",
        "dead-letter-missing-failure-record",
        "replay-missing-scale-refs",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["scale-sharding-success"].negative_case
    assert FIXTURE_ORACLES["autoscale-without-policy"].negative_case
