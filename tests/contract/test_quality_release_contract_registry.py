from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_quality_release_contracts_are_registered() -> None:
    for name in [
        "QualityReleaseThresholds",
        "QualityReleaseGateRef",
        "QualityReleaseStabilityRun",
        "QualityReleaseReport",
        "QualityReleaseManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {"ops", "tests"}


def test_quality_release_commands_and_events_are_registered() -> None:
    for command in [
        "record_quality_release_gate_ref",
        "record_quality_release_stability_run",
        "record_quality_release_report",
        "record_quality_release_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_quality_release_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["quality-release-ready"].negative_case is False
    for fixture_id in [
        "quality-release-missing-prior-gate",
        "quality-release-cost-exceeded",
        "quality-release-latency-violation",
        "quality-release-retry-violation",
        "quality-release-stability-regression",
        "quality-release-insufficient-runs",
        "quality-release-replay-gap",
        "quality-release-false-ready",
        "quality-release-missing-command-event",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_quality_release_ref


def test_quality_release_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["cost_latency_stability_quality_release_gate"]
    assert "QualityReleaseReport" in area.materialized_contract_refs
    assert "RepairQualityReport" in area.materialized_contract_refs
    assert "PrecisionRecallQualityReport" in area.materialized_contract_refs
