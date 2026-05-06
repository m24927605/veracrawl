"""Deterministic evidence runner for optimization objective release gates."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawler_optimization import (
    AgentDecisionLoopEvidence,
    FrontierScoringProfile,
    OptimizationMetricSlice,
    OptimizationObjectiveReleaseGate,
    OptimizationObjectiveScore,
    OptimizationRegressionReleaseGate,
)
from veracrawl.extract.optimization_integration import (
    integrate_extract_verify_optimization,
)
from veracrawl.graph.optimization_integration import (
    integrate_dedupe_identity_optimization,
)
from veracrawl.normalize.optimization_integration import (
    integrate_normalize_optimization,
)
from veracrawl.ops.optimization_integration import (
    LowerOptimizationIntegration,
    integrate_cost_cache_budget_optimization,
    integrate_drift_recovery_feedback,
    optimization_regression_release_gate_from_reports,
)
from veracrawl.optimization.objective_gate import (
    build_agent_decision_loop_evidence,
    build_optimization_objective_score_from_metric,
    optimization_objective_release_gate,
)
from veracrawl.optimization.runtime import (
    RuntimeFieldSource,
    RuntimeRankingInput,
    RuntimeUrlCandidate,
    runtime_dedupe_ranking_decision,
    runtime_dom_extraction_context,
    runtime_frontier_optimization,
)
from veracrawl.publish.optimization_integration import (
    integrate_ranking_publication_optimization,
)
from veracrawl.scheduler.optimization_integration import (
    integrate_scheduler_optimization,
)

DEFAULT_OBJECTIVE_FIXTURE_ID = "optimization-objective-gate-success"


@dataclass(frozen=True)
class OptimizationObjectiveEvidenceRun:
    fixture_id: str
    metric: OptimizationMetricSlice
    lower_integrations: list[LowerOptimizationIntegration]
    regression_gate: OptimizationRegressionReleaseGate
    objective_score: OptimizationObjectiveScore
    agent_decision_loop: AgentDecisionLoopEvidence
    objective_release_gate: OptimizationObjectiveReleaseGate


def run_deterministic_objective_evidence(
    *,
    fixture_id: str = DEFAULT_OBJECTIVE_FIXTURE_ID,
    run_ref: Ref | None = None,
    profile_ref: Ref = "profile:optimization",
    claim_scope_ref: Ref | None = None,
) -> OptimizationObjectiveEvidenceRun:
    run_ref = run_ref or f"run:{fixture_id}"
    metric = _metric(fixture_id)
    lower_integrations = _lower_integrations(fixture_id=fixture_id, run_ref=run_ref)
    regression_gate = optimization_regression_release_gate_from_reports(
        fixture_id=fixture_id,
        lower_integrations=lower_integrations,
        metric_slices=[metric],
    )
    objective_score = build_optimization_objective_score_from_metric(
        metric=metric,
        run_ref=run_ref,
        profile_ref=profile_ref,
        freshness=0.91,
        normalized_latency=_normalize_latency(metric.latency_p95_ms),
        normalized_cost=_normalize_cost(metric.cost_per_success),
        algorithm_recommendation_refs=[
            "algorithm:focused-priority-queue",
            "algorithm:dom-pruning-element-ranking",
            "algorithm:extractor-fallback-confidence",
            "algorithm:canonical-dedupe-identity",
            "algorithm:heuristic-ranking",
            "algorithm:cost-recovery-gates",
        ],
    )
    agent_loop = build_agent_decision_loop_evidence(
        fixture_id=fixture_id,
        run_ref=run_ref,
        objective_score_ref=objective_score.id,
        confidence=0.91,
        deterministic_decision_refs=[
            "runtime-frontier-optimization-decision:objective",
            "runtime-dom-extraction-context:objective",
            "runtime-dedupe-ranking-decision:objective",
            regression_gate.id,
            objective_score.id,
        ],
        llm_fallback_used=True,
        llm_fallback_reason_refs=["llm-fallback:bounded-semantic-page-type"],
        model_trace_refs=["model-trace:bounded-semantic-page-type"],
        tool_trace_refs=[
            "tool-trace:frontier-score",
            "tool-trace:objective-score",
            "tool-trace:release-gate",
        ],
    )
    release_gate = optimization_objective_release_gate(
        fixture_id=fixture_id,
        claim_scope_ref=claim_scope_ref or f"claim:optimization-objective:{fixture_id}",
        lower_regression_gates=[regression_gate],
        objective_scores=[objective_score],
        agent_decision_loops=[agent_loop],
    )
    return OptimizationObjectiveEvidenceRun(
        fixture_id=fixture_id,
        metric=metric,
        lower_integrations=lower_integrations,
        regression_gate=regression_gate,
        objective_score=objective_score,
        agent_decision_loop=agent_loop,
        objective_release_gate=release_gate,
    )


def objective_evidence_summary(run: OptimizationObjectiveEvidenceRun) -> dict[str, object]:
    release_gate = run.objective_release_gate
    score = run.objective_score
    return {
        "ok": release_gate.completion_result.value == "pass",
        "fixture_id": run.fixture_id,
        "optimization_score": score.optimization_score,
        "score_threshold": score.score_threshold,
        "completion_result": release_gate.completion_result.value,
        "objective_score_result": score.completion_result.value,
        "agent_decision_loop_result": run.agent_decision_loop.completion_result.value,
        "regression_gate_result": run.regression_gate.completion_result.value,
        "lower_integration_count": len(run.lower_integrations),
        "lower_regression_gate_ref": run.regression_gate.id,
        "objective_score_ref": score.id,
        "agent_decision_loop_ref": run.agent_decision_loop.id,
        "objective_release_gate_ref": release_gate.id,
        "extraction_accuracy": score.extraction_accuracy,
        "intent_match_precision": score.intent_match_precision,
        "crawl_success_rate": score.crawl_success_rate,
        "dedupe_quality": score.dedupe_quality,
        "freshness": score.freshness,
        "normalized_latency": score.normalized_latency,
        "normalized_cost": score.normalized_cost,
    }


def _lower_integrations(
    *,
    fixture_id: str,
    run_ref: Ref,
) -> list[LowerOptimizationIntegration]:
    frontier = runtime_frontier_optimization(
        fixture_id=fixture_id,
        run_ref=run_ref,
        objective_ref="objective:crawler-optimization:general-purpose",
        profile=_profile(),
        candidates=[
            RuntimeUrlCandidate(
                candidate_url="https://example.com/listing",
                source_anchor_ref="anchor:listing",
                page_type="listing",
                url_pattern_score=0.9,
                anchor_text_score=0.9,
                page_title_score=0.9,
                semantic_similarity_score=0.9,
                domain_authority_score=0.8,
                freshness_score=0.8,
                historical_success_score=0.9,
                page_type_score=0.9,
            )
        ],
    )
    dom = runtime_dom_extraction_context(
        fixture_id=fixture_id,
        normalized_document_ref="normalized:optimization-objective",
        source_url="https://example.com/listing",
        html_body=_html(),
        fields=[
            RuntimeFieldSource(
                field_name="title",
                raw_value="Objective Product",
                normalized_value="Objective Product",
                source_kind="css_selector",
                confidence=0.96,
            ),
            RuntimeFieldSource(
                field_name="price",
                raw_value="$42.00",
                normalized_value="42.00 USD",
                source_kind="json_ld",
                confidence=0.97,
            ),
        ],
    )
    ranking = runtime_dedupe_ranking_decision(
        fixture_id=fixture_id,
        objective_ref="objective:crawler-optimization:general-purpose",
        inputs=[
            RuntimeRankingInput(
                item_ref="candidate:objective-red",
                canonical_url="https://example.com/item?id=1&utm_source=ad",
                text="Objective Product red available",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:objective-red-duplicate",
                canonical_url="https://example.com/item?utm_source=ad&id=1",
                text="Objective Product red duplicate",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:objective-blue",
                canonical_url="https://example.com/item?id=1&color=blue",
                text="Objective Product blue available",
                variant_key="product:blue",
            ),
        ],
    )
    cost = integrate_cost_cache_budget_optimization(
        fixture_id=fixture_id,
        metric_slices=[_metric(fixture_id)],
        fetch_cost=0.2,
        browser_cost=0.0,
        token_cost=0.3,
        cache_hit_refs=["cache:objective:fresh"],
    )
    drift = integrate_drift_recovery_feedback(
        fixture_id=fixture_id,
        drift_type="selector_drift",
        affected_ref="selector:price",
        retry_class="repairable",
        repair_outcome="review_required",
        memory_advisory_refs=["memory:objective:advisory"],
    )
    return [
        integrate_scheduler_optimization(
            fixture_id=fixture_id,
            run_ref=run_ref,
            frontier_decisions=frontier.decisions,
        ),
        integrate_normalize_optimization(dom),
        integrate_extract_verify_optimization(dom),
        integrate_dedupe_identity_optimization(ranking),
        integrate_ranking_publication_optimization(ranking),
        cost,
        drift,
    ]


def _profile() -> FrontierScoringProfile:
    return FrontierScoringProfile(
        id="frontier-profile:optimization-objective",
        profile_refs=["optimization"],
        objective_ref="objective:crawler-optimization:general-purpose",
        scoring_formula_ref="formula:focused-priority-frontier:v1",
        required_signal_refs=["signal:url", "signal:anchor", "signal:semantic"],
    )


def _metric(fixture_id: str) -> OptimizationMetricSlice:
    return OptimizationMetricSlice(
        id=f"optimization-metric:{fixture_id}:corpus",
        fixture_id=fixture_id,
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
        metric_evidence_refs=[f"metric-evidence:{fixture_id}:objective"],
    )


def _normalize_latency(latency_p95_ms: int, *, slo_ms: int = 5000) -> float:
    return max(0.0, min(1.0, latency_p95_ms / slo_ms))


def _normalize_cost(cost_per_success: float, *, budget_per_success: float = 0.25) -> float:
    return max(0.0, min(1.0, cost_per_success / budget_per_success))


def _html() -> str:
    return """
    <html>
      <body>
        <article class="product-card">
          <script type="application/ld+json">
            {"@type":"Product","name":"Objective Product","offers":{"price":"42.00"}}
          </script>
          <h2>Objective Product</h2>
          <span class="price">$42.00</span>
          <button>Sort by rating</button>
          <a href="/next">Next page</a>
        </article>
      </body>
    </html>
    """
