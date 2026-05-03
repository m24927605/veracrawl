"""Deterministic graph and memory production runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.agents.orchestration import MultiAgentRepairResult, run_multi_agent_repair
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphMemoryProductionFailureType,
)
from veracrawl.contracts.graph_memory import GraphMemoryProductionRuntimeReport
from veracrawl.graph.frontier_review import (
    GraphFrontierReviewRuntimeResult,
    run_graph_frontier_review_runtime_gate,
)
from veracrawl.graph.projection import (
    AdvancedGraphProjectionResult,
    build_advanced_graph_projection,
)
from veracrawl.graph.temporal_kg import TemporalKGRuntimeResult, run_temporal_kg_runtime_gate
from veracrawl.memory.kernel import MemoryKernelResult, run_memory_kernel


@dataclass(frozen=True)
class GraphMemoryProductionRuntimeResult:
    report: GraphMemoryProductionRuntimeReport
    advanced_graph: AdvancedGraphProjectionResult | None = None
    frontier_review: GraphFrontierReviewRuntimeResult | None = None
    temporal_kg: TemporalKGRuntimeResult | None = None
    memory: MemoryKernelResult | None = None
    multi_agent: MultiAgentRepairResult | None = None


_FAILURES: dict[str, tuple[GraphMemoryProductionFailureType, str]] = {
    "graph-memory-missing-live-normalization": (
        GraphMemoryProductionFailureType.MISSING_LIVE_NORMALIZATION,
        "live_normalization_runtime_report_ref",
    ),
    "graph-memory-missing-live-evidence": (
        GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE,
        "live_evidence_verification_runtime_report_ref",
    ),
    "graph-memory-missing-multi-agent": (
        GraphMemoryProductionFailureType.MISSING_MULTI_AGENT_REPAIR,
        "multi_agent_repair_report_ref",
    ),
    "graph-memory-missing-invalidation": (
        GraphMemoryProductionFailureType.MISSING_INVALIDATION_REF,
        "memory_invalidation_refs",
    ),
    "graph-memory-missing-frontier-explanation": (
        GraphMemoryProductionFailureType.MISSING_FRONTIER_EXPLANATION,
        "frontier_decision_refs",
    ),
    "graph-memory-replay-mismatch": (
        GraphMemoryProductionFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_graph_memory_production_runtime(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> GraphMemoryProductionRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:graph-memory"]
    advanced_graph = build_advanced_graph_projection(
        fixture_id=fixture_id,
        scenario="graph-signal-frontier-review",
        base_manifest_ref=f"graph-manifest:{fixture_id}:basic-site",
        graph_node_refs=[
            f"graph-node:{fixture_id}:url:home",
            f"graph-node:{fixture_id}:url:listing",
            f"graph-node:{fixture_id}:canonical:detail",
            f"graph-node:{fixture_id}:page-structure:listing",
        ],
        graph_edge_refs=[
            f"graph-edge:{fixture_id}:hyperlink:home-listing",
            f"graph-edge:{fixture_id}:canonical:detail",
            f"graph-edge:{fixture_id}:redirect:http-https",
            f"graph-edge:{fixture_id}:page-structure:listing",
        ],
        source_output_refs=[f"published-output:{fixture_id}:verified"],
        evidence_packet_refs=[f"evidence-packet:{fixture_id}:accepted"],
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:advanced-graph"],
    )
    frontier_review = run_graph_frontier_review_runtime_gate(
        fixture_id=fixture_id,
        scenario="graph-frontier-review-success",
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:graph-frontier-review"],
    )
    temporal_kg = run_temporal_kg_runtime_gate(
        fixture_id=fixture_id,
        scenario="temporal-kg-projection-success",
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:temporal-kg"],
    )
    memory = run_memory_kernel(
        fixture_id=fixture_id,
        scenario="memory-write-retrieve-success",
        evidence_refs=[f"evidence-packet:{fixture_id}:accepted"],
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:memory"],
    )
    multi_agent = run_multi_agent_repair(
        fixture_id=fixture_id,
        scenario=_multi_agent_scenario(scenario),
        policy_decision_refs=[*policy_refs, f"policy:{fixture_id}:multi-agent"],
        agent_model_adapter_runtime_report_ref=(
            f"agent-model-adapter-runtime-report:{fixture_id}"
        ),
        live_evidence_verification_runtime_report_ref=(
            f"live-evidence-verification-runtime-report:{fixture_id}"
        ),
    )

    if scenario == "graph-memory-graph-as-evidence":
        return _boundary_failure_result(
            fixture_id=fixture_id,
            failure=GraphMemoryProductionFailureType.GRAPH_AS_EVIDENCE,
            policy_refs=policy_refs,
            graph_as_evidence_refs=[
                f"graph-signal:{fixture_id}:frontier_priority",
                f"temporal-kg-projection:{fixture_id}:fact-1",
            ],
            advanced_graph=advanced_graph,
            frontier_review=frontier_review,
            temporal_kg=temporal_kg,
            memory=memory,
            multi_agent=multi_agent,
        )
    if scenario == "graph-memory-memory-as-evidence":
        return _boundary_failure_result(
            fixture_id=fixture_id,
            failure=GraphMemoryProductionFailureType.MEMORY_AS_EVIDENCE,
            policy_refs=policy_refs,
            memory_as_evidence_refs=[f"memory-event:{fixture_id}:site-behavior"],
            advanced_graph=advanced_graph,
            frontier_review=frontier_review,
            temporal_kg=temporal_kg,
            memory=memory,
            multi_agent=multi_agent,
        )
    if scenario == "graph-memory-stale-memory":
        return _boundary_failure_result(
            fixture_id=fixture_id,
            failure=GraphMemoryProductionFailureType.STALE_MEMORY_USED,
            policy_refs=policy_refs,
            stale_memory_refs=[f"memory-event:{fixture_id}:stale-repair"],
            advanced_graph=advanced_graph,
            frontier_review=frontier_review,
            temporal_kg=temporal_kg,
            memory=memory,
            multi_agent=multi_agent,
        )
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _dependency_failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
            advanced_graph=advanced_graph,
            frontier_review=frontier_review,
            temporal_kg=temporal_kg,
            memory=memory,
            multi_agent=multi_agent,
        )

    report = _pass_report(
        fixture_id=fixture_id,
        scenario=scenario,
        policy_refs=policy_refs,
        advanced_graph=advanced_graph,
        frontier_review=frontier_review,
        temporal_kg=temporal_kg,
        memory=memory,
        multi_agent=multi_agent,
    )
    return GraphMemoryProductionRuntimeResult(
        report=report,
        advanced_graph=advanced_graph,
        frontier_review=frontier_review,
        temporal_kg=temporal_kg,
        memory=memory,
        multi_agent=multi_agent,
    )


def _pass_report(
    *,
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
    advanced_graph: AdvancedGraphProjectionResult,
    frontier_review: GraphFrontierReviewRuntimeResult,
    temporal_kg: TemporalKGRuntimeResult,
    memory: MemoryKernelResult,
    multi_agent: MultiAgentRepairResult,
) -> GraphMemoryProductionRuntimeReport:
    advanced_watermark_refs = _optional_ref(advanced_graph.report.watermark_ref)
    memory_retrieval_trace_refs = _optional_ref(memory.report.retrieval_trace_ref)
    return GraphMemoryProductionRuntimeReport(
        id=f"graph-memory-production-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_normalization_runtime_report_ref=(
            f"live-normalization-runtime-report:{fixture_id}"
        ),
        live_evidence_verification_runtime_report_ref=(
            f"live-evidence-verification-runtime-report:{fixture_id}"
        ),
        multi_agent_repair_report_ref=multi_agent.report.id,
        advanced_graph_projection_report_ref=advanced_graph.report.id,
        graph_frontier_review_runtime_report_ref=frontier_review.report.id,
        temporal_kg_runtime_report_ref=temporal_kg.report.id,
        memory_kernel_report_ref=memory.report.id,
        url_graph_refs=[
            f"graph-node:{fixture_id}:url:home",
            f"graph-edge:{fixture_id}:hyperlink:home-listing",
        ],
        redirect_graph_refs=[f"graph-edge:{fixture_id}:redirect:http-https"],
        canonical_graph_refs=[
            f"graph-node:{fixture_id}:canonical:detail",
            f"graph-edge:{fixture_id}:canonical:detail",
        ],
        page_structure_graph_refs=[
            f"graph-node:{fixture_id}:page-structure:listing",
            f"graph-edge:{fixture_id}:page-structure:listing",
        ],
        entity_graph_refs=[*temporal_kg.report.identity_refs],
        task_graph_refs=[
            f"task-graph-node:{fixture_id}:crawl-plan",
            f"task-graph-edge:{fixture_id}:frontier-to-repair",
        ],
        temporal_graph_refs=[
            *advanced_graph.report.temporal_record_refs,
            *temporal_kg.report.projection_record_refs,
        ],
        graph_signal_refs=[
            *advanced_graph.report.signal_refs,
            *frontier_review.report.graph_signal_refs,
        ],
        projection_watermark_refs=[
            *advanced_watermark_refs,
            *temporal_kg.report.projection_watermark_refs,
        ],
        site_memory_event_refs=[f"memory-event:{fixture_id}:site-behavior"],
        task_memory_event_refs=[f"memory-event:{fixture_id}:task-context"],
        repair_memory_event_refs=[f"memory-event:{fixture_id}:repair-strategy"],
        run_diary_memory_event_refs=[f"run-diary-memory:{fixture_id}:agent-diary"],
        memory_retrieval_trace_refs=[
            *memory_retrieval_trace_refs,
            f"memory-retrieval-trace:{fixture_id}:task-context",
            f"memory-retrieval-trace:{fixture_id}:repair",
        ],
        memory_write_refs=[
            *memory.report.memory_event_refs,
            f"memory-write:{fixture_id}:task-context",
            f"memory-write:{fixture_id}:repair",
            f"memory-write:{fixture_id}:run-diary",
        ],
        memory_freshness_refs=[
            f"freshness:{fixture_id}:memory",
            f"freshness-cutoff:{fixture_id}:memory",
        ],
        memory_invalidation_refs=[
            f"invalidation:{fixture_id}:stale-memory-excluded",
            f"excluded-memory:{fixture_id}:stale-repair",
        ],
        frontier_decision_refs=frontier_review.report.frontier_decision_refs,
        repair_explanation_refs=[
            f"repair-explanation:{fixture_id}:{_repair_kind(scenario)}",
            *multi_agent.report.repair_signal_refs,
        ],
        operator_explanation_refs=[
            f"operator-explanation:{fixture_id}:graph-memory-influence",
            *frontier_review.report.explanation_refs,
        ],
        owner_command_refs=multi_agent.report.owner_command_refs,
        review_escalation_refs=multi_agent.report.review_escalation_refs,
        source_evidence_refs=[
            f"evidence-packet:{fixture_id}:accepted",
            f"source-anchor:{fixture_id}:primary",
        ],
        verification_decision_refs=[f"verification-decision:{fixture_id}:accepted"],
        policy_decision_refs=[
            *policy_refs,
            *advanced_graph.report.policy_decision_refs,
            *frontier_review.report.policy_decision_refs,
            *temporal_kg.report.policy_decision_refs,
            *memory.report.policy_decision_refs,
            *multi_agent.report.policy_decision_refs,
            f"policy:{fixture_id}:source-evidence-boundary",
        ],
        privacy_lifecycle_refs=[f"privacy-lifecycle:{fixture_id}:graph-memory"],
        command_record_refs=[
            f"command-record:{fixture_id}:graph-memory",
            *advanced_graph.report.command_record_refs,
            *frontier_review.report.command_record_refs,
            *temporal_kg.report.command_record_refs,
            *memory.report.command_record_refs,
            *multi_agent.report.command_record_refs,
        ],
        event_cursor_refs=[
            f"event-cursor:{fixture_id}:graph-memory",
            *advanced_graph.report.event_cursor_refs,
            *frontier_review.report.event_cursor_refs,
            *temporal_kg.report.event_cursor_refs,
            *memory.report.event_cursor_refs,
            *multi_agent.report.event_cursor_refs,
        ],
        outbox_refs=[
            f"outbox:{fixture_id}:graph-memory",
            *advanced_graph.report.outbox_refs,
            *frontier_review.report.outbox_refs,
            *temporal_kg.report.outbox_refs,
            *memory.report.outbox_refs,
            *multi_agent.report.outbox_refs,
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:graph-memory",
        operator_status=_operator_status(scenario),
        completion_result=CompletenessResult.PASS,
    )


def _dependency_failure_result(
    *,
    fixture_id: str,
    failure: GraphMemoryProductionFailureType,
    missing_field: str,
    policy_refs: list[Ref],
    advanced_graph: AdvancedGraphProjectionResult,
    frontier_review: GraphFrontierReviewRuntimeResult,
    temporal_kg: TemporalKGRuntimeResult,
    memory: MemoryKernelResult,
    multi_agent: MultiAgentRepairResult,
) -> GraphMemoryProductionRuntimeResult:
    report = _failure_report(
        fixture_id=fixture_id,
        failure=failure,
        policy_refs=policy_refs,
        missing_ref_fields=[missing_field],
    )
    return GraphMemoryProductionRuntimeResult(
        report=report,
        advanced_graph=advanced_graph,
        frontier_review=frontier_review,
        temporal_kg=temporal_kg,
        memory=memory,
        multi_agent=multi_agent,
    )


def _boundary_failure_result(
    *,
    fixture_id: str,
    failure: GraphMemoryProductionFailureType,
    policy_refs: list[Ref],
    graph_as_evidence_refs: list[Ref] | None = None,
    memory_as_evidence_refs: list[Ref] | None = None,
    stale_memory_refs: list[Ref] | None = None,
    advanced_graph: AdvancedGraphProjectionResult,
    frontier_review: GraphFrontierReviewRuntimeResult,
    temporal_kg: TemporalKGRuntimeResult,
    memory: MemoryKernelResult,
    multi_agent: MultiAgentRepairResult,
) -> GraphMemoryProductionRuntimeResult:
    report = _failure_report(
        fixture_id=fixture_id,
        failure=failure,
        policy_refs=policy_refs,
        graph_as_evidence_refs=graph_as_evidence_refs,
        memory_as_evidence_refs=memory_as_evidence_refs,
        stale_memory_refs=stale_memory_refs,
    )
    return GraphMemoryProductionRuntimeResult(
        report=report,
        advanced_graph=advanced_graph,
        frontier_review=frontier_review,
        temporal_kg=temporal_kg,
        memory=memory,
        multi_agent=multi_agent,
    )


def _failure_report(
    *,
    fixture_id: str,
    failure: GraphMemoryProductionFailureType,
    policy_refs: list[Ref],
    missing_ref_fields: list[str] | None = None,
    graph_as_evidence_refs: list[Ref] | None = None,
    memory_as_evidence_refs: list[Ref] | None = None,
    stale_memory_refs: list[Ref] | None = None,
) -> GraphMemoryProductionRuntimeReport:
    return GraphMemoryProductionRuntimeReport(
        id=f"graph-memory-production-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        failure_type=failure,
        failure_report_refs=[f"graph-memory-failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=missing_ref_fields or [failure.value],
        graph_as_evidence_refs=graph_as_evidence_refs or [],
        memory_as_evidence_refs=memory_as_evidence_refs or [],
        stale_memory_refs=stale_memory_refs or [],
        diagnostics=[failure.value],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _multi_agent_scenario(scenario: str) -> str:
    if scenario == "graph-memory-repair-explanation-success":
        return "extraction-repair-success"
    if scenario == "graph-memory-frontier-priority-success":
        return "crawl-repair-success"
    return "multi-agent-repair-success"


def _optional_ref(value: Ref | None) -> list[Ref]:
    return [value] if value else []


def _repair_kind(scenario: str) -> str:
    if scenario == "graph-memory-frontier-priority-success":
        return "crawl"
    if scenario == "graph-memory-repair-explanation-success":
        return "extraction"
    return "drift"


def _operator_status(scenario: str) -> str:
    if scenario == "graph-memory-frontier-priority-success":
        return "graph_memory_frontier_priority_completed"
    if scenario == "graph-memory-repair-explanation-success":
        return "graph_memory_repair_explanation_completed"
    return "graph_memory_production_completed"
