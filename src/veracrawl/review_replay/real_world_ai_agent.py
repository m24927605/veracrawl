"""Replay checks for the real-world AI agent benchmark."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.real_world_ai_agent import (
    RealWorldAIAgentBenchmarkRunReport,
    RealWorldAIAgentDecisionTrace,
    RealWorldAIAgentExtractionCandidate,
)


def real_world_ai_agent_decision_replay_passes(
    decision: RealWorldAIAgentDecisionTrace,
) -> bool:
    return (
        decision.completion_result == CompletenessResult.PASS
        and bool(decision.replay_bundle_ref)
        and bool(decision.command_record_refs)
        and bool(decision.event_cursor_refs)
        and bool(decision.outbox_refs)
        and bool(decision.model_call_trace_ref)
        and bool(decision.agent_action_trace_ref)
        and bool(decision.tool_call_trace_refs)
        and bool(decision.context_bundle_trace_ref)
    )


def real_world_ai_agent_candidate_replay_passes(
    candidate: RealWorldAIAgentExtractionCandidate,
) -> bool:
    return (
        candidate.completion_result == CompletenessResult.PASS
        and bool(candidate.replay_bundle_ref)
        and bool(candidate.command_record_refs)
        and bool(candidate.event_cursor_refs)
        and bool(candidate.outbox_refs)
        and bool(candidate.source_anchor_refs)
        and bool(candidate.artifact_refs)
        and bool(candidate.content_hash_refs)
    )


def real_world_ai_agent_report_replay_passes(
    report: RealWorldAIAgentBenchmarkRunReport,
) -> bool:
    return (
        report.completion_result == CompletenessResult.PASS
        and bool(report.real_world_benchmark_run_report_ref)
        and bool(report.replay_bundle_refs)
        and bool(report.command_record_refs)
        and bool(report.event_cursor_refs)
        and bool(report.outbox_refs)
        and bool(report.model_call_trace_refs)
        and bool(report.agent_action_trace_refs)
        and bool(report.tool_call_trace_refs)
        and bool(report.context_bundle_trace_refs)
        and not report.llm_output_evidence_refs
        and not report.direct_publication_refs
        and not report.framework_native_state_refs
    )
