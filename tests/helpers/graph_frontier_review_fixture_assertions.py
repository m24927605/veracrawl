from __future__ import annotations

from veracrawl.cli.graph_frontier_review import GraphFrontierReviewFixtureRunReport
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphFrontierDecisionType,
    GraphReviewRouteType,
)


def assert_graph_frontier_review_success(
    report: GraphFrontierReviewFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "graph_frontier_review_completed"
    assert report.graph_signal_refs
    assert report.frontier_decision_refs
    assert report.review_route_decision_refs
    assert report.frontier_item_refs
    assert report.review_item_refs
    assert report.source_graph_refs
    assert report.explanation_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert set(report.frontier_decision_types) == {
        GraphFrontierDecisionType.PRIORITIZE,
        GraphFrontierDecisionType.RETRY,
        GraphFrontierDecisionType.RETIRE,
        GraphFrontierDecisionType.EXPAND,
    }
    assert set(report.review_route_types) == {GraphReviewRouteType.ROUTE_TO_REVIEW}
    assert not report.graph_signal_as_evidence_refs
    assert not report.missing_ref_fields


def assert_graph_frontier_review_needs_review(
    report: GraphFrontierReviewFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "graph_frontier_review_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_graph_frontier_review_negative(
    report: GraphFrontierReviewFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert missing_field in report.missing_ref_fields
