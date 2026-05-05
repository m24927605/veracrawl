"""Scheduler-owned adoption of crawler optimization frontier decisions."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import (
    RuntimeFrontierOptimizationDecision,
    SchedulerOptimizationIntegration,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrawlerOptimizationFailureType,
)


def integrate_scheduler_optimization(
    *,
    fixture_id: str,
    run_ref: Ref,
    frontier_decisions: list[RuntimeFrontierOptimizationDecision],
    min_enqueue_priority: int = 1,
) -> SchedulerOptimizationIntegration:
    if not frontier_decisions:
        return SchedulerOptimizationIntegration(
            id=f"scheduler-optimization-integration:{fixture_id}",
            fixture_id=fixture_id,
            run_ref=run_ref,
            failure_type=CrawlerOptimizationFailureType.MISSING_FRONTIER_SCORE,
            diagnostics=["scheduler optimization integration missing frontier decisions"],
            completion_result=CompletenessResult.FAIL,
        )

    enqueue_refs: list[Ref] = []
    blocked_refs: list[Ref] = []
    retired_refs: list[Ref] = []
    stop_reason_refs: list[Ref] = []
    priority_refs: list[Ref] = []
    policy_refs: list[Ref] = []
    for decision in frontier_decisions:
        policy_refs.extend(decision.policy_decision_refs)
        if (
            decision.scheduler_action == "enqueue"
            and decision.scheduler_priority >= min_enqueue_priority
        ):
            enqueue_refs.append(f"scheduler-enqueue:{decision.id}")
            priority_refs.append(f"scheduler-priority:{decision.id}:{decision.scheduler_priority}")
        elif decision.scheduler_action == "block":
            blocked_refs.append(f"scheduler-block:{decision.id}")
            stop_reason_refs.extend(decision.blocked_reason_refs)
        else:
            retired_refs.append(f"scheduler-retire:{decision.id}")
            stop_reason_refs.append(f"stop-reason:{decision.id}:{decision.scheduler_action}")

    return SchedulerOptimizationIntegration(
        id=f"scheduler-optimization-integration:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        frontier_decision_refs=[decision.id for decision in frontier_decisions],
        enqueue_refs=enqueue_refs,
        blocked_refs=blocked_refs,
        retired_refs=retired_refs,
        stop_reason_refs=sorted(set(stop_reason_refs)),
        scheduler_priority_refs=priority_refs,
        policy_decision_refs=sorted(set(policy_refs))
        or [f"policy:scheduler-opt:{fixture_id}:allow"],
        command_record_refs=[f"command:scheduler-opt:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:scheduler-opt:{fixture_id}"],
        outbox_refs=[f"outbox:scheduler-opt:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:scheduler-opt:{fixture_id}",
    )
