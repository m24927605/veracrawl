"""Replay helpers for runtime optimization wiring decisions."""

from __future__ import annotations

from veracrawl.contracts.crawler_optimization import (
    RuntimeDedupeRankingDecision,
    RuntimeDomExtractionContext,
    RuntimeFrontierOptimizationDecision,
    RuntimeOptimizationAggregate,
)
from veracrawl.contracts.enums import CompletenessResult


def missing_frontier_decision_replay_refs(
    decision: RuntimeFrontierOptimizationDecision,
) -> list[str]:
    required = {
        "signal_set_ref": decision.signal_set_ref,
        "policy_decision_refs": decision.policy_decision_refs,
        "command_record_refs": decision.command_record_refs,
        "event_cursor_refs": decision.event_cursor_refs,
        "outbox_refs": decision.outbox_refs,
        "replay_bundle_ref": decision.replay_bundle_ref,
    }
    if decision.scheduler_action == "enqueue":
        required["frontier_score_ref"] = decision.frontier_score_ref
    if decision.scheduler_action == "block":
        required["blocked_reason_refs"] = decision.blocked_reason_refs
    return sorted(name for name, value in required.items() if not value)


def frontier_decision_replay_passes(decision: RuntimeFrontierOptimizationDecision) -> bool:
    return not missing_frontier_decision_replay_refs(decision)


def missing_dom_extraction_context_replay_refs(
    context: RuntimeDomExtractionContext,
) -> list[str]:
    required = {
        "normalized_document_ref": context.normalized_document_ref,
        "dom_context_ref": context.dom_context_ref,
        "extractor_plan_ref": context.extractor_plan_ref,
        "extractor_attempt_refs": context.extractor_attempt_refs,
        "field_confidence_refs": context.field_confidence_refs,
        "policy_decision_refs": context.policy_decision_refs,
        "command_record_refs": context.command_record_refs,
        "event_cursor_refs": context.event_cursor_refs,
        "outbox_refs": context.outbox_refs,
        "replay_bundle_ref": context.replay_bundle_ref,
    }
    return sorted(name for name, value in required.items() if not value)


def dom_extraction_context_replay_passes(context: RuntimeDomExtractionContext) -> bool:
    return not missing_dom_extraction_context_replay_refs(context)


def missing_dedupe_ranking_decision_replay_refs(
    decision: RuntimeDedupeRankingDecision,
) -> list[str]:
    required = {
        "input_candidate_refs": decision.input_candidate_refs,
        "canonicalization_refs": decision.canonicalization_refs,
        "fingerprint_refs": decision.fingerprint_refs,
        "identity_decision_refs": decision.identity_decision_refs,
        "duplicate_suppression_ref": decision.duplicate_suppression_ref,
        "ranking_score_refs": decision.ranking_score_refs,
        "ranked_output_set_ref": decision.ranked_output_set_ref,
        "retained_refs": decision.retained_refs,
        "policy_decision_refs": decision.policy_decision_refs,
        "command_record_refs": decision.command_record_refs,
        "event_cursor_refs": decision.event_cursor_refs,
        "outbox_refs": decision.outbox_refs,
        "replay_bundle_ref": decision.replay_bundle_ref,
    }
    return sorted(name for name, value in required.items() if not value)


def dedupe_ranking_decision_replay_passes(decision: RuntimeDedupeRankingDecision) -> bool:
    return not missing_dedupe_ranking_decision_replay_refs(decision)


def missing_runtime_aggregate_replay_refs(
    aggregate: RuntimeOptimizationAggregate,
) -> list[str]:
    required = {
        "lower_decision_refs": aggregate.lower_decision_refs,
        "metric_slice_refs": aggregate.metric_slice_refs,
        "optimization_report_ref": aggregate.optimization_report_ref,
        "policy_decision_refs": aggregate.policy_decision_refs,
        "command_record_refs": aggregate.command_record_refs,
        "event_cursor_refs": aggregate.event_cursor_refs,
        "outbox_refs": aggregate.outbox_refs,
        "replay_bundle_refs": aggregate.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + aggregate.missing_ref_fields))


def runtime_aggregate_replay_passes(aggregate: RuntimeOptimizationAggregate) -> bool:
    return aggregate.completion_result == CompletenessResult.PASS and not (
        missing_runtime_aggregate_replay_refs(aggregate)
    )
