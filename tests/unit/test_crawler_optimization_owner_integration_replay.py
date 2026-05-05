from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    FrontierScoringProfile,
    OptimizationMetricSlice,
)
from veracrawl.contracts.enums import CompletenessResult
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
    integrate_cost_cache_budget_optimization,
    integrate_drift_recovery_feedback,
    optimization_regression_release_gate,
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
from veracrawl.review_replay.crawler_optimization_owner_integration import (
    cost_cache_budget_integration_replay_passes,
    dedupe_identity_integration_replay_passes,
    drift_recovery_feedback_replay_passes,
    extract_verify_integration_replay_passes,
    missing_regression_release_gate_replay_refs,
    normalize_integration_replay_passes,
    ranking_publication_integration_replay_passes,
    regression_release_gate_replay_passes,
    scheduler_integration_replay_passes,
)
from veracrawl.scheduler.optimization_integration import (
    integrate_scheduler_optimization,
)


def test_owner_integration_replay_passes_for_complete_refs() -> None:
    frontier = runtime_frontier_optimization(
        fixture_id="owner-optimization-integration-success",
        run_ref="run:owner",
        objective_ref="objective:owner",
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
        fixture_id="owner-optimization-integration-success",
        normalized_document_ref="normalized:owner",
        source_url="https://example.com/listing",
        html_body="<html><body><article><h2>Owner Product</h2></article></body></html>",
        fields=[
            RuntimeFieldSource(
                field_name="title",
                raw_value="Owner Product",
                normalized_value="Owner Product",
                source_kind="css_selector",
                confidence=0.96,
            )
        ],
    )
    ranking = runtime_dedupe_ranking_decision(
        fixture_id="owner-optimization-integration-success",
        objective_ref="objective:owner",
        inputs=[
            RuntimeRankingInput(
                item_ref="candidate:a",
                canonical_url="https://example.com/item?id=1",
                text="Owner Product",
            )
        ],
    )
    scheduler = integrate_scheduler_optimization(
        fixture_id="owner-optimization-integration-success",
        run_ref="run:owner",
        frontier_decisions=frontier.decisions,
    )
    normalize = integrate_normalize_optimization(dom)
    extract = integrate_extract_verify_optimization(dom)
    dedupe = integrate_dedupe_identity_optimization(ranking)
    publication = integrate_ranking_publication_optimization(ranking)
    cost = integrate_cost_cache_budget_optimization(
        fixture_id="owner-optimization-integration-success",
        metric_slices=[_metric()],
        fetch_cost=0.1,
        browser_cost=0.0,
        token_cost=0.2,
    )
    drift = integrate_drift_recovery_feedback(
        fixture_id="owner-optimization-integration-success",
        drift_type="selector_drift",
        affected_ref="selector:title",
        retry_class="repairable",
        repair_outcome="review_required",
    )
    gate = optimization_regression_release_gate(
        fixture_id="owner-optimization-integration-success",
        lower_integration_refs=[
            scheduler.id,
            normalize.id,
            extract.id,
            dedupe.id,
            publication.id,
            cost.id,
            drift.id,
        ],
        metric_slice_refs=[_metric().id],
    )

    assert scheduler_integration_replay_passes(scheduler)
    assert normalize_integration_replay_passes(normalize)
    assert extract_verify_integration_replay_passes(extract)
    assert dedupe_identity_integration_replay_passes(dedupe)
    assert ranking_publication_integration_replay_passes(publication)
    assert cost_cache_budget_integration_replay_passes(cost)
    assert drift_recovery_feedback_replay_passes(drift)
    assert regression_release_gate_replay_passes(gate)


def test_regression_gate_replay_detects_missing_lower_refs() -> None:
    gate = optimization_regression_release_gate(
        fixture_id="owner-optimization-missing-replay",
        lower_integration_refs=["scheduler:ok"],
        metric_slice_refs=[],
        missing_lower_integration_refs=["normalize:missing"],
        false_ready_guard_refs=["false-ready:missing-replay"],
    )

    assert gate.completion_result == CompletenessResult.FAIL
    assert "metric_slice_refs" in missing_regression_release_gate_replay_refs(gate)
    assert "normalize:missing" in missing_regression_release_gate_replay_refs(gate)
    assert not regression_release_gate_replay_passes(gate)


def _profile() -> FrontierScoringProfile:
    return FrontierScoringProfile(
        id="frontier-profile:owner-replay",
        profile_refs=["optimization"],
        objective_ref="objective:owner",
        scoring_formula_ref="formula:owner-frontier",
        required_signal_refs=["signal:url", "signal:anchor", "signal:semantic"],
    )


def _metric() -> OptimizationMetricSlice:
    return OptimizationMetricSlice(
        id="owner-metric:corpus",
        fixture_id="owner-optimization-integration-success",
        dimension="corpus",
        slice_ref="corpus",
        precision=0.97,
        recall=0.92,
        extraction_accuracy=0.98,
        duplicate_rate=0.02,
        crawl_success_rate=0.98,
        cost_per_success=0.06,
        latency_p95_ms=2100,
        ranking_ndcg=0.95,
        llm_token_savings_rate=0.43,
        metric_evidence_refs=["metric-evidence:owner"],
    )
