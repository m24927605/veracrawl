from __future__ import annotations

from veracrawl.cli.graph import GraphFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_graph_success(report: GraphFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "graph_build_completed"
    assert report.manifest_ref
    assert report.node_refs
    assert report.edge_refs
    assert report.provenance_refs
    assert report.watermark_ref
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs


def assert_graph_negative(
    report: GraphFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_report_refs
    assert report.missing_ref_fields
    assert not report.manifest_ref
