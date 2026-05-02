from __future__ import annotations

from veracrawl.graph.projection import build_advanced_graph_projection
from veracrawl.review_replay.graph import (
    advanced_graph_replay_passes,
    missing_advanced_graph_replay_refs,
)


def test_advanced_graph_replay_passes_for_complete_projection_report() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-advanced-replay",
        scenario="projection-rebuild-success",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert advanced_graph_replay_passes(result.report)
    assert not missing_advanced_graph_replay_refs(result.report)


def test_advanced_graph_replay_reports_projection_failures() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-advanced-replay-gap",
        scenario="graph-signal-as-evidence",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert not advanced_graph_replay_passes(result.report)
    assert "graph_signal_as_evidence" in missing_advanced_graph_replay_refs(result.report)
