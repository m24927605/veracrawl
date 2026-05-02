from __future__ import annotations

from veracrawl.graph.build import LinkInput, build_basic_site_graph


def test_graph_as_evidence_is_rejected() -> None:
    result = build_basic_site_graph(
        fixture_id="unit-graph-evidence",
        scenario="graph-as-evidence",
        link_inputs=[LinkInput("https://example.test/", "https://example.test/a", "link:1")],
        policy_decision_refs=["policy:unit-graph-evidence:graph"],
    )
    assert result.report.operator_status == "graph_as_evidence"
    assert not result.report.manifest_ref
