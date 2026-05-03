from __future__ import annotations

from veracrawl.cli.graph_memory_runtime import GraphMemoryProductionFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_graph_memory_success(
    report: GraphMemoryProductionFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == operator_status
    assert report.live_normalization_runtime_report_ref
    assert report.live_evidence_verification_runtime_report_ref
    assert report.multi_agent_repair_report_ref
    assert report.advanced_graph_projection_report_ref
    assert report.graph_frontier_review_runtime_report_ref
    assert report.temporal_kg_runtime_report_ref
    assert report.memory_kernel_report_ref
    assert report.graph_signal_refs
    assert report.memory_retrieval_trace_refs
    assert report.memory_invalidation_refs
    assert report.frontier_decision_refs
    assert report.repair_explanation_refs
    assert report.operator_explanation_refs
    assert report.source_evidence_refs
    assert report.verification_decision_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.graph_as_evidence_refs
    assert not report.memory_as_evidence_refs
    assert not report.stale_memory_refs
    assert not report.missing_ref_fields


def assert_graph_memory_negative(
    report: GraphMemoryProductionFixtureRunReport,
    *,
    operator_status: str,
    failure_type: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type == failure_type
    assert report.failure_report_refs
    assert report.missing_ref_fields
