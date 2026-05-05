"""Ops-owned cost, recovery, and regression optimization integration."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import (
    CostCacheBudgetOptimizationIntegration,
    DriftRecoveryFeedbackIntegration,
    OptimizationMetricSlice,
    OptimizationRegressionReleaseGate,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrawlerOptimizationFailureType,
)


def integrate_cost_cache_budget_optimization(
    *,
    fixture_id: str,
    metric_slices: list[OptimizationMetricSlice],
    fetch_cost: float,
    browser_cost: float,
    token_cost: float,
    cache_hit_refs: list[Ref] | None = None,
    stale_cache_refs: list[Ref] | None = None,
    budget_exhausted: bool = False,
) -> CostCacheBudgetOptimizationIntegration:
    stale_refs = stale_cache_refs or []
    failed = bool(stale_refs or budget_exhausted or not metric_slices)
    return CostCacheBudgetOptimizationIntegration(
        id=f"cost-cache-budget-optimization-integration:{fixture_id}",
        fixture_id=fixture_id,
        fetch_cost=fetch_cost,
        browser_cost=browser_cost,
        token_cost=token_cost,
        cache_hit_refs=cache_hit_refs or [],
        stale_cache_refs=stale_refs,
        metric_slice_refs=[metric.id for metric in metric_slices],
        budget_exhausted=budget_exhausted,
        diagnostics=(
            ["cost/cache budget integration failed"]
            if failed
            else ["cost/cache budget integration passed"]
        ),
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        policy_decision_refs=[f"policy:cost-cache-opt:{fixture_id}:allow"],
        command_record_refs=[f"command:cost-cache-opt:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:cost-cache-opt:{fixture_id}"],
        outbox_refs=[f"outbox:cost-cache-opt:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:cost-cache-opt:{fixture_id}",
        failure_type=CrawlerOptimizationFailureType.COST_BUDGET_EXCEEDED if failed else None,
    )


def integrate_drift_recovery_feedback(
    *,
    fixture_id: str,
    drift_type: str,
    affected_ref: Ref,
    retry_class: str,
    repair_outcome: str,
    memory_advisory_refs: list[Ref] | None = None,
    unsafe_recovery_refs: list[Ref] | None = None,
) -> DriftRecoveryFeedbackIntegration:
    unsafe_refs = unsafe_recovery_refs or []
    failed = bool(unsafe_refs)
    return DriftRecoveryFeedbackIntegration(
        id=f"drift-recovery-feedback-integration:{fixture_id}",
        fixture_id=fixture_id,
        drift_type=drift_type,
        affected_ref=affected_ref,
        retry_class=retry_class,
        repair_outcome=repair_outcome,
        memory_advisory_refs=memory_advisory_refs or [],
        unsafe_recovery_refs=unsafe_refs,
        diagnostics=(
            ["unsafe recovery blocked"] if failed else ["drift recovery feedback recorded"]
        ),
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        policy_decision_refs=[f"policy:drift-recovery-opt:{fixture_id}:allow"],
        command_record_refs=[f"command:drift-recovery-opt:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:drift-recovery-opt:{fixture_id}"],
        outbox_refs=[f"outbox:drift-recovery-opt:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:drift-recovery-opt:{fixture_id}",
        failure_type=CrawlerOptimizationFailureType.UNSAFE_RECOVERY_ACTION if failed else None,
    )


def optimization_regression_release_gate(
    *,
    fixture_id: str,
    lower_integration_refs: list[Ref],
    metric_slice_refs: list[Ref],
    missing_lower_integration_refs: list[Ref] | None = None,
    false_ready_guard_refs: list[Ref] | None = None,
    diagnostics: list[str] | None = None,
) -> OptimizationRegressionReleaseGate:
    missing = missing_lower_integration_refs or []
    false_ready = false_ready_guard_refs or []
    failed = bool(missing or false_ready or not lower_integration_refs or not metric_slice_refs)
    return OptimizationRegressionReleaseGate(
        id=f"optimization-regression-release-gate:{fixture_id}",
        fixture_id=fixture_id,
        lower_integration_refs=lower_integration_refs,
        missing_lower_integration_refs=missing,
        metric_slice_refs=metric_slice_refs,
        false_ready_guard_refs=false_ready,
        diagnostics=diagnostics
        or (["optimization regression release gate failed"] if failed else []),
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        policy_decision_refs=[f"policy:optimization-regression:{fixture_id}:allow"],
        command_record_refs=[f"command:optimization-regression:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:optimization-regression:{fixture_id}"],
        outbox_refs=[f"outbox:optimization-regression:{fixture_id}"],
        replay_bundle_ref=f"replay-bundle:optimization-regression:{fixture_id}",
        failure_type=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS if failed else None,
    )
