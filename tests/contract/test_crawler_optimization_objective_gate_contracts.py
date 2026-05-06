from __future__ import annotations

import pytest

from veracrawl.contracts.crawler_optimization import (
    OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF,
    AgentDecisionLoopEvidence,
    OptimizationObjectiveReleaseGate,
    OptimizationObjectiveScore,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


def test_objective_score_requires_exact_formula_and_refs() -> None:
    score = OptimizationObjectiveScore(
        id="optimization-objective-score:success",
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        profile_ref="profile:optimization",
        score_formula_ref=OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF,
        extraction_accuracy=0.98,
        intent_match_precision=0.96,
        crawl_success_rate=0.97,
        dedupe_quality=0.98,
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        optimization_score=0.35 * 0.98
        + 0.25 * 0.96
        + 0.15 * 0.97
        + 0.10 * 0.98
        + 0.10 * 0.91
        - 0.03 * 0.25
        - 0.02 * 0.20,
        metric_slice_refs=["metric:objective"],
        algorithm_recommendation_refs=["algorithm:objective"],
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:objective"],
        event_cursor_refs=["event:objective"],
        outbox_refs=["outbox:objective"],
        artifact_refs=["artifact:objective"],
        replay_bundle_ref="replay:objective",
        completion_result=CompletenessResult.PASS,
    )

    assert score.completion_result == CompletenessResult.PASS

    with pytest.raises(ValueError, match="formula mismatch"):
        OptimizationObjectiveScore(
            **{
                **score.model_dump(exclude={"created_at"}),
                "id": "optimization-objective-score:mismatch",
                "optimization_score": 0.1,
            }
        )


def test_objective_score_pass_rejects_missing_algorithm_refs() -> None:
    with pytest.raises(ValueError, match="missing refs"):
        OptimizationObjectiveScore(
            id="optimization-objective-score:missing-algorithm",
            fixture_id="optimization-objective-missing-algorithms",
            run_ref="run:objective",
            profile_ref="profile:optimization",
            extraction_accuracy=0.98,
            intent_match_precision=0.96,
            crawl_success_rate=0.97,
            dedupe_quality=0.98,
            freshness=0.91,
            normalized_latency=0.25,
            normalized_cost=0.20,
            optimization_score=0.906,
            metric_slice_refs=["metric:objective"],
            algorithm_recommendation_refs=[],
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:objective"],
            event_cursor_refs=["event:objective"],
            outbox_refs=["outbox:objective"],
            artifact_refs=["artifact:objective"],
            replay_bundle_ref="replay:objective",
            completion_result=CompletenessResult.PASS,
        )


def test_agent_decision_loop_rejects_llm_output_as_evidence() -> None:
    with pytest.raises(ValueError, match="LLM output"):
        AgentDecisionLoopEvidence(
            id="agent-decision-loop-evidence:llm-evidence",
            fixture_id="agent-decision-llm-output-as-evidence",
            run_ref="run:objective",
            objective_score_ref="optimization-objective-score:success",
            observe_ref="agent:observe",
            think_ref="agent:think",
            act_ref="agent:act",
            verify_ref="agent:verify",
            confidence=0.91,
            stop_condition_ref="agent:stop",
            deterministic_decision_refs=["frontier:score"],
            llm_output_evidence_refs=["model-output:evidence"],
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:agent"],
            event_cursor_refs=["event:agent"],
            outbox_refs=["outbox:agent"],
            artifact_refs=["artifact:agent"],
            replay_bundle_ref="replay:agent",
            completion_result=CompletenessResult.PASS,
        )


def test_agent_decision_loop_allows_bounded_llm_fallback() -> None:
    evidence = AgentDecisionLoopEvidence(
        id="agent-decision-loop-evidence:bounded",
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        observe_ref="agent:observe",
        think_ref="agent:think",
        act_ref="agent:act",
        verify_ref="agent:verify",
        confidence=0.91,
        stop_condition_ref="agent:stop",
        deterministic_decision_refs=["frontier:score"],
        llm_fallback_used=True,
        llm_fallback_reason_refs=["fallback:semantic-label"],
        model_trace_refs=["model-trace:fallback"],
        tool_trace_refs=["tool-trace:verify"],
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:agent"],
        event_cursor_refs=["event:agent"],
        outbox_refs=["outbox:agent"],
        artifact_refs=["artifact:agent"],
        replay_bundle_ref="replay:agent",
        completion_result=CompletenessResult.PASS,
    )

    assert evidence.llm_fallback_used is True


def test_objective_release_gate_pass_requires_096_lower_gate_refs() -> None:
    with pytest.raises(ValueError, match="non-096 lower refs"):
        OptimizationObjectiveReleaseGate(
            id="optimization-objective-release-gate:false-ready",
            fixture_id="objective-release-missing-lower-gate",
            claim_scope_ref="claim:fixture",
            required_lower_gate_refs=["optimization-regression-release-gate:success"],
            present_lower_gate_refs=["lower-gate:success"],
            objective_score_refs=["optimization-objective-score:success"],
            agent_decision_loop_refs=["agent-decision-loop-evidence:success"],
            metric_slice_refs=["metric:objective"],
            algorithm_recommendation_refs=["algorithm:objective"],
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:release"],
            event_cursor_refs=["event:release"],
            outbox_refs=["outbox:release"],
            artifact_refs=["artifact:release"],
            replay_bundle_ref="replay:release",
            completion_result=CompletenessResult.PASS,
        )


def test_objective_release_gate_failure_requires_typed_diagnostics() -> None:
    gate = OptimizationObjectiveReleaseGate(
        id="optimization-objective-release-gate:fail",
        fixture_id="objective-release-failed-lower-gate",
        claim_scope_ref="claim:fixture",
        required_lower_gate_refs=["optimization-regression-release-gate:success"],
        present_lower_gate_refs=[],
        failed_lower_gate_refs=["optimization-regression-release-gate:failed"],
        diagnostics=["lower gate failed"],
        completion_result=CompletenessResult.FAIL,
        failure_type=CrawlerOptimizationFailureType.OBJECTIVE_LOWER_GATE_GAP,
    )

    assert gate.failure_type == CrawlerOptimizationFailureType.OBJECTIVE_LOWER_GATE_GAP
