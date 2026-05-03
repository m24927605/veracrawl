from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityMetricConfusionClass,
    QualityMetricSliceDimension,
)
from veracrawl.contracts.quality_metrics import (
    FieldConfusionRecord,
    PrecisionRecallQualityReport,
    PrecisionRecallSliceMetric,
    QualityMetricManifest,
    QualityMetricThresholds,
)


def _record() -> FieldConfusionRecord:
    return FieldConfusionRecord(
        id="confusion:1",
        field_evaluation_ref="field:1",
        schema_ref="schema:1",
        website_pattern_ref="pattern:1",
        source_type_ref="source:html",
        rendering_mode_ref="rendering:http",
        confidence_bucket_ref="confidence:high",
        confusion_class=QualityMetricConfusionClass.TRUE_POSITIVE,
        evidence_packet_refs=["evidence:1"],
        publication_gate_refs=["publication-gate:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["hash:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:1",
    )


def test_quality_metric_threshold_defaults_are_release_blocking() -> None:
    thresholds = QualityMetricThresholds(id="thresholds:1")
    assert thresholds.min_precision == 0.98
    assert thresholds.min_recall == 0.90
    assert thresholds.min_f1 == 0.94
    assert thresholds.min_critical_field_precision == 0.99


def test_true_positive_cannot_use_model_only_evidence() -> None:
    with pytest.raises(ValidationError):
        FieldConfusionRecord(
            id="confusion:1",
            field_evaluation_ref="field:1",
            schema_ref="schema:1",
            website_pattern_ref="pattern:1",
            source_type_ref="source:html",
            rendering_mode_ref="rendering:http",
            confidence_bucket_ref="confidence:high",
            confusion_class=QualityMetricConfusionClass.TRUE_POSITIVE,
            evidence_packet_refs=["evidence:1"],
            publication_gate_refs=["publication-gate:1"],
            artifact_refs=["artifact:1"],
            content_hash_refs=["hash:1"],
            policy_decision_refs=["policy:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_ref="replay:1",
            model_only_evidence=True,
        )


def test_slice_metric_rates_are_bounded() -> None:
    metric = PrecisionRecallSliceMetric(
        id="metric:corpus",
        dimension=QualityMetricSliceDimension.CORPUS,
        slice_ref="corpus",
        true_positive_count=250,
        false_positive_count=2,
        false_negative_count=10,
        precision=250 / 252,
        recall=250 / 260,
        f1=0.976,
        field_confusion_refs=["confusion:1"],
    )
    assert metric.precision > 0.98


def test_quality_metric_report_requires_trace_refs() -> None:
    report = PrecisionRecallQualityReport(
        id="report:1",
        fixture_id="precision-recall-quality",
        run_ref="run:1",
        thresholds_ref="thresholds:1",
        corpus_metric_ref="metric:corpus",
        slice_metric_refs=["metric:corpus"],
        field_confusion_refs=["confusion:1"],
        precision=0.99,
        recall=0.96,
        f1=0.97,
        critical_field_precision=1.0,
        evidence_packet_refs=["evidence:1"],
        publication_gate_refs=["publication-gate:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["hash:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay:1"],
        operator_status="quality_metrics_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.f1 == 0.97


def test_quality_metric_manifest_supports_quality_profile() -> None:
    manifest = QualityMetricManifest(
        id="precision-recall-quality",
        scenario="precision-recall-quality",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="quality_metrics_completed",
        required_ref_types=["field_confusion"],
    )
    assert manifest.thresholds.min_precision == 0.98
