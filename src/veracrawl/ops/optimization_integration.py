"""Ops-owned cost, recovery, and regression optimization integration."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import (
    CostCacheBudgetOptimizationIntegration,
    DedupeIdentityOptimizationIntegration,
    DriftRecoveryFeedbackIntegration,
    ExtractVerifyOptimizationIntegration,
    NormalizeOptimizationIntegration,
    OptimizationMetricSlice,
    OptimizationRegressionReleaseGate,
    RankingPublicationOptimizationIntegration,
    SchedulerOptimizationIntegration,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrawlerOptimizationFailureType,
)
from veracrawl.review_replay.crawler_optimization_owner_integration import (
    missing_cost_cache_budget_integration_replay_refs,
    missing_dedupe_identity_integration_replay_refs,
    missing_drift_recovery_feedback_replay_refs,
    missing_extract_verify_integration_replay_refs,
    missing_normalize_integration_replay_refs,
    missing_ranking_publication_integration_replay_refs,
    missing_scheduler_integration_replay_refs,
)

LowerOptimizationIntegration: TypeAlias = (
    SchedulerOptimizationIntegration
    | NormalizeOptimizationIntegration
    | ExtractVerifyOptimizationIntegration
    | DedupeIdentityOptimizationIntegration
    | RankingPublicationOptimizationIntegration
    | CostCacheBudgetOptimizationIntegration
    | DriftRecoveryFeedbackIntegration
)

REQUIRED_LOWER_INTEGRATION_KINDS: tuple[str, ...] = (
    "scheduler",
    "normalize",
    "extract_verify",
    "dedupe_identity",
    "ranking_publication",
    "cost_cache_budget",
    "drift_recovery",
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
    present_lower_integration_kinds: list[str] | None = None,
    missing_lower_integration_refs: list[Ref] | None = None,
    failed_lower_integration_refs: list[Ref] | None = None,
    replay_gap_refs: list[Ref] | None = None,
    metric_regression_refs: list[Ref] | None = None,
    false_ready_guard_refs: list[Ref] | None = None,
    diagnostics: list[str] | None = None,
) -> OptimizationRegressionReleaseGate:
    present_kinds = sorted(set(present_lower_integration_kinds or []))
    missing_kind_refs = [
        f"lower-integration-kind:{kind}:missing"
        for kind in REQUIRED_LOWER_INTEGRATION_KINDS
        if kind not in present_kinds
    ]
    missing = missing_lower_integration_refs or []
    failed_lower = failed_lower_integration_refs or []
    replay_gaps = replay_gap_refs or []
    metric_regressions = metric_regression_refs or []
    false_ready = false_ready_guard_refs or []
    all_missing = [*missing, *missing_kind_refs]
    failed = bool(
        all_missing
        or failed_lower
        or replay_gaps
        or metric_regressions
        or false_ready
        or not lower_integration_refs
        or not metric_slice_refs
    )
    return OptimizationRegressionReleaseGate(
        id=f"optimization-regression-release-gate:{fixture_id}",
        fixture_id=fixture_id,
        required_lower_integration_kinds=list(REQUIRED_LOWER_INTEGRATION_KINDS),
        present_lower_integration_kinds=present_kinds,
        lower_integration_refs=lower_integration_refs,
        missing_lower_integration_refs=all_missing,
        failed_lower_integration_refs=failed_lower,
        replay_gap_refs=replay_gaps,
        metric_slice_refs=metric_slice_refs,
        metric_regression_refs=metric_regressions,
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


def optimization_regression_release_gate_from_reports(
    *,
    fixture_id: str,
    lower_integrations: Sequence[LowerOptimizationIntegration],
    metric_slices: Sequence[OptimizationMetricSlice],
    false_ready_guard_refs: list[Ref] | None = None,
) -> OptimizationRegressionReleaseGate:
    reports_by_kind: dict[str, LowerOptimizationIntegration] = {}
    lower_integration_refs: list[Ref] = []
    failed_lower_refs: list[Ref] = []
    replay_gap_refs: list[Ref] = []
    duplicate_kind_refs: list[Ref] = []

    for integration in lower_integrations:
        kind = _lower_integration_kind(integration)
        lower_integration_refs.append(integration.id)
        if kind in reports_by_kind:
            duplicate_kind_refs.append(
                f"duplicate-lower-integration-kind:{kind}:{integration.id}"
            )
        else:
            reports_by_kind[kind] = integration
        if integration.completion_result != CompletenessResult.PASS:
            failed_lower_refs.append(integration.id)
        replay_gap_refs.extend(
            f"replay-gap:{integration.id}:{missing_ref}"
            for missing_ref in _missing_lower_integration_replay_refs(integration)
        )

    metric_regression_refs = [
        ref
        for metric in metric_slices
        for ref in _metric_regression_refs(metric)
    ]
    return optimization_regression_release_gate(
        fixture_id=fixture_id,
        lower_integration_refs=lower_integration_refs,
        present_lower_integration_kinds=sorted(reports_by_kind),
        missing_lower_integration_refs=[],
        failed_lower_integration_refs=failed_lower_refs,
        replay_gap_refs=replay_gap_refs,
        metric_slice_refs=[metric.id for metric in metric_slices],
        metric_regression_refs=metric_regression_refs,
        false_ready_guard_refs=[*(false_ready_guard_refs or []), *duplicate_kind_refs],
    )


def _lower_integration_kind(integration: LowerOptimizationIntegration) -> str:
    if isinstance(integration, SchedulerOptimizationIntegration):
        return "scheduler"
    if isinstance(integration, NormalizeOptimizationIntegration):
        return "normalize"
    if isinstance(integration, ExtractVerifyOptimizationIntegration):
        return "extract_verify"
    if isinstance(integration, DedupeIdentityOptimizationIntegration):
        return "dedupe_identity"
    if isinstance(integration, RankingPublicationOptimizationIntegration):
        return "ranking_publication"
    if isinstance(integration, CostCacheBudgetOptimizationIntegration):
        return "cost_cache_budget"
    return "drift_recovery"


def _missing_lower_integration_replay_refs(
    integration: LowerOptimizationIntegration,
) -> list[str]:
    if isinstance(integration, SchedulerOptimizationIntegration):
        return missing_scheduler_integration_replay_refs(integration)
    if isinstance(integration, NormalizeOptimizationIntegration):
        return missing_normalize_integration_replay_refs(integration)
    if isinstance(integration, ExtractVerifyOptimizationIntegration):
        return missing_extract_verify_integration_replay_refs(integration)
    if isinstance(integration, DedupeIdentityOptimizationIntegration):
        return missing_dedupe_identity_integration_replay_refs(integration)
    if isinstance(integration, RankingPublicationOptimizationIntegration):
        return missing_ranking_publication_integration_replay_refs(integration)
    if isinstance(integration, CostCacheBudgetOptimizationIntegration):
        return missing_cost_cache_budget_integration_replay_refs(integration)
    return missing_drift_recovery_feedback_replay_refs(integration)


def _metric_regression_refs(metric: OptimizationMetricSlice) -> list[Ref]:
    regressions: list[Ref] = []
    if metric.precision < 0.90:
        regressions.append(f"metric-regression:{metric.id}:precision")
    if metric.recall < 0.85:
        regressions.append(f"metric-regression:{metric.id}:recall")
    if metric.extraction_accuracy < 0.95:
        regressions.append(f"metric-regression:{metric.id}:extraction_accuracy")
    if metric.duplicate_rate > 0.05:
        regressions.append(f"metric-regression:{metric.id}:duplicate_rate")
    if metric.crawl_success_rate < 0.95:
        regressions.append(f"metric-regression:{metric.id}:crawl_success_rate")
    if metric.cost_per_success > 0.25:
        regressions.append(f"metric-regression:{metric.id}:cost_per_success")
    if metric.latency_p95_ms > 5000:
        regressions.append(f"metric-regression:{metric.id}:latency_p95_ms")
    if metric.ranking_ndcg < 0.90:
        regressions.append(f"metric-regression:{metric.id}:ranking_ndcg")
    if metric.llm_token_savings_rate < 0.20:
        regressions.append(f"metric-regression:{metric.id}:llm_token_savings_rate")
    return regressions
