from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphFrontierDecisionType,
    GraphFrontierReviewFailureType,
    GraphReviewRouteType,
    GraphSignalType,
    ReviewPriority,
)
from veracrawl.contracts.graph import (
    GraphFrontierDecisionRecord,
    GraphFrontierReviewFixtureManifest,
    GraphFrontierReviewRuntimeReport,
    GraphReviewRouteDecisionRecord,
)


def _frontier_decision(
    decision_type: GraphFrontierDecisionType = GraphFrontierDecisionType.PRIORITIZE,
) -> GraphFrontierDecisionRecord:
    return GraphFrontierDecisionRecord(
        id=f"graph-frontier-decision:{decision_type.value}",
        run_ref="run:contract",
        graph_signal_ref=f"graph-signal:{decision_type.value}",
        signal_type=GraphSignalType.FRONTIER_PRIORITY,
        decision_type=decision_type,
        frontier_item_ref=f"frontier-item:{decision_type.value}",
        before_priority=10,
        after_priority=20,
        generated_frontier_item_refs=(
            ["frontier-item:generated"]
            if decision_type == GraphFrontierDecisionType.EXPAND
            else []
        ),
        retry_frontier_item_refs=(
            ["frontier-item:retry"]
            if decision_type == GraphFrontierDecisionType.RETRY
            else []
        ),
        retired_frontier_item_refs=(
            ["frontier-item:retire"]
            if decision_type == GraphFrontierDecisionType.RETIRE
            else []
        ),
        source_graph_refs=["graph-manifest:contract"],
        explanation_ref=f"explanation:{decision_type.value}",
        policy_decision_refs=["policy:contract"],
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay:contract",
        result=CompletenessResult.PASS,
    )


def _review_decision() -> GraphReviewRouteDecisionRecord:
    return GraphReviewRouteDecisionRecord(
        id="graph-review-route-decision:contract",
        run_ref="run:contract",
        graph_signal_ref="graph-signal:review",
        signal_type=GraphSignalType.REVIEW_ROUTE,
        route_type=GraphReviewRouteType.ROUTE_TO_REVIEW,
        review_item_ref="review-item:contract",
        review_priority=ReviewPriority.HIGH,
        source_graph_refs=["graph-manifest:contract"],
        explanation_ref="explanation:review",
        policy_decision_refs=["policy:contract"],
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay:contract",
        result=CompletenessResult.PASS,
    )


def test_frontier_decision_rejects_graph_signal_as_evidence() -> None:
    with pytest.raises(ValidationError):
        GraphFrontierDecisionRecord(
            **(_frontier_decision().model_dump() | {"evidence_ref_allowed": True})
        )


def test_frontier_decision_requires_decision_specific_refs() -> None:
    with pytest.raises(ValidationError):
        GraphFrontierDecisionRecord(
            **(
                _frontier_decision(GraphFrontierDecisionType.EXPAND).model_dump()
                | {"generated_frontier_item_refs": []}
            )
        )
    with pytest.raises(ValidationError):
        GraphFrontierDecisionRecord(
            **(
                _frontier_decision(GraphFrontierDecisionType.RETRY).model_dump()
                | {"retry_frontier_item_refs": []}
            )
        )
    with pytest.raises(ValidationError):
        GraphFrontierDecisionRecord(
            **(
                _frontier_decision(GraphFrontierDecisionType.RETIRE).model_dump()
                | {"retired_frontier_item_refs": []}
            )
        )


def test_frontier_decision_rejects_unsupported_signal_type() -> None:
    with pytest.raises(ValidationError):
        GraphFrontierDecisionRecord(
            **(_frontier_decision().model_dump() | {"signal_type": GraphSignalType.REVIEW_ROUTE})
        )


def test_review_route_decision_rejects_graph_signal_as_evidence() -> None:
    with pytest.raises(ValidationError):
        GraphReviewRouteDecisionRecord(
            **(_review_decision().model_dump() | {"evidence_ref_allowed": True})
        )


def test_review_route_decision_rejects_unsupported_signal_type() -> None:
    with pytest.raises(ValidationError):
        GraphReviewRouteDecisionRecord(
            **(_review_decision().model_dump() | {"signal_type": GraphSignalType.DEDUP_HINT})
        )


def test_graph_frontier_review_report_requires_frontier_and_review_refs() -> None:
    with pytest.raises(ValidationError):
        GraphFrontierReviewRuntimeReport(
            id="graph-frontier-review-report:bad",
            run_ref="run:bad",
            graph_signal_refs=["graph-signal:frontier"],
            frontier_decision_refs=["graph-frontier-decision:bad"],
            review_route_decision_refs=[],
            frontier_item_refs=["frontier-item:bad"],
            review_item_refs=["review-item:bad"],
            source_graph_refs=["graph-manifest:bad"],
            explanation_refs=["explanation:bad"],
            policy_decision_refs=["policy:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay:bad",
            operator_status="graph_frontier_review_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_graph_frontier_review_report_accepts_complete_pass() -> None:
    report = GraphFrontierReviewRuntimeReport(
        id="graph-frontier-review-report:ok",
        run_ref="run:ok",
        graph_signal_refs=["graph-signal:frontier", "graph-signal:review"],
        frontier_decision_refs=["graph-frontier-decision:ok"],
        review_route_decision_refs=["graph-review-route-decision:ok"],
        frontier_item_refs=["frontier-item:ok"],
        review_item_refs=["review-item:ok"],
        source_graph_refs=["graph-manifest:ok"],
        explanation_refs=["explanation:ok"],
        policy_decision_refs=["policy:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay:ok",
        operator_status="graph_frontier_review_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS


def test_graph_frontier_review_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        GraphFrontierReviewFixtureManifest(
            id="graph-frontier-review-bad",
            scenario="graph-frontier-review-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=GraphFrontierReviewFailureType.GRAPH_SIGNAL_AS_EVIDENCE,
            negative_case=True,
        )
