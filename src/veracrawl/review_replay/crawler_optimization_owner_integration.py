"""Replay helpers for optimization owner-service integration records."""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.contracts.crawler_optimization import (
    CostCacheBudgetOptimizationIntegration,
    DedupeIdentityOptimizationIntegration,
    DriftRecoveryFeedbackIntegration,
    ExtractVerifyOptimizationIntegration,
    NormalizeOptimizationIntegration,
    OptimizationRegressionReleaseGate,
    RankingPublicationOptimizationIntegration,
    SchedulerOptimizationIntegration,
)
from veracrawl.contracts.enums import CompletenessResult


def _missing(required: Mapping[str, object]) -> list[str]:
    return sorted(name for name, value in required.items() if not value)


def missing_scheduler_integration_replay_refs(
    integration: SchedulerOptimizationIntegration,
) -> list[str]:
    required = {
        "run_ref": integration.run_ref,
        "frontier_decision_refs": integration.frontier_decision_refs,
        "policy_decision_refs": integration.policy_decision_refs,
        "command_record_refs": integration.command_record_refs,
        "event_cursor_refs": integration.event_cursor_refs,
        "outbox_refs": integration.outbox_refs,
        "replay_bundle_ref": integration.replay_bundle_ref,
    }
    if integration.enqueue_refs:
        required["scheduler_priority_refs"] = integration.scheduler_priority_refs
    if integration.blocked_refs or integration.retired_refs:
        required["stop_reason_refs"] = integration.stop_reason_refs
    return _missing(required)


def scheduler_integration_replay_passes(
    integration: SchedulerOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_scheduler_integration_replay_refs(integration)
    )


def missing_normalize_integration_replay_refs(
    integration: NormalizeOptimizationIntegration,
) -> list[str]:
    return _missing(
        {
            "normalized_document_ref": integration.normalized_document_ref,
            "dom_context_ref": integration.dom_context_ref,
            "retained_node_refs": integration.retained_node_refs,
            "artifact_refs": integration.artifact_refs,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def normalize_integration_replay_passes(
    integration: NormalizeOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_normalize_integration_replay_refs(integration)
    )


def missing_extract_verify_integration_replay_refs(
    integration: ExtractVerifyOptimizationIntegration,
) -> list[str]:
    return _missing(
        {
            "normalized_document_ref": integration.normalized_document_ref,
            "extractor_plan_ref": integration.extractor_plan_ref,
            "field_confidence_refs": integration.field_confidence_refs,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def extract_verify_integration_replay_passes(
    integration: ExtractVerifyOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_extract_verify_integration_replay_refs(integration)
    )


def missing_dedupe_identity_integration_replay_refs(
    integration: DedupeIdentityOptimizationIntegration,
) -> list[str]:
    return _missing(
        {
            "canonicalization_refs": integration.canonicalization_refs,
            "fingerprint_refs": integration.fingerprint_refs,
            "identity_decision_refs": integration.identity_decision_refs,
            "duplicate_suppression_ref": integration.duplicate_suppression_ref,
            "retained_refs": integration.retained_refs,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def dedupe_identity_integration_replay_passes(
    integration: DedupeIdentityOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_dedupe_identity_integration_replay_refs(integration)
    )


def missing_ranking_publication_integration_replay_refs(
    integration: RankingPublicationOptimizationIntegration,
) -> list[str]:
    return _missing(
        {
            "ranked_output_set_ref": integration.ranked_output_set_ref,
            "ranking_score_refs": integration.ranking_score_refs,
            "retained_output_refs": integration.retained_output_refs,
            "verification_status_refs": integration.verification_status_refs,
            "publication_gate_refs": integration.publication_gate_refs,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def ranking_publication_integration_replay_passes(
    integration: RankingPublicationOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_ranking_publication_integration_replay_refs(integration)
    )


def missing_cost_cache_budget_integration_replay_refs(
    integration: CostCacheBudgetOptimizationIntegration,
) -> list[str]:
    return _missing(
        {
            "metric_slice_refs": integration.metric_slice_refs,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def cost_cache_budget_integration_replay_passes(
    integration: CostCacheBudgetOptimizationIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_cost_cache_budget_integration_replay_refs(integration)
    )


def missing_drift_recovery_feedback_replay_refs(
    integration: DriftRecoveryFeedbackIntegration,
) -> list[str]:
    return _missing(
        {
            "affected_ref": integration.affected_ref,
            "retry_class": integration.retry_class,
            "repair_outcome": integration.repair_outcome,
            "policy_decision_refs": integration.policy_decision_refs,
            "command_record_refs": integration.command_record_refs,
            "event_cursor_refs": integration.event_cursor_refs,
            "outbox_refs": integration.outbox_refs,
            "replay_bundle_ref": integration.replay_bundle_ref,
        }
    )


def drift_recovery_feedback_replay_passes(
    integration: DriftRecoveryFeedbackIntegration,
) -> bool:
    return integration.completion_result == CompletenessResult.PASS and not (
        missing_drift_recovery_feedback_replay_refs(integration)
    )


def missing_regression_release_gate_replay_refs(
    gate: OptimizationRegressionReleaseGate,
) -> list[str]:
    missing = _missing(
        {
            "required_lower_integration_kinds": gate.required_lower_integration_kinds,
            "present_lower_integration_kinds": gate.present_lower_integration_kinds,
            "lower_integration_refs": gate.lower_integration_refs,
            "metric_slice_refs": gate.metric_slice_refs,
            "policy_decision_refs": gate.policy_decision_refs,
            "command_record_refs": gate.command_record_refs,
            "event_cursor_refs": gate.event_cursor_refs,
            "outbox_refs": gate.outbox_refs,
            "replay_bundle_ref": gate.replay_bundle_ref,
        }
    )
    return sorted(
        set(
            missing
            + gate.missing_lower_integration_refs
            + gate.failed_lower_integration_refs
            + gate.replay_gap_refs
            + gate.metric_regression_refs
        )
    )


def regression_release_gate_replay_passes(gate: OptimizationRegressionReleaseGate) -> bool:
    return gate.completion_result == CompletenessResult.PASS and not (
        missing_regression_release_gate_replay_refs(gate)
    )
