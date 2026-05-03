"""Graph/memory production replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.graph_memory import GraphMemoryProductionRuntimeReport


def missing_graph_memory_replay_refs(
    report: GraphMemoryProductionRuntimeReport,
) -> list[str]:
    required = {
        "live_normalization_runtime_report_ref": (
            report.live_normalization_runtime_report_ref
        ),
        "live_evidence_verification_runtime_report_ref": (
            report.live_evidence_verification_runtime_report_ref
        ),
        "multi_agent_repair_report_ref": report.multi_agent_repair_report_ref,
        "advanced_graph_projection_report_ref": (
            report.advanced_graph_projection_report_ref
        ),
        "graph_frontier_review_runtime_report_ref": (
            report.graph_frontier_review_runtime_report_ref
        ),
        "temporal_kg_runtime_report_ref": report.temporal_kg_runtime_report_ref,
        "memory_kernel_report_ref": report.memory_kernel_report_ref,
        "graph_signal_refs": report.graph_signal_refs,
        "memory_retrieval_trace_refs": report.memory_retrieval_trace_refs,
        "memory_invalidation_refs": report.memory_invalidation_refs,
        "frontier_decision_refs": report.frontier_decision_refs,
        "repair_explanation_refs": report.repair_explanation_refs,
        "operator_explanation_refs": report.operator_explanation_refs,
        "source_evidence_refs": report.source_evidence_refs,
        "verification_decision_refs": report.verification_decision_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def graph_memory_replay_passes(report: GraphMemoryProductionRuntimeReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_graph_memory_replay_refs(report)
        or report.graph_as_evidence_refs
        or report.memory_as_evidence_refs
        or report.stale_memory_refs
    )
