from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.crawler_optimization import (
    UrlScoringSignals,
    canonicalize_url,
    content_minhash,
    content_simhash,
    run_crawler_optimization_benchmark,
    score_frontier_url,
)
from veracrawl.contracts.crawler_optimization import (
    CrawlerOptimizationManifest,
    FrontierScoringProfile,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest(
    *,
    scenario: str = "crawler-optimization-success",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: CrawlerOptimizationFailureType | None = None,
) -> CrawlerOptimizationManifest:
    return CrawlerOptimizationManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["optimization"],
        objective_ref="objective:crawler-optimization:test",
        expected_completion_result=expected_result,
        expected_operator_status=(
            expected_failure.value if expected_failure else "crawler_optimization_completed"
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_ref_types=["frontier_score", "dom_context", "replay"],
        algorithm_refs=["algorithm:focused-priority-queue"],
        architecture_refs=["architecture:crawler-intelligence-optimization:v1"],
    )


def test_canonicalize_url_removes_tracking_and_sorts_query() -> None:
    decision = canonicalize_url(
        "HTTPS://Example.COM:443/search?utm_source=ad&b=2&a=1&sid=abc",
        fixture_id="fixture:test",
    )

    assert decision.canonical_url == "https://example.com/search?a=1&b=2"
    assert decision.removed_query_params == ["sid", "utm_source"]


def test_frontier_scoring_formula_penalizes_cost_and_risk() -> None:
    profile = FrontierScoringProfile(
        id="frontier-profile:test",
        profile_refs=["optimization"],
        objective_ref="objective:test",
        scoring_formula_ref="formula:test",
        required_signal_refs=["signal:url"],
    )
    low_risk = UrlScoringSignals(0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.0, 0.0)
    high_risk = UrlScoringSignals(0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0)

    assert score_frontier_url(profile, low_risk) > score_frontier_url(profile, high_risk)


def test_content_fingerprints_are_stable_for_same_text() -> None:
    text = "VeraCrawl Pro in stock with stable extraction evidence"

    assert content_simhash(text) == content_simhash(text)
    assert content_minhash(text) == content_minhash(text)


def test_crawler_optimization_runtime_materializes_success_report(tmp_path: Path) -> None:
    result = run_crawler_optimization_benchmark(
        manifest=_manifest(),
        profile="optimization",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.precision >= 0.95
    assert result.report.recall >= 0.88
    assert result.report.extraction_accuracy >= 0.96
    assert result.report.duplicate_rate <= 0.05
    assert result.report.ranking_ndcg >= 0.90
    assert result.report.llm_token_savings_rate >= 0.30
    assert result.frontier_scores[0].final_score >= result.frontier_profile.confidence_threshold
    assert result.dom_contexts[0].retained_node_count < result.dom_contexts[0].original_node_count
    assert result.duplicate_suppression_records[0].suppressed_refs
    assert result.ranked_output_sets[0].sorted_item_refs[0] == "candidate:veracrawl-pro"


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "crawler-optimization-missing-frontier-score",
            CrawlerOptimizationFailureType.MISSING_FRONTIER_SCORE,
        ),
        (
            "crawler-optimization-llm-as-evidence",
            CrawlerOptimizationFailureType.LLM_OUTPUT_AS_EVIDENCE,
        ),
        (
            "crawler-optimization-unsafe-recovery",
            CrawlerOptimizationFailureType.UNSAFE_RECOVERY_ACTION,
        ),
        (
            "crawler-optimization-quality-regression",
            CrawlerOptimizationFailureType.RANKING_QUALITY_REGRESSION,
        ),
        (
            "crawler-optimization-missing-replay",
            CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
        ),
    ],
)
def test_crawler_optimization_runtime_maps_negative_scenarios(
    tmp_path: Path,
    scenario: str,
    failure: CrawlerOptimizationFailureType,
) -> None:
    result = run_crawler_optimization_benchmark(
        manifest=_manifest(
            scenario=scenario,
            expected_result=CompletenessResult.FAIL,
            expected_failure=failure,
        ),
        profile="optimization",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
