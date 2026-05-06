"""Deterministic optimization objective scoring and release gating."""

from __future__ import annotations

from collections.abc import Sequence

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import (
    OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF,
    AgentDecisionLoopEvidence,
    OptimizationMetricSlice,
    OptimizationObjectiveReleaseGate,
    OptimizationObjectiveScore,
    OptimizationRegressionReleaseGate,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrawlerOptimizationFailureType,
)

DEFAULT_OBJECTIVE_SCORE_THRESHOLD = 0.82


def compute_optimization_score(
    *,
    extraction_accuracy: float,
    intent_match_precision: float,
    crawl_success_rate: float,
    dedupe_quality: float,
    freshness: float,
    normalized_latency: float,
    normalized_cost: float,
) -> float:
    """Compute the user-approved weighted optimization objective score."""

    return (
        0.35 * extraction_accuracy
        + 0.25 * intent_match_precision
        + 0.15 * crawl_success_rate
        + 0.10 * dedupe_quality
        + 0.10 * freshness
        - 0.03 * normalized_latency
        - 0.02 * normalized_cost
    )


def build_optimization_objective_score(
    *,
    fixture_id: str,
    run_ref: Ref,
    profile_ref: Ref,
    extraction_accuracy: float,
    intent_match_precision: float,
    crawl_success_rate: float,
    dedupe_quality: float,
    freshness: float,
    normalized_latency: float,
    normalized_cost: float,
    metric_slice_refs: Sequence[Ref] | None = None,
    algorithm_recommendation_refs: Sequence[Ref] | None = None,
    score_threshold: float = DEFAULT_OBJECTIVE_SCORE_THRESHOLD,
    policy_decision_refs: Sequence[Ref] | None = None,
    command_record_refs: Sequence[Ref] | None = None,
    event_cursor_refs: Sequence[Ref] | None = None,
    outbox_refs: Sequence[Ref] | None = None,
    artifact_refs: Sequence[Ref] | None = None,
    replay_bundle_ref: Ref | None = None,
) -> OptimizationObjectiveScore:
    score = compute_optimization_score(
        extraction_accuracy=extraction_accuracy,
        intent_match_precision=intent_match_precision,
        crawl_success_rate=crawl_success_rate,
        dedupe_quality=dedupe_quality,
        freshness=freshness,
        normalized_latency=normalized_latency,
        normalized_cost=normalized_cost,
    )
    metric_refs = _refs_or_default(
        metric_slice_refs, [f"metric-slice:{fixture_id}:objective"]
    )
    algorithm_refs = _refs_or_default(
        algorithm_recommendation_refs,
        [f"algorithm-recommendation:{fixture_id}:objective-score"],
    )
    policy_refs = _refs_or_default(
        policy_decision_refs, [f"policy:optimization-objective:{fixture_id}:allow"]
    )
    command_refs = _refs_or_default(
        command_record_refs, [f"command:optimization-objective:{fixture_id}"]
    )
    event_refs = _refs_or_default(
        event_cursor_refs, [f"event-cursor:optimization-objective:{fixture_id}"]
    )
    outbox_ref_list = _refs_or_default(
        outbox_refs, [f"outbox:optimization-objective:{fixture_id}"]
    )
    artifact_ref_list = _refs_or_default(
        artifact_refs, [f"artifact:optimization-objective:{fixture_id}"]
    )
    replay_ref = (
        replay_bundle_ref
        if replay_bundle_ref is not None
        else f"replay-bundle:optimization-objective:{fixture_id}"
    )
    missing = _missing(
        {
            "metric_slice_refs": metric_refs,
            "algorithm_recommendation_refs": algorithm_refs,
            "policy_decision_refs": policy_refs,
            "command_record_refs": command_refs,
            "event_cursor_refs": event_refs,
            "outbox_refs": outbox_ref_list,
            "artifact_refs": artifact_ref_list,
            "replay_bundle_ref": replay_ref,
        }
    )
    below_threshold = score < score_threshold
    failed = bool(missing or below_threshold)
    diagnostics = _objective_score_diagnostics(
        missing=missing, below_threshold=below_threshold
    )
    failure_type = _objective_score_failure_type(
        missing=missing, below_threshold=below_threshold
    )
    return OptimizationObjectiveScore(
        id=f"optimization-objective-score:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        profile_ref=profile_ref,
        score_formula_ref=OPTIMIZATION_OBJECTIVE_SCORE_FORMULA_REF,
        score_threshold=score_threshold,
        extraction_accuracy=extraction_accuracy,
        intent_match_precision=intent_match_precision,
        crawl_success_rate=crawl_success_rate,
        dedupe_quality=dedupe_quality,
        freshness=freshness,
        normalized_latency=normalized_latency,
        normalized_cost=normalized_cost,
        optimization_score=score,
        metric_slice_refs=metric_refs,
        algorithm_recommendation_refs=algorithm_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_ref_list,
        artifact_refs=artifact_ref_list,
        replay_bundle_ref=replay_ref,
        diagnostics=diagnostics,
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        failure_type=failure_type,
    )


def build_optimization_objective_score_from_metric(
    *,
    metric: OptimizationMetricSlice,
    run_ref: Ref,
    profile_ref: Ref,
    freshness: float,
    normalized_latency: float,
    normalized_cost: float,
    intent_match_precision: float | None = None,
    score_threshold: float = DEFAULT_OBJECTIVE_SCORE_THRESHOLD,
    algorithm_recommendation_refs: Sequence[Ref] | None = None,
) -> OptimizationObjectiveScore:
    return build_optimization_objective_score(
        fixture_id=metric.fixture_id,
        run_ref=run_ref,
        profile_ref=profile_ref,
        extraction_accuracy=metric.extraction_accuracy,
        intent_match_precision=(
            metric.precision if intent_match_precision is None else intent_match_precision
        ),
        crawl_success_rate=metric.crawl_success_rate,
        dedupe_quality=max(0.0, min(1.0, 1.0 - metric.duplicate_rate)),
        freshness=freshness,
        normalized_latency=normalized_latency,
        normalized_cost=normalized_cost,
        metric_slice_refs=[metric.id],
        algorithm_recommendation_refs=algorithm_recommendation_refs,
        score_threshold=score_threshold,
    )


def build_agent_decision_loop_evidence(
    *,
    fixture_id: str,
    run_ref: Ref,
    objective_score_ref: Ref,
    confidence: float,
    confidence_threshold: float = DEFAULT_OBJECTIVE_SCORE_THRESHOLD,
    observe_ref: Ref | None = None,
    think_ref: Ref | None = None,
    act_ref: Ref | None = None,
    verify_ref: Ref | None = None,
    stop_condition_ref: Ref | None = None,
    deterministic_decision_refs: Sequence[Ref] | None = None,
    llm_fallback_used: bool = False,
    llm_fallback_reason_refs: Sequence[Ref] | None = None,
    llm_output_evidence_refs: Sequence[Ref] | None = None,
    model_trace_refs: Sequence[Ref] | None = None,
    tool_trace_refs: Sequence[Ref] | None = None,
    policy_decision_refs: Sequence[Ref] | None = None,
    command_record_refs: Sequence[Ref] | None = None,
    event_cursor_refs: Sequence[Ref] | None = None,
    outbox_refs: Sequence[Ref] | None = None,
    artifact_refs: Sequence[Ref] | None = None,
    replay_bundle_ref: Ref | None = None,
) -> AgentDecisionLoopEvidence:
    resolved_observe_ref = (
        observe_ref if observe_ref is not None else f"agent-loop:{fixture_id}:observe"
    )
    resolved_think_ref = (
        think_ref if think_ref is not None else f"agent-loop:{fixture_id}:think"
    )
    resolved_act_ref = act_ref if act_ref is not None else f"agent-loop:{fixture_id}:act"
    resolved_verify_ref = (
        verify_ref if verify_ref is not None else f"agent-loop:{fixture_id}:verify"
    )
    resolved_stop_condition_ref = (
        stop_condition_ref
        if stop_condition_ref is not None
        else f"agent-loop:{fixture_id}:stop-condition"
    )
    deterministic_refs = _refs_or_default(
        deterministic_decision_refs,
        [f"deterministic-decision:{fixture_id}:frontier-score"],
    )
    fallback_reason_refs = _refs_or_default(
        llm_fallback_reason_refs,
        [f"llm-fallback:{fixture_id}:bounded-reason"] if llm_fallback_used else [],
    )
    llm_evidence_refs = list(llm_output_evidence_refs or [])
    model_refs = _refs_or_default(
        model_trace_refs, [f"model-trace:{fixture_id}:fallback"] if llm_fallback_used else []
    )
    tool_refs = _refs_or_default(
        tool_trace_refs, [f"tool-trace:{fixture_id}:deterministic-gate"]
    )
    policy_refs = _refs_or_default(
        policy_decision_refs, [f"policy:agent-loop:{fixture_id}:allow"]
    )
    command_refs = _refs_or_default(
        command_record_refs, [f"command:agent-loop:{fixture_id}"]
    )
    event_refs = _refs_or_default(
        event_cursor_refs, [f"event-cursor:agent-loop:{fixture_id}"]
    )
    outbox_ref_list = _refs_or_default(outbox_refs, [f"outbox:agent-loop:{fixture_id}"])
    artifact_ref_list = _refs_or_default(
        artifact_refs, [f"artifact:agent-loop:{fixture_id}"]
    )
    replay_ref = (
        replay_bundle_ref
        if replay_bundle_ref is not None
        else f"replay-bundle:agent-loop:{fixture_id}"
    )
    missing = _missing(
        {
            "observe_ref": resolved_observe_ref,
            "think_ref": resolved_think_ref,
            "act_ref": resolved_act_ref,
            "verify_ref": resolved_verify_ref,
            "stop_condition_ref": resolved_stop_condition_ref,
            "deterministic_decision_refs": deterministic_refs,
            "policy_decision_refs": policy_refs,
            "command_record_refs": command_refs,
            "event_cursor_refs": event_refs,
            "outbox_refs": outbox_ref_list,
            "artifact_refs": artifact_ref_list,
            "replay_bundle_ref": replay_ref,
        }
    )
    if llm_fallback_used:
        missing.extend(
            f"llm_fallback:{field}"
            for field in _missing(
                {
                    "llm_fallback_reason_refs": fallback_reason_refs,
                    "model_trace_refs": model_refs,
                }
            )
        )
    failed = bool(missing or confidence < confidence_threshold or llm_evidence_refs)
    failure_type = _agent_loop_failure_type(
        missing=missing,
        confidence=confidence,
        confidence_threshold=confidence_threshold,
        llm_output_evidence_refs=llm_evidence_refs,
    )
    return AgentDecisionLoopEvidence(
        id=f"agent-decision-loop-evidence:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        objective_score_ref=objective_score_ref,
        observe_ref=resolved_observe_ref,
        think_ref=resolved_think_ref,
        act_ref=resolved_act_ref,
        verify_ref=resolved_verify_ref,
        confidence=confidence,
        confidence_threshold=confidence_threshold,
        stop_condition_ref=resolved_stop_condition_ref,
        deterministic_decision_refs=deterministic_refs,
        llm_fallback_used=llm_fallback_used,
        llm_fallback_reason_refs=fallback_reason_refs,
        llm_output_evidence_refs=llm_evidence_refs,
        model_trace_refs=model_refs,
        tool_trace_refs=tool_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_ref_list,
        artifact_refs=artifact_ref_list,
        replay_bundle_ref=replay_ref,
        diagnostics=_agent_loop_diagnostics(
            missing=missing,
            low_confidence=confidence < confidence_threshold,
            llm_output_evidence_refs=llm_evidence_refs,
        ),
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        failure_type=failure_type,
    )


def optimization_objective_release_gate(
    *,
    fixture_id: str,
    claim_scope_ref: Ref,
    lower_regression_gates: Sequence[OptimizationRegressionReleaseGate],
    objective_scores: Sequence[OptimizationObjectiveScore],
    agent_decision_loops: Sequence[AgentDecisionLoopEvidence],
    metric_slice_refs: Sequence[Ref] | None = None,
    algorithm_recommendation_refs: Sequence[Ref] | None = None,
    required_lower_gate_refs: Sequence[Ref] | None = None,
    policy_decision_refs: Sequence[Ref] | None = None,
    command_record_refs: Sequence[Ref] | None = None,
    event_cursor_refs: Sequence[Ref] | None = None,
    outbox_refs: Sequence[Ref] | None = None,
    artifact_refs: Sequence[Ref] | None = None,
    replay_bundle_ref: Ref | None = None,
) -> OptimizationObjectiveReleaseGate:
    present_lower = [gate.id for gate in lower_regression_gates]
    required_lower = list(required_lower_gate_refs or present_lower)
    if not required_lower:
        required_lower = [f"optimization-regression-release-gate:{fixture_id}"]

    failed_lower = [
        gate.id
        for gate in lower_regression_gates
        if gate.completion_result != CompletenessResult.PASS
    ]
    failed_scores = [
        score.id
        for score in objective_scores
        if score.completion_result != CompletenessResult.PASS
    ]
    if not objective_scores:
        failed_scores.append(f"optimization-objective-score:{fixture_id}:missing")
    failed_loops = [
        loop.id
        for loop in agent_decision_loops
        if loop.completion_result != CompletenessResult.PASS
    ]
    if not agent_decision_loops:
        failed_loops.append(f"agent-decision-loop-evidence:{fixture_id}:missing")
    metric_refs = _refs_or_default(
        metric_slice_refs,
        [ref for score in objective_scores for ref in score.metric_slice_refs],
    )
    algorithm_refs = _refs_or_default(
        algorithm_recommendation_refs,
        [
            ref
            for score in objective_scores
            for ref in score.algorithm_recommendation_refs
        ],
    )
    policy_refs = _refs_or_default(
        policy_decision_refs, [f"policy:optimization-release:{fixture_id}:allow"]
    )
    command_refs = _refs_or_default(
        command_record_refs, [f"command:optimization-release:{fixture_id}"]
    )
    event_refs = _refs_or_default(
        event_cursor_refs, [f"event-cursor:optimization-release:{fixture_id}"]
    )
    outbox_ref_list = _refs_or_default(
        outbox_refs, [f"outbox:optimization-release:{fixture_id}"]
    )
    artifact_ref_list = _refs_or_default(
        artifact_refs, [f"artifact:optimization-release:{fixture_id}"]
    )
    replay_ref = (
        replay_bundle_ref
        if replay_bundle_ref is not None
        else f"replay-bundle:optimization-release:{fixture_id}"
    )
    missing_lower = sorted(set(required_lower) - set(present_lower))
    missing_refs = _missing(
        {
            "metric_slice_refs": metric_refs,
            "algorithm_recommendation_refs": algorithm_refs,
            "policy_decision_refs": policy_refs,
            "command_record_refs": command_refs,
            "event_cursor_refs": event_refs,
            "outbox_refs": outbox_ref_list,
            "artifact_refs": artifact_ref_list,
            "replay_bundle_ref": replay_ref,
        }
    )
    failed = bool(
        missing_lower
        or failed_lower
        or failed_scores
        or failed_loops
        or not objective_scores
        or not agent_decision_loops
        or missing_refs
    )
    return OptimizationObjectiveReleaseGate(
        id=f"optimization-objective-release-gate:{fixture_id}",
        fixture_id=fixture_id,
        claim_scope_ref=claim_scope_ref,
        required_lower_gate_refs=required_lower,
        present_lower_gate_refs=present_lower,
        failed_lower_gate_refs=failed_lower,
        objective_score_refs=[score.id for score in objective_scores],
        failed_objective_score_refs=failed_scores,
        agent_decision_loop_refs=[loop.id for loop in agent_decision_loops],
        failed_agent_decision_loop_refs=failed_loops,
        metric_slice_refs=metric_refs,
        algorithm_recommendation_refs=algorithm_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_ref_list,
        artifact_refs=artifact_ref_list,
        replay_bundle_ref=replay_ref,
        diagnostics=_release_gate_diagnostics(
            missing_lower=missing_lower,
            failed_lower=failed_lower,
            failed_scores=failed_scores,
            failed_loops=failed_loops,
            missing_refs=missing_refs,
            missing_scores=not objective_scores,
            missing_loops=not agent_decision_loops,
        ),
        completion_result=CompletenessResult.FAIL if failed else CompletenessResult.PASS,
        failure_type=_release_gate_failure_type(
            missing_lower=missing_lower,
            failed_lower=failed_lower,
            failed_scores=failed_scores,
            failed_loops=failed_loops,
            missing_refs=missing_refs,
            missing_scores=not objective_scores,
            missing_loops=not agent_decision_loops,
        ),
    )


def _refs_or_default(refs: Sequence[Ref] | None, default: Sequence[Ref]) -> list[Ref]:
    return list(default) if refs is None else list(refs)


def _missing(refs: dict[str, object]) -> list[str]:
    return sorted(name for name, value in refs.items() if not value)


def _objective_score_diagnostics(*, missing: list[str], below_threshold: bool) -> list[str]:
    diagnostics: list[str] = []
    if missing:
        diagnostics.append(f"missing objective refs: {', '.join(missing)}")
    if below_threshold:
        diagnostics.append("objective score below threshold")
    return diagnostics


def _objective_score_failure_type(
    *, missing: list[str], below_threshold: bool
) -> CrawlerOptimizationFailureType | None:
    if missing:
        return CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
    if below_threshold:
        return CrawlerOptimizationFailureType.OBJECTIVE_SCORE_GAP
    return None


def _agent_loop_diagnostics(
    *,
    missing: list[str],
    low_confidence: bool,
    llm_output_evidence_refs: list[Ref],
) -> list[str]:
    diagnostics: list[str] = []
    if missing:
        diagnostics.append(f"missing agent loop refs: {', '.join(missing)}")
    if low_confidence:
        diagnostics.append("agent confidence below threshold")
    if llm_output_evidence_refs:
        diagnostics.append("LLM output was supplied as evidence")
    return diagnostics


def _agent_loop_failure_type(
    *,
    missing: list[str],
    confidence: float,
    confidence_threshold: float,
    llm_output_evidence_refs: list[Ref],
) -> CrawlerOptimizationFailureType | None:
    if llm_output_evidence_refs:
        return CrawlerOptimizationFailureType.LLM_OUTPUT_AS_EVIDENCE
    if missing:
        return CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
    if confidence < confidence_threshold:
        return CrawlerOptimizationFailureType.AGENT_DECISION_LOOP_GAP
    return None


def _release_gate_diagnostics(
    *,
    missing_lower: list[Ref],
    failed_lower: list[Ref],
    failed_scores: list[Ref],
    failed_loops: list[Ref],
    missing_refs: list[str],
    missing_scores: bool,
    missing_loops: bool,
) -> list[str]:
    diagnostics: list[str] = []
    if missing_lower:
        diagnostics.append(f"missing lower gate refs: {', '.join(missing_lower)}")
    if failed_lower:
        diagnostics.append(f"failed lower gate refs: {', '.join(failed_lower)}")
    if failed_scores:
        diagnostics.append(f"failed objective score refs: {', '.join(failed_scores)}")
    if failed_loops:
        diagnostics.append(f"failed agent loop refs: {', '.join(failed_loops)}")
    if missing_refs:
        diagnostics.append(f"missing release refs: {', '.join(missing_refs)}")
    if missing_scores:
        diagnostics.append("missing objective score reports")
    if missing_loops:
        diagnostics.append("missing agent decision loop evidence")
    return diagnostics


def _release_gate_failure_type(
    *,
    missing_lower: list[Ref],
    failed_lower: list[Ref],
    failed_scores: list[Ref],
    failed_loops: list[Ref],
    missing_refs: list[str],
    missing_scores: bool,
    missing_loops: bool,
) -> CrawlerOptimizationFailureType | None:
    if missing_refs:
        return CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
    if missing_lower or failed_lower:
        return CrawlerOptimizationFailureType.OBJECTIVE_LOWER_GATE_GAP
    if failed_scores or missing_scores:
        return CrawlerOptimizationFailureType.OBJECTIVE_SCORE_GAP
    if failed_loops or missing_loops:
        return CrawlerOptimizationFailureType.AGENT_DECISION_LOOP_GAP
    return None
