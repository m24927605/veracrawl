from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphMemoryProductionFailureType,
)
from veracrawl.contracts.graph_memory import (
    GraphMemoryProductionFixtureManifest,
    GraphMemoryProductionRuntimeReport,
)


def _complete_report() -> GraphMemoryProductionRuntimeReport:
    return GraphMemoryProductionRuntimeReport(
        id="graph-memory-production-report:contract",
        fixture_id="contract",
        run_ref="run:contract",
        live_normalization_runtime_report_ref="live-normalization-runtime-report:contract",
        live_evidence_verification_runtime_report_ref=(
            "live-evidence-verification-runtime-report:contract"
        ),
        multi_agent_repair_report_ref="multi-agent-repair-report:contract",
        advanced_graph_projection_report_ref="advanced-graph-report:contract",
        graph_frontier_review_runtime_report_ref="graph-frontier-review-report:contract",
        temporal_kg_runtime_report_ref="temporal-kg-report:contract",
        memory_kernel_report_ref="memory-kernel-report:contract",
        url_graph_refs=["graph-node:contract:url"],
        redirect_graph_refs=["graph-edge:contract:redirect"],
        canonical_graph_refs=["graph-edge:contract:canonical"],
        page_structure_graph_refs=["graph-edge:contract:page-structure"],
        entity_graph_refs=["temporal-kg-identity:contract"],
        task_graph_refs=["task-graph-node:contract"],
        temporal_graph_refs=["temporal-kg-projection:contract"],
        graph_signal_refs=["graph-signal:contract"],
        projection_watermark_refs=["projection-watermark:contract"],
        site_memory_event_refs=["memory-event:contract:site"],
        task_memory_event_refs=["memory-event:contract:task"],
        repair_memory_event_refs=["memory-event:contract:repair"],
        run_diary_memory_event_refs=["run-diary-memory:contract"],
        memory_retrieval_trace_refs=["memory-retrieval-trace:contract"],
        memory_write_refs=["memory-write:contract"],
        memory_freshness_refs=["freshness:contract"],
        memory_invalidation_refs=["invalidation:contract"],
        frontier_decision_refs=["graph-frontier-decision:contract"],
        repair_explanation_refs=["repair-explanation:contract"],
        operator_explanation_refs=["operator-explanation:contract"],
        owner_command_refs=["command:contract:owner"],
        review_escalation_refs=["review-escalation:contract"],
        source_evidence_refs=["evidence-packet:contract"],
        verification_decision_refs=["verification-decision:contract"],
        policy_decision_refs=["policy:contract"],
        privacy_lifecycle_refs=["privacy-lifecycle:contract"],
        command_record_refs=["command-record:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay-bundle:contract",
        operator_status="graph_memory_production_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_graph_memory_report_accepts_complete_pass() -> None:
    report = _complete_report()
    assert report.completion_result == CompletenessResult.PASS
    assert report.graph_signal_refs
    assert report.memory_retrieval_trace_refs
    assert report.source_evidence_refs


def test_graph_memory_report_rejects_missing_dependency_on_pass() -> None:
    with pytest.raises(ValidationError):
        GraphMemoryProductionRuntimeReport(
            **(_complete_report().model_dump() | {"memory_kernel_report_ref": None})
        )


def test_graph_memory_report_rejects_graph_or_memory_as_evidence_on_pass() -> None:
    with pytest.raises(ValidationError):
        GraphMemoryProductionRuntimeReport(
            **(
                _complete_report().model_dump()
                | {"graph_as_evidence_refs": ["graph-signal:bad"]}
            )
        )
    with pytest.raises(ValidationError):
        GraphMemoryProductionRuntimeReport(
            **(
                _complete_report().model_dump()
                | {"memory_as_evidence_refs": ["memory-event:bad"]}
            )
        )


def test_graph_memory_report_requires_typed_failure_details() -> None:
    report = GraphMemoryProductionRuntimeReport(
        id="graph-memory-production-report:fail",
        fixture_id="fail",
        run_ref="run:fail",
        policy_decision_refs=["policy:fail"],
        failure_type=GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE,
        failure_report_refs=["graph-memory-failure:fail"],
        missing_ref_fields=["live_evidence_verification_runtime_report_ref"],
        operator_status=GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert report.failure_type == GraphMemoryProductionFailureType.MISSING_LIVE_EVIDENCE


def test_graph_memory_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        GraphMemoryProductionFixtureManifest(
            id="graph-memory-bad",
            scenario="graph-memory-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=GraphMemoryProductionFailureType.GRAPH_AS_EVIDENCE,
            negative_case=True,
            required_ref_types=["graph", "memory"],
        )


def test_graph_memory_fixture_manifest_requires_ref_types() -> None:
    with pytest.raises(ValidationError):
        GraphMemoryProductionFixtureManifest(
            id="graph-memory-bad",
            scenario="graph-memory-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=GraphMemoryProductionFailureType.GRAPH_AS_EVIDENCE,
            negative_case=True,
        )
