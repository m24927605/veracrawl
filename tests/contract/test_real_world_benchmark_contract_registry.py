from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_real_world_benchmark_contracts_registered() -> None:
    for contract in [
        "RealWorldBenchmarkSiteSpec",
        "RealWorldBenchmarkSiteObservation",
        "RealWorldBenchmarkRunReport",
        "RealWorldBenchmarkCorpusManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_real_world_benchmark_commands_events_and_fixture_registered() -> None:
    expected = {
        "record_real_world_benchmark_site_observation": (
            "real_world_benchmark_site_observed"
        ),
        "record_real_world_benchmark_run_report": "real_world_benchmark_run_reported",
        "record_real_world_benchmark_corpus_manifest": (
            "real_world_benchmark_corpus_manifest_recorded"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    for fixture_id in {"real-world-public-corpus", "top-ecommerce-public-corpus"}:
        fixture = FIXTURE_ORACLES[fixture_id]
        assert fixture.expected_real_world_benchmark_ref
        assert fixture.expected_replay_ref
        assert not fixture.negative_case


def test_real_world_benchmark_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["real_world_benchmark_corpus_gate"]
    assert area.coverage_status == "materialized"
    assert "RealWorldBenchmarkRunReport" in area.materialized_contract_refs
    assert "LiveHttpAcquisitionReport" in area.materialized_contract_refs
