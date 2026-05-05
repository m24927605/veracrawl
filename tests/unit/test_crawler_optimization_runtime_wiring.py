from __future__ import annotations

import pytest

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
    canonicalize_url,
    runtime_dedupe_ranking_decision,
    runtime_dom_extraction_context,
    runtime_frontier_optimization,
    runtime_optimization_aggregate,
)


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
    <html>
      <body>
        <article class="product-card">
          <h2>Runtime Product</h2>
          <span class="price">$42.00</span>
          <button>Sort by rating</button>
          <a href="/next">Next page</a>
        </article>
      </body>
    </html>
    """


def test_runtime_frontier_optimization_orders_allowed_urls_and_blocks_denied() -> None:
    result = runtime_frontier_optimization(
        fixture_id="runtime-optimization-wiring-success",
        run_ref="run:runtime",
        objective_ref="objective:runtime",
        profile=_profile(),
        candidates=[
            RuntimeUrlCandidate(
                candidate_url="https://example.com/listing?utm_source=ad",
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
            ),
            RuntimeUrlCandidate(
                candidate_url="https://example.com/private",
                source_anchor_ref="anchor:private",
                page_type="detail",
                url_pattern_score=0.9,
                anchor_text_score=0.9,
                page_title_score=0.9,
                semantic_similarity_score=0.9,
                domain_authority_score=0.8,
                freshness_score=0.8,
                historical_success_score=0.9,
                page_type_score=0.9,
                allowed=False,
                blocked_reason_refs=("robots:denied",),
            ),
        ],
    )

    assert len(result.score_breakdowns) == 1
    assert result.decisions[0].scheduler_action == "enqueue"
    assert result.decisions[0].scheduler_priority > 0
    assert result.decisions[-1].scheduler_action == "block"
    assert result.decisions[-1].blocked_reason_refs == ["robots:denied"]


def test_runtime_dom_extraction_context_materializes_refs() -> None:
    result = runtime_dom_extraction_context(
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
            ),
            RuntimeFieldSource(
                field_name="price",
                raw_value="$42.00",
                normalized_value="42.00 USD",
                source_kind="regex",
                confidence=0.91,
            ),
        ],
    )

    assert result.dom_context.retained_node_count < result.dom_context.original_node_count
    assert result.page_zones
    assert result.extractor_attempts[0].accepted
    assert result.runtime_context.dom_context_ref == result.dom_context.id
    assert result.runtime_context.field_confidence_refs


def test_runtime_dom_extraction_rejects_llm_output_as_source_evidence() -> None:
    with pytest.raises(ValueError, match="LLM output cannot be accepted field evidence"):
        runtime_dom_extraction_context(
            fixture_id="runtime-optimization-llm-as-evidence",
            normalized_document_ref="normalized-document:runtime",
            source_url="https://example.com/listing",
            html_body=_html(),
            fields=[
                RuntimeFieldSource(
                    field_name="price",
                    raw_value="$42.00",
                    normalized_value="42.00 USD",
                    source_kind="llm_structured",
                    confidence=0.91,
                    llm_output_evidence_refs=("model-output:price",),
                )
            ],
        )


def test_runtime_dedupe_ranking_preserves_variants_and_suppresses_duplicates() -> None:
    result = runtime_dedupe_ranking_decision(
        fixture_id="runtime-optimization-wiring-success",
        objective_ref="objective:runtime",
        inputs=[
            RuntimeRankingInput(
                item_ref="candidate:a",
                canonical_url="https://example.com/item?a=1&utm_source=ad",
                text="Runtime Product red",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:b",
                canonical_url="https://example.com/item?utm_source=ad&a=1",
                text="Runtime Product red duplicate",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:c",
                canonical_url="https://example.com/item?a=1&color=blue",
                text="Runtime Product blue",
                variant_key="product:blue",
            ),
        ],
    )

    assert result.duplicate_suppression.suppressed_refs == ["candidate:b"]
    assert set(result.duplicate_suppression.retained_refs) == {"candidate:a", "candidate:c"}
    assert result.runtime_decision.ranked_output_set_ref == result.ranked_output_set.id
    assert len(result.ranking_scores) == 2


def test_runtime_canonicalize_url_strips_tracking_but_keeps_semantic_query() -> None:
    decision = canonicalize_url(
        "https://Example.com/search?utm_source=ad&q=crawler&sid=abc",
        "runtime-optimization-wiring-success",
    )

    assert decision.canonical_url == "https://example.com/search?q=crawler"
    assert decision.removed_query_params == ["sid", "utm_source"]


def test_runtime_optimization_aggregate_passes_with_lower_refs() -> None:
    report = _report()
    metric = _metric()
    aggregate = runtime_optimization_aggregate(
        fixture_id="runtime-optimization-wiring-success",
        lower_decision_refs=["runtime-frontier:1", "runtime-dom:1", "runtime-ranking:1"],
        metric_slices=[metric],
        report=report,
        replay_bundle_refs=["replay:frontier", "replay:dom", "replay:ranking"],
    )

    assert aggregate.completion_result == CompletenessResult.PASS
    assert aggregate.optimization_report_ref == report.id


def test_runtime_optimization_aggregate_fails_on_missing_replay() -> None:
    aggregate = runtime_optimization_aggregate(
        fixture_id="runtime-optimization-missing-replay",
        lower_decision_refs=["runtime-frontier:1"],
        metric_slices=[_metric()],
        report=_report(),
        replay_bundle_refs=[],
    )

    assert aggregate.completion_result == CompletenessResult.FAIL
    assert "replay_bundle_refs" in aggregate.missing_ref_fields


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
