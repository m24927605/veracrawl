from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_production_benchmark_release_contracts_are_registered() -> None:
    assert "ProductionBenchmarkReleaseReport" in FOUNDATION_CONTRACTS
    assert "ProductionBenchmarkReleaseFixtureManifest" in FOUNDATION_CONTRACTS
    assert (
        FOUNDATION_CONTRACTS["ProductionBenchmarkReleaseReport"].python_model
        == "veracrawl.contracts.release.ProductionBenchmarkReleaseReport"
    )
    assert validate_registry().ok


def test_production_benchmark_release_commands_and_events_are_registered() -> None:
    expected = {
        "record_production_benchmark_release_report": (
            "production_benchmark_release_reported"
        ),
        "record_production_benchmark_release_fixture_manifest": (
            "production_benchmark_release_fixture_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_production_benchmark_release_fixtures_are_registered() -> None:
    expected = {
        "production-release-benchmark-success",
        "production-release-missing-target-runtime",
        "production-release-missing-source-coverage",
        "production-release-missing-product-acceptance",
        "production-release-missing-security-privacy",
        "production-release-missing-publication",
        "production-release-missing-worker-orchestration",
        "production-release-missing-ops-runtime",
        "production-release-slo-violation",
        "production-release-blocker-present",
        "production-release-false-ready",
        "production-release-replay-mismatch",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["production-release-benchmark-success"].negative_case
    assert FIXTURE_ORACLES["production-release-replay-mismatch"].negative_case
    for fixture_id in expected:
        assert FIXTURE_ORACLES[fixture_id].expected_release_ref


def test_production_benchmark_release_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["production_benchmark_release_gate"]
    assert area.coverage_status == "materialized"
    assert "ProductionBenchmarkReleaseReport" in area.materialized_contract_refs
    assert "TargetRuntimeReport" in area.materialized_contract_refs
    assert "OpsReplayObservabilityRuntimeReport" in area.materialized_contract_refs
    assert area.followup_spec_gate is None
