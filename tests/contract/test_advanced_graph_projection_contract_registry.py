from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_advanced_graph_projection_contracts_registered() -> None:
    for contract in [
        "ProjectionSpec",
        "ProjectionRebuildJob",
        "ProjectionMismatchReport",
        "GraphSignal",
        "GraphDeltaReport",
        "GraphQualityReport",
        "TemporalGraphProjectionRecord",
        "AdvancedGraphProjectionReport",
        "AdvancedGraphFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_advanced_graph_projection_commands_events_fixtures_registered() -> None:
    assert {"build_advanced_graph_projection", "record_projection_mismatch"}.issubset(
        COMMAND_TYPES
    )
    assert {
        "projection_spec_recorded",
        "projection_rebuild_job_recorded",
        "projection_mismatch_reported",
        "graph_delta_recorded",
        "graph_quality_recorded",
        "graph_signal_recorded",
        "temporal_graph_recorded",
        "advanced_graph_projection_reported",
    }.issubset(EVENT_TYPES)
    assert TARGET_CONTRACT_AREAS["projection"].coverage_status == "materialized"
    assert {
        "projection-rebuild-success",
        "graph-signal-frontier-review",
        "temporal-graph-foundation",
        "projection-missing-watermark",
        "projection-mismatch",
        "graph-signal-as-evidence",
    }.issubset(FIXTURE_ORACLES)


def test_advanced_graph_projection_registry_validation_passes() -> None:
    assert validate_registry().ok
