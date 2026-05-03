from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphFrontierDecisionType,
    GraphFrontierReviewFailureType,
    GraphReviewRouteType,
)
from veracrawl.graph.frontier_review import run_graph_frontier_review_runtime_gate


def test_graph_frontier_review_gate_success_requires_all_decision_families() -> None:
    result = run_graph_frontier_review_runtime_gate(
        fixture_id="unit",
        scenario="graph-frontier-review-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
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
    assert {decision.decision_type for decision in result.frontier_decisions} == {
        GraphFrontierDecisionType.PRIORITIZE,
        GraphFrontierDecisionType.RETRY,
        GraphFrontierDecisionType.RETIRE,
        GraphFrontierDecisionType.EXPAND,
    }
    assert {decision.route_type for decision in result.review_route_decisions} == {
        GraphReviewRouteType.ROUTE_TO_REVIEW
    }


def test_graph_frontier_review_runtime_unavailable_needs_review() -> None:
    result = run_graph_frontier_review_runtime_gate(
        fixture_id="unit-no-runtime",
        scenario="graph-frontier-review-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_graph_frontier_review_negative_scenarios_fail() -> None:
    expectations = {
        "graph-frontier-review-signal-as-evidence": (
            GraphFrontierReviewFailureType.GRAPH_SIGNAL_AS_EVIDENCE
        ),
        "graph-frontier-review-missing-source-graph": (
            GraphFrontierReviewFailureType.MISSING_SOURCE_GRAPH_REFS
        ),
        "graph-frontier-review-missing-explanation": (
            GraphFrontierReviewFailureType.MISSING_EXPLANATION_REF
        ),
        "graph-frontier-review-unauthorized-frontier-mutation": (
            GraphFrontierReviewFailureType.UNAUTHORIZED_FRONTIER_MUTATION
        ),
        "graph-frontier-review-missing-review-route": (
            GraphFrontierReviewFailureType.MISSING_REVIEW_ROUTE
        ),
        "graph-frontier-review-missing-replay": (
            GraphFrontierReviewFailureType.MISSING_REPLAY_REFS
        ),
        "graph-frontier-review-unsupported-signal": (
            GraphFrontierReviewFailureType.UNSUPPORTED_SIGNAL
        ),
    }
    for scenario, failure in expectations.items():
        result = run_graph_frontier_review_runtime_gate(
            fixture_id=scenario,
            scenario=scenario,
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
