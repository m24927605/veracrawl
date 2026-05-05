from __future__ import annotations

import pytest

from veracrawl.contracts.crawler_optimization import (
    CostCacheBudgetOptimizationIntegration,
    OptimizationOwnerIntegrationRoadmap,
    OptimizationRegressionReleaseGate,
    SchedulerOptimizationIntegration,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


def test_owner_integration_roadmap_requires_specs_089_096() -> None:
    roadmap = OptimizationOwnerIntegrationRoadmap(
        id="owner-integration-roadmap:088",
        fixture_id="owner-optimization-integration-success",
        spec_refs=[f"spec:{number:03d}" for number in range(89, 97)],
        dependency_refs=["spec:080", "spec:087"],
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:roadmap"],
        event_cursor_refs=["event:roadmap"],
        outbox_refs=["outbox:roadmap"],
        replay_bundle_ref="replay:roadmap",
    )

    assert "spec:096" in roadmap.spec_refs

    with pytest.raises(ValueError, match="089-096"):
        OptimizationOwnerIntegrationRoadmap(
            id="owner-integration-roadmap:bad",
            fixture_id="owner-optimization-missing-lower-ref",
            spec_refs=["spec:089"],
            dependency_refs=["spec:080"],
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:roadmap"],
            event_cursor_refs=["event:roadmap"],
            outbox_refs=["outbox:roadmap"],
            replay_bundle_ref="replay:roadmap",
        )


def test_scheduler_integration_requires_stop_reasons_for_blocked_refs() -> None:
    with pytest.raises(ValueError, match="stop reasons"):
        SchedulerOptimizationIntegration(
            id="scheduler-opt:bad",
            fixture_id="owner-optimization-policy-blocked-url",
            run_ref="run:owner",
            frontier_decision_refs=["frontier:blocked"],
            blocked_refs=["scheduler-block:frontier"],
            policy_decision_refs=["policy:deny"],
            command_record_refs=["command:scheduler"],
            event_cursor_refs=["event:scheduler"],
            outbox_refs=["outbox:scheduler"],
            replay_bundle_ref="replay:scheduler",
        )


def test_cost_cache_budget_pass_cannot_include_stale_cache() -> None:
    with pytest.raises(ValueError, match="stale cache"):
        CostCacheBudgetOptimizationIntegration(
            id="cost-cache:bad",
            fixture_id="owner-optimization-stale-cache",
            fetch_cost=0.1,
            browser_cost=0.0,
            token_cost=0.2,
            stale_cache_refs=["cache:stale"],
            metric_slice_refs=["metric:owner"],
            completion_result=CompletenessResult.PASS,
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:cost"],
            event_cursor_refs=["event:cost"],
            outbox_refs=["outbox:cost"],
            replay_bundle_ref="replay:cost",
        )


def test_regression_gate_failure_requires_typed_diagnostics() -> None:
    gate = OptimizationRegressionReleaseGate(
        id="regression-gate:fail",
        fixture_id="owner-optimization-missing-lower-ref",
        lower_integration_refs=["scheduler:ok"],
        missing_lower_integration_refs=["normalize:missing"],
        metric_slice_refs=["metric:owner"],
        false_ready_guard_refs=["false-ready:missing-lower"],
        diagnostics=["missing normalize lower integration"],
        completion_result=CompletenessResult.FAIL,
        failure_type=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
    )

    assert gate.completion_result == CompletenessResult.FAIL
