from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_worker_orchestration_contracts_are_registered() -> None:
    assert "WorkerOrchestrationRuntimeReport" in FOUNDATION_CONTRACTS
    assert "WorkerOrchestrationFixtureManifest" in FOUNDATION_CONTRACTS
    assert (
        FOUNDATION_CONTRACTS["WorkerOrchestrationRuntimeReport"].python_model
        == "veracrawl.contracts.scale.WorkerOrchestrationRuntimeReport"
    )
    assert validate_registry().ok


def test_worker_orchestration_commands_and_events_are_registered() -> None:
    expected = {
        "record_worker_orchestration_runtime_report": (
            "worker_orchestration_runtime_reported"
        ),
        "record_worker_orchestration_fixture_manifest": (
            "worker_orchestration_fixture_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_worker_orchestration_fixtures_are_registered() -> None:
    expected = {
        "worker-orchestration-production-success",
        "worker-orchestration-worker-crash-recovered",
        "worker-orchestration-backpressure-autoscale-success",
        "worker-orchestration-missing-persistence",
        "worker-orchestration-missing-queue-broker",
        "worker-orchestration-stale-lease-unrecovered",
        "worker-orchestration-missing-heartbeat",
        "worker-orchestration-dead-letter-hidden",
        "worker-orchestration-duplicate-pollution",
        "worker-orchestration-backpressure-without-policy",
        "worker-orchestration-replay-mismatch",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["worker-orchestration-production-success"].negative_case
    assert FIXTURE_ORACLES["worker-orchestration-replay-mismatch"].negative_case
    for fixture_id in expected:
        assert FIXTURE_ORACLES[fixture_id].expected_worker_orchestration_ref


def test_worker_orchestration_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["worker_orchestration_scale_runtime"]
    assert area.coverage_status == "materialized"
    assert "WorkerOrchestrationRuntimeReport" in area.materialized_contract_refs
    assert "QueueBrokerConformanceReport" in area.materialized_contract_refs
    assert area.followup_spec_gate is None
