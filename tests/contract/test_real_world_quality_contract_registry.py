from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_real_world_quality_contracts_registered() -> None:
    for contract in [
        "RealWorldQualityTargetSpec",
        "RealWorldQualitySiteObservation",
        "RealWorldQualityPatternCoverageRecord",
        "RealWorldQualityCorpusReport",
        "RealWorldQualityCorpusManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_real_world_quality_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_real_world_quality_site_observation": "real_world_quality_site_observed",
        "record_real_world_quality_pattern_coverage": (
            "real_world_quality_pattern_coverage_recorded"
        ),
        "record_real_world_quality_corpus_report": "real_world_quality_corpus_reported",
        "record_real_world_quality_corpus_manifest": (
            "real_world_quality_corpus_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    fixture = FIXTURE_ORACLES["real-world-quality-corpus"]
    assert fixture.expected_real_world_benchmark_ref
    assert fixture.expected_replay_ref
    assert not fixture.negative_case
    assert FIXTURE_ORACLES["real-world-quality-target-drift"].negative_case


def test_real_world_quality_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["real_world_quality_corpus_gate"]
    assert area.coverage_status == "materialized"
    assert "RealWorldQualityCorpusReport" in area.materialized_contract_refs
    assert "RealWorldBenchmarkRunReport" in area.materialized_contract_refs
