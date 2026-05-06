"""Replay helpers for optimization objective gate records."""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.contracts.crawler_optimization import (
    AgentDecisionLoopEvidence,
    OptimizationObjectiveReleaseGate,
    OptimizationObjectiveScore,
)
from veracrawl.contracts.enums import CompletenessResult


def _missing(required: Mapping[str, object]) -> list[str]:
    return sorted(name for name, value in required.items() if not value)


def missing_objective_score_replay_refs(report: OptimizationObjectiveScore) -> list[str]:
    return _missing(
        {
            "run_ref": report.run_ref,
            "profile_ref": report.profile_ref,
            "score_formula_ref": report.score_formula_ref,
            "metric_slice_refs": report.metric_slice_refs,
            "algorithm_recommendation_refs": report.algorithm_recommendation_refs,
            "policy_decision_refs": report.policy_decision_refs,
            "command_record_refs": report.command_record_refs,
            "event_cursor_refs": report.event_cursor_refs,
            "outbox_refs": report.outbox_refs,
            "artifact_refs": report.artifact_refs,
            "replay_bundle_ref": report.replay_bundle_ref,
        }
    )


def objective_score_replay_passes(report: OptimizationObjectiveScore) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_objective_score_replay_refs(report)
    )


def missing_agent_decision_loop_replay_refs(
    evidence: AgentDecisionLoopEvidence,
) -> list[str]:
    required = {
        "run_ref": evidence.run_ref,
        "objective_score_ref": evidence.objective_score_ref,
        "observe_ref": evidence.observe_ref,
        "think_ref": evidence.think_ref,
        "act_ref": evidence.act_ref,
        "verify_ref": evidence.verify_ref,
        "stop_condition_ref": evidence.stop_condition_ref,
        "deterministic_decision_refs": evidence.deterministic_decision_refs,
        "policy_decision_refs": evidence.policy_decision_refs,
        "command_record_refs": evidence.command_record_refs,
        "event_cursor_refs": evidence.event_cursor_refs,
        "outbox_refs": evidence.outbox_refs,
        "artifact_refs": evidence.artifact_refs,
        "replay_bundle_ref": evidence.replay_bundle_ref,
    }
    if evidence.llm_fallback_used:
        required["llm_fallback_reason_refs"] = evidence.llm_fallback_reason_refs
        required["model_trace_refs"] = evidence.model_trace_refs
    return _missing(required)


def agent_decision_loop_replay_passes(evidence: AgentDecisionLoopEvidence) -> bool:
    return evidence.completion_result == CompletenessResult.PASS and not (
        missing_agent_decision_loop_replay_refs(evidence)
    )


def missing_objective_release_gate_replay_refs(
    gate: OptimizationObjectiveReleaseGate,
) -> list[str]:
    missing = _missing(
        {
            "claim_scope_ref": gate.claim_scope_ref,
            "required_lower_gate_refs": gate.required_lower_gate_refs,
            "present_lower_gate_refs": gate.present_lower_gate_refs,
            "objective_score_refs": gate.objective_score_refs,
            "agent_decision_loop_refs": gate.agent_decision_loop_refs,
            "metric_slice_refs": gate.metric_slice_refs,
            "algorithm_recommendation_refs": gate.algorithm_recommendation_refs,
            "policy_decision_refs": gate.policy_decision_refs,
            "command_record_refs": gate.command_record_refs,
            "event_cursor_refs": gate.event_cursor_refs,
            "outbox_refs": gate.outbox_refs,
            "artifact_refs": gate.artifact_refs,
            "replay_bundle_ref": gate.replay_bundle_ref,
        }
    )
    missing_lower = sorted(
        set(gate.required_lower_gate_refs) - set(gate.present_lower_gate_refs)
    )
    return sorted(
        set(
            [
                *missing,
                *missing_lower,
                *gate.failed_lower_gate_refs,
                *gate.failed_objective_score_refs,
                *gate.failed_agent_decision_loop_refs,
            ]
        )
    )


def objective_release_gate_replay_passes(
    gate: OptimizationObjectiveReleaseGate,
) -> bool:
    return gate.completion_result == CompletenessResult.PASS and not (
        missing_objective_release_gate_replay_refs(gate)
    )
