from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_owner_integration_contracts_registered() -> None:
    for name in {
        "OptimizationOwnerIntegrationRoadmap",
        "SchedulerOptimizationIntegration",
        "NormalizeOptimizationIntegration",
        "ExtractVerifyOptimizationIntegration",
        "DedupeIdentityOptimizationIntegration",
        "RankingPublicationOptimizationIntegration",
        "CostCacheBudgetOptimizationIntegration",
        "DriftRecoveryFeedbackIntegration",
        "OptimizationRegressionReleaseGate",
    }:
        assert name in FOUNDATION_CONTRACTS


def test_owner_integration_commands_events_and_fixtures_registered() -> None:
    expected = {
        "record_optimization_owner_integration_roadmap": (
            "optimization_owner_integration_roadmap_recorded"
        ),
        "record_scheduler_optimization_integration": "scheduler_optimization_integrated",
        "record_normalize_optimization_integration": "normalize_optimization_integrated",
        "record_extract_verify_optimization_integration": (
            "extract_verify_optimization_integrated"
        ),
        "record_dedupe_identity_optimization_integration": (
            "dedupe_identity_optimization_integrated"
        ),
        "record_ranking_publication_optimization_integration": (
            "ranking_publication_optimization_integrated"
        ),
        "record_cost_cache_budget_optimization_integration": (
            "cost_cache_budget_optimization_integrated"
        ),
        "record_drift_recovery_feedback_integration": "drift_recovery_feedback_integrated",
        "record_optimization_regression_release_gate": (
            "optimization_regression_release_gated"
        ),
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES

    assert FIXTURE_ORACLES["owner-optimization-integration-success"].negative_case is False
    for fixture_id in [
        "owner-optimization-policy-blocked-url",
        "owner-optimization-missing-dom-anchor",
        "owner-optimization-llm-as-evidence",
        "owner-optimization-variant-collapse",
        "owner-optimization-stale-cache",
        "owner-optimization-unsafe-recovery",
        "owner-optimization-ranking-regression",
        "owner-optimization-missing-lower-ref",
        "owner-optimization-missing-replay",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True


def test_owner_integration_target_area_extends_existing_optimization_gate() -> None:
    area = TARGET_CONTRACT_AREAS["crawler_intelligence_optimization_gate"]
    assert "SchedulerOptimizationIntegration" in area.materialized_contract_refs
    assert "OptimizationRegressionReleaseGate" in area.materialized_contract_refs
    assert validate_registry().ok
