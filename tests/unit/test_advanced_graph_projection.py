from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, GraphSignalType
from veracrawl.graph.projection import build_advanced_graph_projection


def test_advanced_projection_builds_replayable_projection_records() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-projection",
        scenario="projection-rebuild-success",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a", "graph-node:unit:url:b"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        source_output_refs=["published-output:unit:1"],
        evidence_packet_refs=["evidence-packet:unit:1"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.projection_spec
    assert result.rebuild_job
    assert result.watermark
    assert result.delta_report
    assert result.quality_report
    assert result.signals
    assert result.temporal_records


def test_graph_signal_frontier_review_scenario_emits_both_signal_types() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-signals",
        scenario="graph-signal-frontier-review",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert {signal.signal_type for signal in result.signals} == {
        GraphSignalType.FRONTIER_PRIORITY,
        GraphSignalType.REVIEW_ROUTE,
    }
    assert all(not signal.evidence_ref_allowed for signal in result.signals)


def test_projection_mismatch_emits_mismatch_report_and_fails() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-mismatch",
        scenario="projection-mismatch",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "projection_mismatch"
    assert result.mismatch_report
    assert result.report.mismatch_report_ref == result.mismatch_report.id


def test_projection_missing_watermark_fails_without_pass_claim() -> None:
    result = build_advanced_graph_projection(
        fixture_id="unit-missing-watermark",
        scenario="projection-missing-watermark",
        base_manifest_ref="graph-manifest:unit",
        graph_node_refs=["graph-node:unit:url:a"],
        graph_edge_refs=["graph-edge:unit:hyperlink:a"],
        policy_decision_refs=["policy:unit:advanced-graph"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "missing_projection_watermark"
    assert result.watermark is None
