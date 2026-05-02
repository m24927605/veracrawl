from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_graph_contracts_registered() -> None:
    for contract in [
        "GraphNode",
        "GraphEdge",
        "GraphEdgeProvenance",
        "GraphBuildManifest",
        "ProjectionWatermark",
        "GraphBuildReport",
        "GraphFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_graph_commands_events_fixtures_registered() -> None:
    assert {"build_basic_site_graph", "record_graph_report"}.issubset(COMMAND_TYPES)
    assert {
        "graph_node_recorded",
        "graph_edge_recorded",
        "graph_manifest_recorded",
        "graph_report_recorded",
    }.issubset(EVENT_TYPES)
    assert TARGET_CONTRACT_AREAS["graph"].coverage_status == "materialized"
    assert {
        "graph-url-hyperlink",
        "graph-canonical-redirect",
        "graph-page-structure",
        "graph-missing-input",
        "graph-rebuild-mismatch",
        "graph-as-evidence",
    }.issubset(FIXTURE_ORACLES)


def test_graph_registry_validation_passes() -> None:
    assert validate_registry().ok
