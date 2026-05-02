from __future__ import annotations

from veracrawl.graph.build import LinkInput, build_basic_site_graph
from veracrawl.review_replay.graph import graph_replay_passes, missing_graph_replay_refs


def test_graph_replay_passes_for_complete_report() -> None:
    result = build_basic_site_graph(
        fixture_id="unit-replay-graph",
        scenario="url-hyperlink",
        link_inputs=[LinkInput("https://example.test/", "https://example.test/a", "link:1")],
        policy_decision_refs=["policy:unit-replay-graph:graph"],
    )
    assert graph_replay_passes(result.report)


def test_graph_replay_reports_failure_markers() -> None:
    result = build_basic_site_graph(
        fixture_id="unit-replay-gap-graph",
        scenario="missing-input",
        link_inputs=[],
        policy_decision_refs=["policy:unit-replay-gap-graph:graph"],
    )
    assert "missing_graph_input" in missing_graph_replay_refs(result.report)
