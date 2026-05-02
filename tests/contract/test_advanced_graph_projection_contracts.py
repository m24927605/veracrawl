from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphSignalType,
    ProjectionJobStatus,
)
from veracrawl.contracts.graph import (
    AdvancedGraphProjectionReport,
    GraphSignal,
    ProjectionMismatchReport,
    ProjectionRebuildJob,
    ProjectionSpec,
)


def test_projection_spec_and_rebuild_job_require_replay_refs() -> None:
    spec = ProjectionSpec(
        id="projection-spec:unit",
        run_ref="run:unit",
        projection_name="advanced_graph_projection",
        input_manifest_refs=["graph-manifest:unit"],
        graph_version="advanced-graph-projection:v1",
        rebuild_policy_ref="rebuild-policy:unit",
        owner_service_ref="owner-service:graph",
        policy_decision_refs=["policy:unit:graph"],
    )
    job = ProjectionRebuildJob(
        id="projection-rebuild-job:unit",
        run_ref="run:unit",
        projection_spec_ref=spec.id,
        input_manifest_refs=spec.input_manifest_refs,
        expected_rebuild_hash="hash",
        actual_rebuild_hash="hash",
        watermark_ref="projection-watermark:unit",
        status=ProjectionJobStatus.REBUILT,
        policy_decision_refs=["policy:unit:graph"],
    )
    assert job.status == ProjectionJobStatus.REBUILT
    with pytest.raises(ValidationError):
        ProjectionRebuildJob(
            id="projection-rebuild-job:bad",
            run_ref="run:bad",
            projection_spec_ref=spec.id,
            input_manifest_refs=spec.input_manifest_refs,
            expected_rebuild_hash="expected",
            actual_rebuild_hash="actual",
            status=ProjectionJobStatus.REBUILT,
            policy_decision_refs=["policy:unit:graph"],
        )


def test_projection_mismatch_requires_different_hashes() -> None:
    with pytest.raises(ValidationError):
        ProjectionMismatchReport(
            id="projection-mismatch:bad",
            run_ref="run:bad",
            projection_rebuild_job_ref="projection-rebuild-job:bad",
            expected_rebuild_hash="same",
            actual_rebuild_hash="same",
            mismatch_ref="mismatch:bad",
            operator_status="projection_mismatch",
        )


def test_graph_signal_cannot_be_marked_as_evidence() -> None:
    with pytest.raises(ValidationError):
        GraphSignal(
            id="graph-signal:bad",
            run_ref="run:bad",
            signal_type=GraphSignalType.FRONTIER_PRIORITY,
            subject_ref="graph-node:bad",
            score=0.7,
            source_graph_refs=["graph-manifest:bad"],
            explanation_ref="explanation:bad",
            policy_decision_refs=["policy:bad:graph"],
            evidence_ref_allowed=True,
        )


def test_advanced_projection_report_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        AdvancedGraphProjectionReport(
            id="advanced-graph-report:bad",
            run_ref="run:bad",
            operator_status="advanced_graph_projection_completed",
            completion_result=CompletenessResult.PASS,
        )
