"""Deterministic advanced graph projection builder."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphFailureType,
    GraphSignalType,
    ProjectionJobStatus,
)
from veracrawl.contracts.graph import (
    AdvancedGraphProjectionReport,
    GraphDeltaReport,
    GraphQualityReport,
    GraphSignal,
    ProjectionMismatchReport,
    ProjectionRebuildJob,
    ProjectionSpec,
    ProjectionWatermark,
    TemporalGraphProjectionRecord,
)


@dataclass(frozen=True)
class AdvancedGraphProjectionResult:
    projection_spec: ProjectionSpec | None
    rebuild_job: ProjectionRebuildJob | None
    mismatch_report: ProjectionMismatchReport | None
    delta_report: GraphDeltaReport | None
    quality_report: GraphQualityReport | None
    signals: list[GraphSignal]
    temporal_records: list[TemporalGraphProjectionRecord]
    watermark: ProjectionWatermark | None
    report: AdvancedGraphProjectionReport


def build_advanced_graph_projection(
    *,
    fixture_id: str,
    scenario: str,
    base_manifest_ref: Ref,
    graph_node_refs: list[Ref],
    graph_edge_refs: list[Ref],
    source_output_refs: list[Ref] | None = None,
    evidence_packet_refs: list[Ref] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> AdvancedGraphProjectionResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:advanced-graph"]
    if not base_manifest_ref or not graph_node_refs or not graph_edge_refs:
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.MISSING_GRAPH_INPUT,
            policy_refs=policy_refs,
        )
    if scenario == "projection-missing-watermark":
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.MISSING_PROJECTION_WATERMARK,
            policy_refs=policy_refs,
            projection_spec=_projection_spec(fixture_id, base_manifest_ref, policy_refs),
        )
    if scenario == "graph-signal-as-evidence":
        return _failure_result(
            fixture_id=fixture_id,
            failure=GraphFailureType.GRAPH_SIGNAL_AS_EVIDENCE,
            policy_refs=policy_refs,
        )

    projection_spec = _projection_spec(fixture_id, base_manifest_ref, policy_refs)
    input_refs = sorted(set([base_manifest_ref, *graph_node_refs, *graph_edge_refs]))
    canonical_hash = stable_hash(
        {
            "fixture_id": fixture_id,
            "scenario": scenario,
            "inputs": input_refs,
            "source_outputs": source_output_refs or [],
            "evidence_packets": evidence_packet_refs or [],
        }
    )
    actual_hash = canonical_hash
    job_status = ProjectionJobStatus.REBUILT
    if scenario == "projection-mismatch":
        actual_hash = stable_hash({"mismatch": canonical_hash})
        job_status = ProjectionJobStatus.MISMATCH

    watermark = ProjectionWatermark(
        id=f"projection-watermark:{fixture_id}:advanced-graph",
        projection_ref=projection_spec.id,
        input_manifest_ref=base_manifest_ref,
        event_cursor_refs=[f"event-cursor:{fixture_id}:advanced-graph"],
        rebuild_hash=actual_hash,
        freshness_ref=f"freshness:{fixture_id}:advanced-graph",
    )
    rebuild_job = ProjectionRebuildJob(
        id=f"projection-rebuild-job:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        projection_spec_ref=projection_spec.id,
        input_manifest_refs=projection_spec.input_manifest_refs,
        expected_rebuild_hash=canonical_hash,
        actual_rebuild_hash=actual_hash,
        watermark_ref=watermark.id,
        status=job_status,
        policy_decision_refs=policy_refs,
    )
    if scenario == "projection-mismatch":
        mismatch_report = ProjectionMismatchReport(
            id=f"projection-mismatch-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            projection_rebuild_job_ref=rebuild_job.id,
            expected_rebuild_hash=canonical_hash,
            actual_rebuild_hash=actual_hash,
            mismatch_ref=f"mismatch:{fixture_id}:advanced-graph",
            operator_status=GraphFailureType.PROJECTION_MISMATCH.value,
        )
        report = AdvancedGraphProjectionReport(
            id=f"advanced-graph-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            projection_spec_ref=projection_spec.id,
            rebuild_job_ref=rebuild_job.id,
            mismatch_report_ref=mismatch_report.id,
            watermark_ref=watermark.id,
            policy_decision_refs=policy_refs,
            failure_report_refs=[f"graph-failure:{fixture_id}:projection_mismatch"],
            missing_ref_fields=[GraphFailureType.PROJECTION_MISMATCH.value],
            operator_status=GraphFailureType.PROJECTION_MISMATCH.value,
            completion_result=CompletenessResult.FAIL,
        )
        return AdvancedGraphProjectionResult(
            projection_spec=projection_spec,
            rebuild_job=rebuild_job,
            mismatch_report=mismatch_report,
            delta_report=None,
            quality_report=None,
            signals=[],
            temporal_records=[],
            watermark=watermark,
            report=report,
        )

    signals = _signals_for(
        fixture_id=fixture_id,
        scenario=scenario,
        subject_ref=graph_node_refs[0],
        source_graph_refs=[base_manifest_ref, *graph_node_refs[:2], *graph_edge_refs[:2]],
        policy_refs=policy_refs,
    )
    temporal_records = _temporal_records_for(
        fixture_id=fixture_id,
        output_refs=source_output_refs or [f"published-output:{fixture_id}:1"],
        evidence_refs=evidence_packet_refs or [f"evidence-packet:{fixture_id}:1"],
        watermark_ref=watermark.id,
    )
    delta_report = GraphDeltaReport(
        id=f"graph-delta-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        previous_manifest_ref=f"graph-manifest:{fixture_id}:previous",
        current_manifest_ref=base_manifest_ref,
        added_node_refs=graph_node_refs,
        removed_node_refs=[],
        added_edge_refs=graph_edge_refs,
        removed_edge_refs=[],
        changed_signal_refs=[signal.id for signal in signals],
        rebuild_hash=canonical_hash,
    )
    quality_report = GraphQualityReport(
        id=f"graph-quality-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        graph_manifest_ref=base_manifest_ref,
        metric_refs=[
            f"metric:{fixture_id}:rebuild-determinism",
            f"metric:{fixture_id}:provenance-coverage",
        ],
        score_refs=[f"score:{fixture_id}:graph-quality"],
        warning_refs=[],
        policy_decision_refs=policy_refs,
    )
    report = AdvancedGraphProjectionReport(
        id=f"advanced-graph-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        projection_spec_ref=projection_spec.id,
        rebuild_job_ref=rebuild_job.id,
        delta_report_ref=delta_report.id,
        quality_report_ref=quality_report.id,
        signal_refs=[signal.id for signal in signals],
        temporal_record_refs=[record.id for record in temporal_records],
        watermark_ref=watermark.id,
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:advanced-graph"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:advanced-graph"],
        outbox_refs=[f"outbox:{fixture_id}:advanced-graph"],
        operator_status="advanced_graph_projection_completed",
        completion_result=CompletenessResult.PASS,
    )
    return AdvancedGraphProjectionResult(
        projection_spec=projection_spec,
        rebuild_job=rebuild_job,
        mismatch_report=None,
        delta_report=delta_report,
        quality_report=quality_report,
        signals=signals,
        temporal_records=temporal_records,
        watermark=watermark,
        report=report,
    )


def _projection_spec(
    fixture_id: str,
    base_manifest_ref: Ref,
    policy_refs: list[Ref],
) -> ProjectionSpec:
    return ProjectionSpec(
        id=f"projection-spec:{fixture_id}:advanced-graph",
        run_ref=f"run:{fixture_id}",
        projection_name="advanced_graph_projection",
        input_manifest_refs=[base_manifest_ref],
        graph_version="advanced-graph-projection:v1",
        rebuild_policy_ref=f"rebuild-policy:{fixture_id}:advanced-graph",
        owner_service_ref="owner-service:graph",
        policy_decision_refs=policy_refs,
    )


def _signals_for(
    *,
    fixture_id: str,
    scenario: str,
    subject_ref: Ref,
    source_graph_refs: list[Ref],
    policy_refs: list[Ref],
) -> list[GraphSignal]:
    signal_types = [GraphSignalType.DEDUP_HINT]
    if scenario == "graph-signal-frontier-review":
        signal_types = [GraphSignalType.FRONTIER_PRIORITY, GraphSignalType.REVIEW_ROUTE]
    if scenario == "temporal-graph-foundation":
        signal_types = [GraphSignalType.DRIFT_RISK]
    return [
        GraphSignal(
            id=f"graph-signal:{fixture_id}:{signal_type.value}",
            run_ref=f"run:{fixture_id}",
            signal_type=signal_type,
            subject_ref=subject_ref,
            score=0.83,
            source_graph_refs=source_graph_refs,
            explanation_ref=f"explanation:{fixture_id}:{signal_type.value}",
            policy_decision_refs=policy_refs,
            evidence_ref_allowed=False,
        )
        for signal_type in signal_types
    ]


def _temporal_records_for(
    *,
    fixture_id: str,
    output_refs: list[Ref],
    evidence_refs: list[Ref],
    watermark_ref: Ref,
) -> list[TemporalGraphProjectionRecord]:
    return [
        TemporalGraphProjectionRecord(
            id=f"temporal-graph-record:{fixture_id}:entity-1",
            run_ref=f"run:{fixture_id}",
            source_output_refs=output_refs,
            valid_from_ref=f"valid-from:{fixture_id}:published",
            valid_to_ref=None,
            entity_identity_ref=f"entity-identity:{fixture_id}:1",
            evidence_packet_refs=evidence_refs,
            projection_watermark_ref=watermark_ref,
        )
    ]


def _failure_result(
    *,
    fixture_id: str,
    failure: GraphFailureType,
    policy_refs: list[Ref],
    projection_spec: ProjectionSpec | None = None,
) -> AdvancedGraphProjectionResult:
    return AdvancedGraphProjectionResult(
        projection_spec=projection_spec,
        rebuild_job=None,
        mismatch_report=None,
        delta_report=None,
        quality_report=None,
        signals=[],
        temporal_records=[],
        watermark=None,
        report=AdvancedGraphProjectionReport(
            id=f"advanced-graph-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            projection_spec_ref=projection_spec.id if projection_spec else None,
            policy_decision_refs=policy_refs,
            failure_report_refs=[f"graph-failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=[failure.value],
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        ),
    )
