from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_ops_replay_observability_contracts_are_registered() -> None:
    assert "OpsReplayObservabilityRuntimeReport" in FOUNDATION_CONTRACTS
    assert "OpsReplayObservabilityFixtureManifest" in FOUNDATION_CONTRACTS
    assert (
        FOUNDATION_CONTRACTS["OpsReplayObservabilityRuntimeReport"].python_model
        == "veracrawl.contracts.ops.OpsReplayObservabilityRuntimeReport"
    )
    assert validate_registry().ok


def test_ops_replay_observability_commands_and_events_are_registered() -> None:
    expected = {
        "record_ops_replay_observability_runtime_report": (
            "ops_replay_observability_runtime_reported"
        ),
        "record_ops_replay_observability_fixture_manifest": (
            "ops_replay_observability_fixture_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_ops_replay_observability_fixtures_are_registered() -> None:
    expected = {
        "ops-runtime-review-replay-success",
        "ops-runtime-incident-recovery-success",
        "ops-runtime-cost-alert-success",
        "ops-runtime-missing-publication",
        "ops-runtime-missing-worker-orchestration",
        "ops-runtime-missing-ops-console",
        "ops-runtime-missing-observability",
        "ops-runtime-stale-dashboard",
        "ops-runtime-unresolved-recovery",
        "ops-runtime-unsafe-operator-action",
        "ops-runtime-replay-mismatch",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["ops-runtime-review-replay-success"].negative_case
    assert FIXTURE_ORACLES["ops-runtime-replay-mismatch"].negative_case
    for fixture_id in expected:
        assert FIXTURE_ORACLES[fixture_id].expected_ops_runtime_ref


def test_ops_replay_observability_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["ops_replay_observability_runtime"]
    assert area.coverage_status == "materialized"
    assert "OpsReplayObservabilityRuntimeReport" in area.materialized_contract_refs
    assert "ResultPublicationExportRuntimeReport" in area.materialized_contract_refs
    assert "WorkerOrchestrationRuntimeReport" in area.materialized_contract_refs
    assert area.followup_spec_gate is None
