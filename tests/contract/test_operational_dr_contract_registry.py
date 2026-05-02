from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_operational_dr_contracts_are_registered() -> None:
    for name in [
        "DRRestorePlan",
        "DRRestoreRun",
        "DRRestoreReport",
        "DRRestoreFixtureManifest",
        "FailureRecord",
        "RecoveryAction",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_operational_dr_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_dr_restore_plan": "dr_restore_plan_recorded",
        "record_dr_restore_run": "dr_restore_run_recorded",
        "record_dr_restore_report": "dr_restore_reported",
        "record_dr_restore_fixture_manifest": "dr_restore_fixture_manifest_recorded",
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "dr-restore-success",
        "dr-restore-runtime-unavailable",
        "dr-restore-missing-metadata",
        "dr-restore-missing-artifact-reachability",
        "dr-restore-missing-event-replay",
        "dr-restore-missing-projection-rebuild",
        "dr-restore-missing-export-reconciliation",
        "dr-restore-unresolved-refs",
        "dr-restore-data-loss",
        "dr-restore-unsafe-recovery-without-approval",
    ]:
        assert fixture_id in FIXTURE_ORACLES


def test_operational_dr_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["operational_disaster_recovery_gate"]
    assert area.coverage_status == "materialized"
    assert "DRRestorePlan" in area.materialized_contract_refs
    assert "RuntimeInfrastructureReport" in area.materialized_contract_refs
