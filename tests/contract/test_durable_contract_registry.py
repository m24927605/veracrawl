from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_durable_contracts_are_registered() -> None:
    report = validate_registry()
    assert report.ok, report.errors
    for contract in [
        "UnitOfWorkRecord",
        "DurableCommandRecord",
        "OutboxRecord",
        "EventCursorRecord",
        "DurableFixtureManifest",
        "FrontierItem",
        "QueueLease",
        "SchedulerRecoveryReport",
        "DurableReplayRecoveryReport",
    ]:
        assert contract in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[contract].test_refs


def test_durable_command_and_event_taxonomy_is_registered() -> None:
    for command_name in [
        "durable_commit_command",
        "enqueue_frontier_item",
        "lease_frontier_item",
        "complete_frontier_item",
        "record_durable_recovery",
    ]:
        command = COMMAND_TYPES[command_name]
        assert command.payload_schema_ref in FOUNDATION_CONTRACTS
        for event_type in command.emitted_event_types:
            assert event_type in EVENT_TYPES
    assert COMMAND_TYPES["lease_frontier_item"].lease_required is True


def test_durable_fixtures_are_registered() -> None:
    expected = {
        "durable-runtime-success": False,
        "durable-duplicate-command": False,
        "durable-event-gap": True,
        "durable-pending-outbox": True,
        "durable-stale-lease": True,
        "durable-invalid-lease": True,
        "durable-missing-artifact": True,
    }
    for fixture_id, negative in expected.items():
        fixture = FIXTURE_ORACLES[fixture_id]
        assert fixture.negative_case is negative
        assert fixture.manifest_ref.endswith("manifest.yaml")
        assert fixture.expected_replay_ref


def test_durable_target_areas_are_materialized_without_production_adapter_claims() -> None:
    durable = TARGET_CONTRACT_AREAS["durable_persistence"]
    scheduler = TARGET_CONTRACT_AREAS["scheduler"]
    assert durable.coverage_status == "materialized"
    assert scheduler.coverage_status == "materialized"
    assert "UnitOfWorkRecord" in durable.materialized_contract_refs
    assert "QueueLease" in scheduler.materialized_contract_refs
    assert durable.artifact_store_impact == "foundation fixture refs only"
