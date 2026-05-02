from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, GraphEdgeType
from veracrawl.graph.build import LinkInput, build_basic_site_graph


def test_graph_build_deduplicates_hyperlink_edges_and_keeps_provenance() -> None:
    result = build_basic_site_graph(
        fixture_id="unit-graph",
        scenario="url-hyperlink",
        link_inputs=[
            LinkInput("https://example.test/", "https://example.test/a", "link:1"),
            LinkInput("https://example.test/", "https://example.test/a", "link:2"),
        ],
        policy_decision_refs=["policy:unit-graph:graph"],
    )
    assert result.report.completion_result == CompletenessResult.PASS
    hyperlink_edges = [edge for edge in result.edges if edge.edge_type == GraphEdgeType.HYPERLINK]
    assert len(hyperlink_edges) == 1
    assert result.provenances[0].input_refs == ["link:1", "link:2"]


def test_graph_build_creates_canonical_redirect_and_page_structure_edges() -> None:
    result = build_basic_site_graph(
        fixture_id="unit-structure",
        scenario="page-structure",
        link_inputs=[],
        redirect_inputs=[
            LinkInput("http://example.test/", "https://example.test/", "redirect:1")
        ],
        canonical_inputs=[
            LinkInput(
                "https://example.test/?ref=dup",
                "https://example.test/",
                "canonical:1",
            )
        ],
        page_type_refs=["page-type:unit"],
        site_model_refs=["site-model:unit"],
        policy_decision_refs=["policy:unit-structure:graph"],
    )
    edge_types = {edge.edge_type for edge in result.edges}
    assert {
        GraphEdgeType.REDIRECT,
        GraphEdgeType.CANONICAL,
        GraphEdgeType.PAGE_STRUCTURE,
    }.issubset(edge_types)
