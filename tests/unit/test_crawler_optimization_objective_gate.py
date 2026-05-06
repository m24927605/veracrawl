from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    OptimizationMetricSlice,
    OptimizationRegressionReleaseGate,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType
from veracrawl.optimization.objective_gate import (
    build_agent_decision_loop_evidence,
    build_optimization_objective_score,
    build_optimization_objective_score_from_metric,
    compute_optimization_score,
    optimization_objective_release_gate,
)


def test_compute_optimization_score_uses_approved_weighted_formula() -> None:
    score = compute_optimization_score(
        extraction_accuracy=0.98,
        intent_match_precision=0.96,
        crawl_success_rate=0.97,
        dedupe_quality=0.98,
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
    )

    assert score == (
        0.35 * 0.98
        + 0.25 * 0.96
        + 0.15 * 0.97
        + 0.10 * 0.98
        + 0.10 * 0.91
        - 0.03 * 0.25
        - 0.02 * 0.20
    )


def test_objective_score_builder_passes_and_derives_from_metric_slice() -> None:
    score = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )

    assert score.completion_result == CompletenessResult.PASS
    assert score.metric_slice_refs == ["objective-metric:corpus"]
    assert score.dedupe_quality == 0.98


def test_objective_score_builder_fails_low_score_and_missing_refs() -> None:
    low = build_optimization_objective_score(
        fixture_id="optimization-objective-low-score",
        run_ref="run:objective",
        profile_ref="profile:optimization",
        extraction_accuracy=0.20,
        intent_match_precision=0.20,
        crawl_success_rate=0.20,
        dedupe_quality=0.20,
        freshness=0.20,
        normalized_latency=0.90,
        normalized_cost=0.80,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    missing = build_optimization_objective_score(
        fixture_id="optimization-objective-missing-replay",
        run_ref="run:objective",
        profile_ref="profile:optimization",
        extraction_accuracy=0.98,
        intent_match_precision=0.96,
        crawl_success_rate=0.97,
        dedupe_quality=0.98,
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=[],
        command_record_refs=[],
    )

    assert low.completion_result == CompletenessResult.FAIL
    assert low.failure_type == CrawlerOptimizationFailureType.OBJECTIVE_SCORE_GAP
    assert missing.completion_result == CompletenessResult.FAIL
    assert missing.failure_type == CrawlerOptimizationFailureType.MISSING_REPLAY_REFS


def test_agent_decision_loop_evidence_passes_with_bounded_llm_fallback() -> None:
    evidence = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        confidence=0.91,
        llm_fallback_used=True,
    )

    assert evidence.completion_result == CompletenessResult.PASS
    assert evidence.llm_fallback_reason_refs
    assert evidence.model_trace_refs


def test_agent_decision_loop_fails_missing_phase_low_confidence_and_llm_evidence() -> None:
    missing_phase = build_agent_decision_loop_evidence(
        fixture_id="agent-decision-missing-phase",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        observe_ref="",
        confidence=0.91,
    )
    low_confidence = build_agent_decision_loop_evidence(
        fixture_id="agent-decision-low-confidence",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        confidence=0.40,
    )
    llm_evidence = build_agent_decision_loop_evidence(
        fixture_id="agent-decision-llm-output-as-evidence",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        confidence=0.91,
        llm_output_evidence_refs=["model-output:evidence"],
    )

    assert missing_phase.completion_result == CompletenessResult.FAIL
    assert low_confidence.failure_type == (
        CrawlerOptimizationFailureType.AGENT_DECISION_LOOP_GAP
    )
    assert llm_evidence.failure_type == (
        CrawlerOptimizationFailureType.LLM_OUTPUT_AS_EVIDENCE
    )


def test_objective_release_gate_aggregates_lower_scores_and_agent_evidence() -> None:
    score = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    loop = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref=score.id,
        confidence=0.91,
    )
    gate = optimization_objective_release_gate(
        fixture_id="optimization-objective-gate-success",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[_lower_gate()],
        objective_scores=[score],
        agent_decision_loops=[loop],
    )

    assert gate.completion_result == CompletenessResult.PASS
    assert gate.objective_score_refs == [score.id]
    assert gate.agent_decision_loop_refs == [loop.id]


def test_objective_release_gate_fails_missing_or_failed_lower_evidence() -> None:
    score = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    loop = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref=score.id,
        confidence=0.91,
    )
    missing = optimization_objective_release_gate(
        fixture_id="objective-release-missing-lower-gate",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[],
        objective_scores=[score],
        agent_decision_loops=[loop],
    )
    failed = optimization_objective_release_gate(
        fixture_id="objective-release-failed-lower-gate",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[_lower_gate(completion_result=CompletenessResult.FAIL)],
        objective_scores=[score],
        agent_decision_loops=[loop],
    )

    assert missing.completion_result == CompletenessResult.FAIL
    assert missing.failure_type == CrawlerOptimizationFailureType.OBJECTIVE_LOWER_GATE_GAP
    assert failed.completion_result == CompletenessResult.FAIL
    assert failed.failed_lower_gate_refs


def _metric() -> OptimizationMetricSlice:
    return OptimizationMetricSlice(
        id="objective-metric:corpus",
        fixture_id="optimization-objective-gate-success",
        dimension="corpus",
        slice_ref="corpus",
        precision=0.96,
        recall=0.92,
        extraction_accuracy=0.98,
        duplicate_rate=0.02,
        crawl_success_rate=0.97,
        cost_per_success=0.06,
        latency_p95_ms=2100,
        ranking_ndcg=0.95,
        llm_token_savings_rate=0.43,
        metric_evidence_refs=["metric-evidence:objective"],
    )


def _lower_gate(
    completion_result: CompletenessResult = CompletenessResult.PASS,
) -> OptimizationRegressionReleaseGate:
    kinds = [
        "scheduler",
        "normalize",
        "extract_verify",
        "dedupe_identity",
        "ranking_publication",
        "cost_cache_budget",
        "drift_recovery",
    ]
    failed = completion_result != CompletenessResult.PASS
    return OptimizationRegressionReleaseGate(
        id="optimization-regression-release-gate:optimization-objective-gate-success",
        fixture_id="optimization-objective-gate-success",
        required_lower_integration_kinds=kinds,
        present_lower_integration_kinds=kinds,
        lower_integration_refs=[
            "scheduler-optimization-integration:success",
            "normalize-optimization-integration:success",
            "extract-verify-optimization-integration:success",
            "dedupe-identity-optimization-integration:success",
            "ranking-publication-optimization-integration:success",
            "cost-cache-budget-optimization-integration:success",
            "drift-recovery-feedback-integration:success",
        ],
        failed_lower_integration_refs=["scheduler-optimization-integration:failed"]
        if failed
        else [],
        metric_slice_refs=["objective-metric:corpus"],
        diagnostics=["lower gate failed"] if failed else [],
        completion_result=completion_result,
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:lower-gate"],
        event_cursor_refs=["event:lower-gate"],
        outbox_refs=["outbox:lower-gate"],
        replay_bundle_ref="replay:lower-gate",
        failure_type=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
        if failed
        else None,
    )
