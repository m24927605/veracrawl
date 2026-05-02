from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, GraphEdgeType, GraphNodeType
from veracrawl.contracts.graph import (
    GraphBuildReport,
    GraphEdge,
    GraphEdgeProvenance,
    GraphNode,
)


def test_graph_node_edge_and_provenance_require_refs() -> None:
    node = GraphNode(
        id="graph-node:unit:url:a",
        run_ref="run:unit",
        node_key="https://example.test/",
        node_type=GraphNodeType.URL,
        label="example.test/",
        source_ref="link-provenance:unit:1",
    )
    assert node.node_type == GraphNodeType.URL
    edge = GraphEdge(
        id="graph-edge:unit:hyperlink:a",
        run_ref="run:unit",
        from_node_ref="graph-node:unit:url:a",
        to_node_ref="graph-node:unit:url:b",
        edge_type=GraphEdgeType.HYPERLINK,
        provenance_ref="graph-provenance:unit:edge",
    )
    assert edge.edge_type == GraphEdgeType.HYPERLINK
    provenance = GraphEdgeProvenance(
        id="graph-provenance:unit:edge",
        edge_ref=edge.id,
        input_refs=["link-provenance:unit:1"],
        policy_decision_refs=["policy:unit:graph"],
    )
    assert not provenance.evidence_ref_allowed
    with pytest.raises(ValidationError):
        GraphEdgeProvenance(
            id="graph-provenance:unit:bad",
            edge_ref=edge.id,
            input_refs=[],
            policy_decision_refs=["policy:unit:graph"],
        )


def test_graph_report_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        GraphBuildReport(
            id="graph-report:bad",
            run_ref="run:bad",
            operator_status="graph_build_completed",
            completion_result=CompletenessResult.PASS,
        )
