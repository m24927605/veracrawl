from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphMemoryProductionFailureType,
)
from veracrawl.graph_memory.runtime import run_graph_memory_production_runtime


def test_graph_memory_runtime_success_has_graph_memory_and_evidence_refs() -> None:
    result = run_graph_memory_production_runtime(
        fixture_id="unit-graph-memory",
        scenario="graph-memory-production-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert report.live_normalization_runtime_report_ref
    assert report.live_evidence_verification_runtime_report_ref
    assert report.multi_agent_repair_report_ref
    assert report.advanced_graph_projection_report_ref
    assert report.graph_frontier_review_runtime_report_ref
    assert report.temporal_kg_runtime_report_ref
    assert report.memory_kernel_report_ref
    assert report.url_graph_refs
    assert report.redirect_graph_refs
    assert report.canonical_graph_refs
    assert report.page_structure_graph_refs
    assert report.entity_graph_refs
    assert report.task_graph_refs
    assert report.temporal_graph_refs
    assert report.graph_signal_refs
    assert report.site_memory_event_refs
    assert report.task_memory_event_refs
    assert report.repair_memory_event_refs
    assert report.run_diary_memory_event_refs
    assert report.memory_retrieval_trace_refs
    assert report.memory_invalidation_refs
    assert report.frontier_decision_refs
    assert report.repair_explanation_refs
    assert report.operator_explanation_refs
    assert report.source_evidence_refs
    assert report.verification_decision_refs
    assert report.replay_bundle_ref


def test_graph_memory_runtime_success_variants_have_distinct_operator_status() -> None:
    frontier = run_graph_memory_production_runtime(
        fixture_id="unit-frontier",
        scenario="graph-memory-frontier-priority-success",
    ).report
    repair = run_graph_memory_production_runtime(
        fixture_id="unit-repair",
        scenario="graph-memory-repair-explanation-success",
    ).report
    assert frontier.operator_status == "graph_memory_frontier_priority_completed"
    assert repair.operator_status == "graph_memory_repair_explanation_completed"
    assert "crawl" in frontier.repair_explanation_refs[0]
    assert "extraction" in repair.repair_explanation_refs[0]


def test_graph_memory_runtime_dependency_failures_are_typed() -> None:
    expectations = {
        "graph-memory-missing-live-normalization": (
            GraphMemoryProductionFailureType.MISSING_LIVE_NORMALIZATION
        ),
        "graph-memory-missing-live-evidence": (
            GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE
        ),
        "graph-memory-missing-multi-agent": (
            GraphMemoryProductionFailureType.MISSING_MULTI_AGENT_REPAIR
        ),
        "graph-memory-missing-invalidation": (
            GraphMemoryProductionFailureType.MISSING_INVALIDATION_REF
        ),
        "graph-memory-missing-frontier-explanation": (
            GraphMemoryProductionFailureType.MISSING_FRONTIER_EXPLANATION
        ),
        "graph-memory-replay-mismatch": GraphMemoryProductionFailureType.REPLAY_MISMATCH,
    }
    for scenario, failure in expectations.items():
        report = run_graph_memory_production_runtime(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert report.operator_status == failure.value
        assert report.missing_ref_fields


def test_graph_memory_runtime_boundary_failures_are_typed() -> None:
    graph = run_graph_memory_production_runtime(
        fixture_id="graph-boundary",
        scenario="graph-memory-graph-as-evidence",
    ).report
    memory = run_graph_memory_production_runtime(
        fixture_id="memory-boundary",
        scenario="graph-memory-memory-as-evidence",
    ).report
    stale = run_graph_memory_production_runtime(
        fixture_id="stale-boundary",
        scenario="graph-memory-stale-memory",
    ).report
    assert graph.failure_type == GraphMemoryProductionFailureType.GRAPH_AS_EVIDENCE
    assert graph.graph_as_evidence_refs
    assert memory.failure_type == GraphMemoryProductionFailureType.MEMORY_AS_EVIDENCE
    assert memory.memory_as_evidence_refs
    assert stale.failure_type == GraphMemoryProductionFailureType.STALE_MEMORY_USED
    assert stale.stale_memory_refs
