from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, GraphSignalType
from veracrawl.contracts.graph import GraphSignal
from veracrawl.graph.projection import build_advanced_graph_projection


def test_graph_signal_contract_rejects_evidence_authority() -> None:
    with pytest.raises(ValidationError):
        GraphSignal(
            id="graph-signal:evidence",
            run_ref="run:evidence",
            signal_type=GraphSignalType.QUALITY_WARNING,
            subject_ref="published-output:evidence",
            score=0.1,
            source_graph_refs=["graph-manifest:evidence"],
            explanation_ref="explanation:evidence",
            policy_decision_refs=["policy:evidence:graph"],
            evidence_ref_allowed=True,
        )


def test_graph_signal_as_evidence_fixture_path_fails() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-signal-evidence",
        scenario="graph-signal-as-evidence",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "graph_signal_as_evidence"
    assert not result.report.watermark_ref
