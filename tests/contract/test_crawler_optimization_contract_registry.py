from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_crawler_optimization_contracts_registered() -> None:
    for name in {
        "FrontierScoringProfile",
        "FrontierScoreBreakdown",
        "DomContextBundle",
        "ExtractorFallbackPlan",
        "ExtractorAttemptRecord",
        "CanonicalizationDecision",
        "ContentFingerprintRecord",
        "IdentityResolutionDecision",
        "DuplicateSuppressionRecord",
        "RankingProfile",
        "RankingScoreBreakdown",
        "RankedOutputSet",
        "OptimizationMetricSlice",
        "CrawlerOptimizationReport",
        "CrawlerOptimizationManifest",
        "CrawlerOptimizationArchitectureSpec",
        "AlgorithmRecommendation",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_crawler_optimization_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_frontier_score_breakdown": "frontier_score_breakdown_recorded",
        "record_dom_context_bundle": "dom_context_bundle_recorded",
        "record_extractor_fallback_plan": "extractor_fallback_plan_recorded",
        "record_duplicate_suppression": "duplicate_suppression_recorded",
        "record_ranked_output_set": "ranked_output_set_recorded",
        "record_crawler_optimization_report": "crawler_optimization_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    assert FIXTURE_ORACLES["crawler-optimization-success"].negative_case is False
    for fixture_id in [
        "crawler-optimization-missing-frontier-score",
        "crawler-optimization-llm-as-evidence",
        "crawler-optimization-unsafe-recovery",
        "crawler-optimization-quality-regression",
        "crawler-optimization-missing-replay",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_crawler_optimization_ref


def test_crawler_optimization_target_area_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["crawler_intelligence_optimization_gate"]
    assert "FrontierScoreBreakdown" in area.materialized_contract_refs
    assert "DomContextBundle" in area.materialized_contract_refs
    assert "CrawlerOptimizationReport" in area.materialized_contract_refs
    assert validate_registry().ok
