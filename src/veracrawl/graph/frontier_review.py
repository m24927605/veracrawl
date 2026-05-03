"""Deterministic graph-driven frontier and review runtime gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    FrontierItemStatus,
    GraphFrontierDecisionType,
    GraphFrontierReviewFailureType,
    GraphReviewRouteType,
    GraphSignalType,
    ReviewItemStatus,
    ReviewItemType,
    ReviewPriority,
)
from veracrawl.contracts.graph import (
    GraphFrontierDecisionRecord,
    GraphFrontierReviewRuntimeReport,
    GraphReviewRouteDecisionRecord,
    GraphSignal,
)
from veracrawl.contracts.ops import ReviewItem
from veracrawl.contracts.scheduler import FrontierItem


@dataclass(frozen=True)
class GraphFrontierReviewRuntimeResult:
    graph_signals: list[GraphSignal]
    frontier_items: list[FrontierItem]
    review_items: list[ReviewItem]
    frontier_decisions: list[GraphFrontierDecisionRecord]
    review_route_decisions: list[GraphReviewRouteDecisionRecord]
    report: GraphFrontierReviewRuntimeReport


_FAILURES: dict[str, tuple[GraphFrontierReviewFailureType, str]] = {
    "graph-frontier-review-signal-as-evidence": (
        GraphFrontierReviewFailureType.GRAPH_SIGNAL_AS_EVIDENCE,
        "graph_signal_as_evidence_refs",
    ),
    "graph-frontier-review-missing-source-graph": (
        GraphFrontierReviewFailureType.MISSING_SOURCE_GRAPH_REFS,
        "source_graph_refs",
    ),
    "graph-frontier-review-missing-explanation": (
        GraphFrontierReviewFailureType.MISSING_EXPLANATION_REF,
        "explanation_ref",
    ),
    "graph-frontier-review-unauthorized-frontier-mutation": (
        GraphFrontierReviewFailureType.UNAUTHORIZED_FRONTIER_MUTATION,
        "unauthorized_frontier_mutation_refs",
    ),
    "graph-frontier-review-missing-review-route": (
        GraphFrontierReviewFailureType.MISSING_REVIEW_ROUTE,
        "review_route_decision_refs",
    ),
    "graph-frontier-review-missing-replay": (
        GraphFrontierReviewFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "graph-frontier-review-unsupported-signal": (
        GraphFrontierReviewFailureType.UNSUPPORTED_SIGNAL,
        "unsupported_signal_refs",
    ),
}


def run_graph_frontier_review_runtime_gate(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> GraphFrontierReviewRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:graph-frontier-review"]
    if scenario == "graph-frontier-review-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    return _success_result(fixture_id=fixture_id, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> GraphFrontierReviewRuntimeResult:
    source_graph_refs = [
        f"graph-manifest:{fixture_id}:advanced",
        f"graph-node:{fixture_id}:home",
        f"graph-edge:{fixture_id}:home-products",
    ]
    signals = [
        _signal(
            fixture_id,
            signal_type=GraphSignalType.FRONTIER_PRIORITY,
            subject_ref=f"frontier-item:{fixture_id}:priority",
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        ),
        _signal(
            fixture_id,
            signal_type=GraphSignalType.DRIFT_RISK,
            subject_ref=f"frontier-item:{fixture_id}:retry",
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        ),
        _signal(
            fixture_id,
            signal_type=GraphSignalType.DEDUP_HINT,
            subject_ref=f"frontier-item:{fixture_id}:retire",
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        ),
        _signal(
            fixture_id,
            signal_type=GraphSignalType.FRONTIER_PRIORITY,
            subject_ref=f"frontier-item:{fixture_id}:expand",
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
            suffix="expand",
        ),
        _signal(
            fixture_id,
            signal_type=GraphSignalType.REVIEW_ROUTE,
            subject_ref=f"review-item:{fixture_id}:graph-signal-use",
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        ),
    ]
    frontier_items = [
        _frontier_item(fixture_id, "priority", priority=30, policy_refs=policy_refs),
        _frontier_item(
            fixture_id,
            "retry",
            priority=45,
            status=FrontierItemStatus.RETRYING,
            policy_refs=policy_refs,
        ),
        _frontier_item(
            fixture_id,
            "retire",
            priority=10,
            status=FrontierItemStatus.RELEASED,
            policy_refs=policy_refs,
        ),
        _frontier_item(fixture_id, "expand", priority=50, policy_refs=policy_refs),
        _frontier_item(fixture_id, "generated", priority=55, policy_refs=policy_refs),
    ]
    review_items = [_review_item(fixture_id, policy_refs=policy_refs)]
    frontier_decisions = [
        _frontier_decision(
            fixture_id,
            graph_signal=signals[0],
            decision_type=GraphFrontierDecisionType.PRIORITIZE,
            frontier_item_ref=frontier_items[0].id,
            before_priority=frontier_items[0].priority,
            after_priority=90,
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        ),
        _frontier_decision(
            fixture_id,
            graph_signal=signals[1],
            decision_type=GraphFrontierDecisionType.RETRY,
            frontier_item_ref=frontier_items[1].id,
            before_priority=frontier_items[1].priority,
            after_priority=65,
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
            retry_refs=[frontier_items[1].id],
        ),
        _frontier_decision(
            fixture_id,
            graph_signal=signals[2],
            decision_type=GraphFrontierDecisionType.RETIRE,
            frontier_item_ref=frontier_items[2].id,
            before_priority=frontier_items[2].priority,
            after_priority=0,
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
            retired_refs=[frontier_items[2].id],
        ),
        _frontier_decision(
            fixture_id,
            graph_signal=signals[3],
            decision_type=GraphFrontierDecisionType.EXPAND,
            frontier_item_ref=frontier_items[3].id,
            before_priority=frontier_items[3].priority,
            after_priority=75,
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
            generated_refs=[frontier_items[4].id],
        ),
    ]
    review_decisions = [
        _review_decision(
            fixture_id,
            graph_signal=signals[4],
            review_item_ref=review_items[0].id,
            source_graph_refs=source_graph_refs,
            policy_refs=policy_refs,
        )
    ]
    report = _report(
        fixture_id=fixture_id,
        signals=signals,
        frontier_items=frontier_items,
        review_items=review_items,
        frontier_decisions=frontier_decisions,
        review_decisions=review_decisions,
        source_graph_refs=source_graph_refs,
        policy_refs=policy_refs,
    )
    return GraphFrontierReviewRuntimeResult(
        graph_signals=signals,
        frontier_items=frontier_items,
        review_items=review_items,
        frontier_decisions=frontier_decisions,
        review_route_decisions=review_decisions,
        report=report,
    )


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> GraphFrontierReviewRuntimeResult:
    report = GraphFrontierReviewRuntimeReport(
        id=f"graph-frontier-review-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:graph-frontier-review"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:graph-store",
            f"missing-runtime:{fixture_id}:scheduler",
            f"missing-runtime:{fixture_id}:review-router",
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="graph_frontier_review_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return GraphFrontierReviewRuntimeResult([], [], [], [], [], report)


def _failure_result(
    *,
    fixture_id: str,
    failure: GraphFrontierReviewFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> GraphFrontierReviewRuntimeResult:
    report = GraphFrontierReviewRuntimeReport(
        id=f"graph-frontier-review-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        graph_signal_as_evidence_refs=(
            [f"graph-signal:{fixture_id}:evidence"]
            if missing_field == "graph_signal_as_evidence_refs"
            else []
        ),
        missing_source_graph_refs=(
            [f"graph-signal:{fixture_id}:missing-source-graph"]
            if missing_field == "source_graph_refs"
            else []
        ),
        missing_explanation_refs=(
            [f"graph-signal:{fixture_id}:missing-explanation"]
            if missing_field == "explanation_ref"
            else []
        ),
        unauthorized_frontier_mutation_refs=(
            [f"frontier-mutation:{fixture_id}:unauthorized"]
            if missing_field == "unauthorized_frontier_mutation_refs"
            else []
        ),
        missing_review_route_refs=(
            [f"graph-signal:{fixture_id}:missing-review-route"]
            if missing_field == "review_route_decision_refs"
            else []
        ),
        unsupported_signal_refs=(
            [f"graph-signal:{fixture_id}:unsupported"]
            if missing_field == "unsupported_signal_refs"
            else []
        ),
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return GraphFrontierReviewRuntimeResult([], [], [], [], [], report)


def _signal(
    fixture_id: str,
    *,
    signal_type: GraphSignalType,
    subject_ref: Ref,
    source_graph_refs: list[Ref],
    policy_refs: list[Ref],
    suffix: str | None = None,
) -> GraphSignal:
    signal_suffix = suffix or signal_type.value
    return GraphSignal(
        id=f"graph-signal:{fixture_id}:{signal_suffix}",
        run_ref=f"run:{fixture_id}",
        signal_type=signal_type,
        subject_ref=subject_ref,
        score=0.82,
        source_graph_refs=source_graph_refs,
        explanation_ref=f"explanation:{fixture_id}:{signal_suffix}",
        policy_decision_refs=policy_refs,
        evidence_ref_allowed=False,
    )


def _frontier_item(
    fixture_id: str,
    slug: str,
    *,
    priority: int,
    status: FrontierItemStatus = FrontierItemStatus.QUEUED,
    policy_refs: list[Ref],
) -> FrontierItem:
    return FrontierItem(
        id=f"frontier-item:{fixture_id}:{slug}",
        run_ref=f"run:{fixture_id}",
        source_ref=f"source:{fixture_id}:{slug}",
        priority=priority,
        status=status,
        policy_decision_refs=policy_refs,
    )


def _review_item(fixture_id: str, *, policy_refs: list[Ref]) -> ReviewItem:
    return ReviewItem(
        id=f"review-item:{fixture_id}:graph-signal-use",
        run_id=f"run:{fixture_id}",
        objective_id=f"objective:{fixture_id}",
        item_type=ReviewItemType.GRAPH_SIGNAL_USE,
        input_refs=[
            f"graph-signal:{fixture_id}:review_route",
            f"graph-manifest:{fixture_id}:advanced",
        ],
        reason="graph signal routed for operator review",
        priority=ReviewPriority.HIGH,
        status=ReviewItemStatus.OPEN,
        policy_decision_refs=policy_refs,
        replay_audit_refs=[f"replay-audit:{fixture_id}:graph-frontier-review"],
    )


def _frontier_decision(
    fixture_id: str,
    *,
    graph_signal: GraphSignal,
    decision_type: GraphFrontierDecisionType,
    frontier_item_ref: Ref,
    before_priority: int,
    after_priority: int,
    source_graph_refs: list[Ref],
    policy_refs: list[Ref],
    generated_refs: list[Ref] | None = None,
    retry_refs: list[Ref] | None = None,
    retired_refs: list[Ref] | None = None,
) -> GraphFrontierDecisionRecord:
    slug = decision_type.value
    return GraphFrontierDecisionRecord(
        id=f"graph-frontier-decision:{fixture_id}:{slug}",
        run_ref=f"run:{fixture_id}",
        graph_signal_ref=graph_signal.id,
        signal_type=graph_signal.signal_type,
        decision_type=decision_type,
        frontier_item_ref=frontier_item_ref,
        before_priority=before_priority,
        after_priority=after_priority,
        generated_frontier_item_refs=generated_refs or [],
        retry_frontier_item_refs=retry_refs or [],
        retired_frontier_item_refs=retired_refs or [],
        source_graph_refs=source_graph_refs,
        explanation_ref=f"explanation:{fixture_id}:frontier:{slug}",
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:frontier:{slug}"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:frontier:{slug}"],
        outbox_refs=[f"outbox:{fixture_id}:frontier:{slug}"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:graph-frontier-review",
        result=CompletenessResult.PASS,
    )


def _review_decision(
    fixture_id: str,
    *,
    graph_signal: GraphSignal,
    review_item_ref: Ref,
    source_graph_refs: list[Ref],
    policy_refs: list[Ref],
) -> GraphReviewRouteDecisionRecord:
    return GraphReviewRouteDecisionRecord(
        id=f"graph-review-route-decision:{fixture_id}:route-to-review",
        run_ref=f"run:{fixture_id}",
        graph_signal_ref=graph_signal.id,
        signal_type=graph_signal.signal_type,
        route_type=GraphReviewRouteType.ROUTE_TO_REVIEW,
        review_item_ref=review_item_ref,
        review_priority=ReviewPriority.HIGH,
        source_graph_refs=source_graph_refs,
        explanation_ref=f"explanation:{fixture_id}:review-route",
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:review-route"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:review-route"],
        outbox_refs=[f"outbox:{fixture_id}:review-route"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:graph-frontier-review",
        result=CompletenessResult.PASS,
    )


def _report(
    *,
    fixture_id: str,
    signals: list[GraphSignal],
    frontier_items: list[FrontierItem],
    review_items: list[ReviewItem],
    frontier_decisions: list[GraphFrontierDecisionRecord],
    review_decisions: list[GraphReviewRouteDecisionRecord],
    source_graph_refs: list[Ref],
    policy_refs: list[Ref],
) -> GraphFrontierReviewRuntimeReport:
    return GraphFrontierReviewRuntimeReport(
        id=f"graph-frontier-review-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        graph_signal_refs=[signal.id for signal in signals],
        frontier_decision_refs=[decision.id for decision in frontier_decisions],
        review_route_decision_refs=[decision.id for decision in review_decisions],
        frontier_item_refs=[item.id for item in frontier_items],
        review_item_refs=[item.id for item in review_items],
        source_graph_refs=source_graph_refs,
        explanation_refs=[
            *[decision.explanation_ref for decision in frontier_decisions],
            *[decision.explanation_ref for decision in review_decisions],
        ],
        policy_decision_refs=policy_refs,
        command_record_refs=[
            ref
            for decision in frontier_decisions
            for ref in decision.command_record_refs
        ]
        + [
            ref
            for decision in review_decisions
            for ref in decision.command_record_refs
        ],
        event_cursor_refs=[
            ref
            for decision in frontier_decisions
            for ref in decision.event_cursor_refs
        ]
        + [
            ref
            for decision in review_decisions
            for ref in decision.event_cursor_refs
        ],
        outbox_refs=[
            ref
            for decision in frontier_decisions
            for ref in decision.outbox_refs
        ]
        + [
            ref
            for decision in review_decisions
            for ref in decision.outbox_refs
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:graph-frontier-review",
        operator_status="graph_frontier_review_completed",
        completion_result=CompletenessResult.PASS,
    )
