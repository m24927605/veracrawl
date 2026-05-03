from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_repair_success_contracts_are_registered() -> None:
    for name in [
        "RepairQualityThresholds",
        "SeededRepairCase",
        "RepairAttemptTrace",
        "RepairQualityReport",
        "RepairQualityManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {
            "agents",
            "tests",
            "verify",
        }


def test_repair_success_commands_and_events_are_registered() -> None:
    for command in [
        "record_seeded_repair_case",
        "record_repair_attempt_trace",
        "record_repair_quality_report",
        "record_repair_quality_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_repair_success_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["repair-success-quality"].negative_case is False
    for fixture_id in [
        "repair-success-low-rate",
        "repair-success-unsafe-bypass",
        "repair-success-owner-service-bypass",
        "repair-success-model-only-evidence",
        "repair-success-missing-trace",
        "repair-success-rollback-missing",
        "repair-success-unresolved-hidden",
        "repair-success-replay-missing",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_repair_quality_ref


def test_repair_success_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["repair_success_rate_benchmark"]
    assert "RepairQualityReport" in area.materialized_contract_refs
    assert "RepairAttemptTrace" in area.materialized_contract_refs
    assert "ModelCallTrace" in area.materialized_contract_refs
