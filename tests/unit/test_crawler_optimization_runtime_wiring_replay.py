from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    CrawlerOptimizationReport,
    FrontierScoringProfile,
    OptimizationMetricSlice,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.optimization.runtime import (
    RuntimeFieldSource,
    RuntimeRankingInput,
    RuntimeUrlCandidate,
    runtime_dedupe_ranking_decision,
    runtime_dom_extraction_context,
    runtime_frontier_optimization,
    runtime_optimization_aggregate,
)
from veracrawl.review_replay.crawler_optimization_runtime import (
    dedupe_ranking_decision_replay_passes,
    dom_extraction_context_replay_passes,
    frontier_decision_replay_passes,
    missing_runtime_aggregate_replay_refs,
    runtime_aggregate_replay_passes,
)


def test_runtime_wiring_replay_helpers_pass_for_complete_decisions() -> None:
    frontier = runtime_frontier_optimization(
        fixture_id="runtime-optimization-wiring-success",
        run_ref="run:runtime",
        objective_ref="objective:runtime",
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
        fixture_id="runtime-optimization-wiring-success",
        normalized_document_ref="normalized-document:runtime",
        source_url="https://example.com/listing",
        html_body=_html(),
        fields=[
            RuntimeFieldSource(
                field_name="title",
                raw_value="Runtime Product",
                normalized_value="Runtime Product",
                source_kind="css_selector",
                confidence=0.95,
            )
        ],
    )
    ranking = runtime_dedupe_ranking_decision(
        fixture_id="runtime-optimization-wiring-success",
        objective_ref="objective:runtime",
        inputs=[
            RuntimeRankingInput(
                item_ref="candidate:a",
                canonical_url="https://example.com/item?a=1",
                text="Runtime Product",
            )
        ],
    )
    aggregate = runtime_optimization_aggregate(
        fixture_id="runtime-optimization-wiring-success",
        lower_decision_refs=[
            frontier.decisions[0].id,
            dom.runtime_context.id,
            ranking.runtime_decision.id,
        ],
        metric_slices=[_metric()],
        report=_report(),
        replay_bundle_refs=[
            frontier.decisions[0].replay_bundle_ref or "",
            dom.runtime_context.replay_bundle_ref or "",
            ranking.runtime_decision.replay_bundle_ref or "",
        ],
    )

    assert frontier_decision_replay_passes(frontier.decisions[0])
    assert dom_extraction_context_replay_passes(dom.runtime_context)
    assert dedupe_ranking_decision_replay_passes(ranking.runtime_decision)
    assert runtime_aggregate_replay_passes(aggregate)


def test_runtime_aggregate_replay_detects_missing_replay() -> None:
    aggregate = runtime_optimization_aggregate(
        fixture_id="runtime-optimization-missing-replay",
        lower_decision_refs=["runtime-frontier:1"],
        metric_slices=[_metric()],
        report=_report(),
        replay_bundle_refs=[],
    )

    assert "replay_bundle_refs" in missing_runtime_aggregate_replay_refs(aggregate)
    assert not runtime_aggregate_replay_passes(aggregate)


def _profile() -> FrontierScoringProfile:
    return FrontierScoringProfile(
        id="runtime-frontier-profile:test",
        profile_refs=["optimization"],
        objective_ref="objective:runtime",
        scoring_formula_ref="formula:runtime-frontier",
        required_signal_refs=["signal:url", "signal:anchor", "signal:semantic"],
    )


def _html() -> str:
    return """
    <html><body><article><h2>Runtime Product</h2><span>$42.00</span></article></body></html>
    """


def _metric() -> OptimizationMetricSlice:
    return OptimizationMetricSlice(
        id="runtime-metric:corpus",
        fixture_id="runtime-optimization-wiring-success",
        dimension="corpus",
        slice_ref="corpus",
        precision=0.96,
        recall=0.91,
        extraction_accuracy=0.97,
        duplicate_rate=0.02,
        crawl_success_rate=0.97,
        cost_per_success=0.07,
        latency_p95_ms=2200,
        ranking_ndcg=0.94,
        llm_token_savings_rate=0.42,
        metric_evidence_refs=["metric-evidence:runtime"],
    )


def _report() -> CrawlerOptimizationReport:
    return CrawlerOptimizationReport(
        id="crawler-optimization-report:runtime",
        fixture_id="runtime-optimization-wiring-success",
        run_ref="run:runtime",
        manifest_ref="manifest:runtime",
        profile="optimization",
        frontier_profile_ref="frontier-profile:runtime",
        frontier_score_refs=["frontier-score:runtime"],
        dom_context_refs=["dom-context:runtime"],
        extractor_plan_refs=["extractor-plan:runtime"],
        extractor_attempt_refs=["extractor-attempt:runtime"],
        field_confidence_refs=["field-confidence:runtime"],
        canonicalization_refs=["canonical:runtime"],
        fingerprint_refs=["fingerprint:runtime"],
        identity_decision_refs=["identity:runtime"],
        duplicate_suppression_refs=["dedupe:runtime"],
        ranking_profile_ref="ranking-profile:runtime",
        ranking_score_refs=["ranking-score:runtime"],
        ranked_output_set_refs=["ranked-output:runtime"],
        ranking_evaluation_refs=["ranking-evaluation:runtime"],
        metric_slice_refs=["runtime-metric:corpus"],
        crawl_success_rate=0.97,
        precision=0.96,
        recall=0.91,
        extraction_accuracy=0.97,
        duplicate_rate=0.02,
        cost_per_success=0.07,
        latency_p95_ms=2200,
        ranking_ndcg=0.94,
        llm_token_savings_rate=0.42,
        policy_decision_refs=["policy:runtime"],
        command_record_refs=["command:runtime"],
        event_cursor_refs=["event:runtime"],
        outbox_refs=["outbox:runtime"],
        replay_bundle_refs=["replay:runtime"],
        operator_status="crawler_optimization_completed",
        completion_result=CompletenessResult.PASS,
    )
