from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    CrawlerOptimizationReport,
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
from veracrawl.scheduler.optimization_integration import (
    integrate_scheduler_optimization,
)


def test_scheduler_integration_records_enqueue_block_and_stop_refs() -> None:
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

    integration = integrate_scheduler_optimization(
        fixture_id="owner-optimization-integration-success",
        run_ref="run:owner",
        frontier_decisions=frontier.decisions,
    )

    assert integration.enqueue_refs
    assert integration.blocked_refs
    assert "robots:denied" in integration.stop_reason_refs
    assert integration.scheduler_priority_refs


def test_normalize_and_extract_verify_integration_keep_anchors_and_reject_llm_only() -> None:
    dom = runtime_dom_extraction_context(
        fixture_id="owner-optimization-llm-as-evidence",
        normalized_document_ref="normalized:owner",
        source_url="https://example.com/listing",
        html_body=_html(),
        fields=[
            RuntimeFieldSource(
                field_name="title",
                raw_value="Owner Product",
                normalized_value="Owner Product",
                source_kind="css_selector",
                confidence=0.96,
            ),
            RuntimeFieldSource(
                field_name="price",
                raw_value="$42.00",
                normalized_value="42.00 USD",
                source_kind="llm_structured",
                confidence=0.80,
                accepted=False,
                llm_output_evidence_refs=("model-output:price",),
            ),
        ],
    )

    normalize = integrate_normalize_optimization(dom)
    extract = integrate_extract_verify_optimization(dom)

    assert normalize.retained_node_refs
    assert normalize.context_reduction_ratio > 0
    assert extract.accepted_attempt_refs
    assert extract.rejected_attempt_refs
    assert extract.llm_only_rejected_refs == ["model-output:price"]
    assert extract.review_refs


def test_dedupe_and_ranking_integration_preserve_retained_verified_outputs() -> None:
    ranking = runtime_dedupe_ranking_decision(
        fixture_id="owner-optimization-integration-success",
        objective_ref="objective:owner",
        inputs=[
            RuntimeRankingInput(
                item_ref="candidate:a",
                canonical_url="https://example.com/item?id=1&utm_source=ad",
                text="Owner Product red",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:b",
                canonical_url="https://example.com/item?utm_source=ad&id=1",
                text="Owner Product red duplicate",
                variant_key="product:red",
            ),
            RuntimeRankingInput(
                item_ref="candidate:c",
                canonical_url="https://example.com/item?id=1&color=blue",
                text="Owner Product blue",
                variant_key="product:blue",
            ),
        ],
    )

    dedupe = integrate_dedupe_identity_optimization(ranking)
    publication = integrate_ranking_publication_optimization(ranking)

    assert dedupe.suppressed_refs == ["candidate:b"]
    assert set(dedupe.retained_refs) == {"candidate:a", "candidate:c"}
    assert publication.ranking_score_refs
    assert publication.retained_output_refs == ranking.ranked_output_set.sorted_item_refs
    assert all(ref.endswith(":accepted") for ref in publication.verification_status_refs)


def test_ops_cost_cache_drift_and_regression_gates() -> None:
    metric = _metric()
    cost_pass = integrate_cost_cache_budget_optimization(
        fixture_id="owner-optimization-integration-success",
        metric_slices=[metric],
        fetch_cost=0.2,
        browser_cost=0.0,
        token_cost=0.3,
        cache_hit_refs=["cache:hit"],
    )
    cost_fail = integrate_cost_cache_budget_optimization(
        fixture_id="owner-optimization-stale-cache",
        metric_slices=[metric],
        fetch_cost=0.2,
        browser_cost=0.0,
        token_cost=0.3,
        stale_cache_refs=["cache:stale"],
    )
    drift_pass = integrate_drift_recovery_feedback(
        fixture_id="owner-optimization-integration-success",
        drift_type="selector_drift",
        affected_ref="selector:price",
        retry_class="repairable",
        repair_outcome="review_required",
        memory_advisory_refs=["memory:advisory"],
    )
    drift_fail = integrate_drift_recovery_feedback(
        fixture_id="owner-optimization-unsafe-recovery",
        drift_type="selector_drift",
        affected_ref="selector:price",
        retry_class="unsafe",
        repair_outcome="blocked",
        unsafe_recovery_refs=["repair:unsafe"],
    )
    gate_pass = optimization_regression_release_gate(
        fixture_id="owner-optimization-integration-success",
        lower_integration_refs=[
            "scheduler:ok",
            "normalize:ok",
            "extract:ok",
            "dedupe:ok",
            "ranking:ok",
            cost_pass.id,
            drift_pass.id,
        ],
        metric_slice_refs=[metric.id],
    )
    gate_fail = optimization_regression_release_gate(
        fixture_id="owner-optimization-missing-lower-ref",
        lower_integration_refs=["scheduler:ok"],
        metric_slice_refs=[metric.id],
        missing_lower_integration_refs=["normalize:missing"],
        false_ready_guard_refs=["false-ready:missing-lower"],
    )

    assert cost_pass.completion_result == CompletenessResult.PASS
    assert cost_fail.completion_result == CompletenessResult.FAIL
    assert drift_pass.completion_result == CompletenessResult.PASS
    assert drift_fail.completion_result == CompletenessResult.FAIL
    assert gate_pass.completion_result == CompletenessResult.PASS
    assert gate_fail.completion_result == CompletenessResult.FAIL


def _profile() -> FrontierScoringProfile:
    return FrontierScoringProfile(
        id="frontier-profile:owner",
        profile_refs=["optimization"],
        objective_ref="objective:owner",
        scoring_formula_ref="formula:owner-frontier",
        required_signal_refs=["signal:url", "signal:anchor", "signal:semantic"],
    )


def _html() -> str:
    return """
    <html>
      <body>
        <article class="product-card">
          <h2>Owner Product</h2>
          <span class="price">$42.00</span>
          <button>Sort by rating</button>
          <a href="/next">Next page</a>
        </article>
      </body>
    </html>
    """


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


def _report() -> CrawlerOptimizationReport:
    return CrawlerOptimizationReport(
        id="crawler-optimization-report:owner",
        fixture_id="owner-optimization-integration-success",
        run_ref="run:owner",
        manifest_ref="manifest:owner",
        profile="optimization",
        frontier_profile_ref="frontier-profile:owner",
        frontier_score_refs=["frontier-score:owner"],
        dom_context_refs=["dom-context:owner"],
        extractor_plan_refs=["extractor-plan:owner"],
        extractor_attempt_refs=["extractor-attempt:owner"],
        field_confidence_refs=["field-confidence:owner"],
        canonicalization_refs=["canonical:owner"],
        fingerprint_refs=["fingerprint:owner"],
        identity_decision_refs=["identity:owner"],
        duplicate_suppression_refs=["dedupe:owner"],
        ranking_profile_ref="ranking-profile:owner",
        ranking_score_refs=["ranking-score:owner"],
        ranked_output_set_refs=["ranked-output:owner"],
        ranking_evaluation_refs=["ranking-evaluation:owner"],
        metric_slice_refs=["owner-metric:corpus"],
        crawl_success_rate=0.98,
        precision=0.97,
        recall=0.92,
        extraction_accuracy=0.98,
        duplicate_rate=0.02,
        cost_per_success=0.06,
        latency_p95_ms=2100,
        ranking_ndcg=0.95,
        llm_token_savings_rate=0.43,
        policy_decision_refs=["policy:owner"],
        command_record_refs=["command:owner"],
        event_cursor_refs=["event:owner"],
        outbox_refs=["outbox:owner"],
        replay_bundle_refs=["replay:owner"],
        operator_status="owner_optimization_completed",
        completion_result=CompletenessResult.PASS,
    )
