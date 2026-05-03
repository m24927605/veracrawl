"""Precision/recall quality metric benchmark runtime."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityMetricConfusionClass,
    QualityMetricFailureType,
    QualityMetricSliceDimension,
)
from veracrawl.contracts.quality_metrics import (
    FieldConfusionRecord,
    PrecisionRecallQualityReport,
    PrecisionRecallSliceMetric,
    QualityMetricManifest,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class QualityMetricBenchmarkResult:
    report: PrecisionRecallQualityReport
    confusion_records: list[FieldConfusionRecord]
    slice_metrics: list[PrecisionRecallSliceMetric]


_DIRECT_FAILURES: dict[str, tuple[QualityMetricFailureType, str]] = {
    "precision-recall-low-precision": (
        QualityMetricFailureType.PRECISION_BELOW_THRESHOLD,
        "precision",
    ),
    "precision-recall-low-recall": (
        QualityMetricFailureType.RECALL_BELOW_THRESHOLD,
        "recall",
    ),
    "precision-recall-low-f1": (QualityMetricFailureType.F1_BELOW_THRESHOLD, "f1"),
    "precision-recall-hidden-false-positive": (
        QualityMetricFailureType.HIDDEN_FALSE_POSITIVE,
        "false_positive_count",
    ),
    "precision-recall-llm-true-positive": (
        QualityMetricFailureType.LLM_AS_TRUE_POSITIVE,
        "model_only_evidence",
    ),
    "precision-recall-replay-missing": (
        QualityMetricFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_refs",
    ),
}


def run_quality_metric_benchmark(
    *,
    manifest: QualityMetricManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> QualityMetricBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"quality metric fixture {manifest.id} does not support {profile}")

    records = _generate_records(manifest)
    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        report = _direct_failure_report(manifest, records, failure, missing)
        store.save_canonical_model("quality_metric_reports", report.id, report)
        return QualityMetricBenchmarkResult(
            report=report,
            confusion_records=records,
            slice_metrics=[],
        )

    records = [
        _record_confusion_event(manifest.id, record, store) for record in records
    ]
    slice_metrics = _build_slice_metrics(manifest.id, records)
    report = _build_report(manifest, records, slice_metrics)
    store.save_canonical_model("quality_metric_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("quality_metric_reports", report.id, report)
    return QualityMetricBenchmarkResult(
        report=report,
        confusion_records=records,
        slice_metrics=slice_metrics,
    )


def _generate_records(manifest: QualityMetricManifest) -> list[FieldConfusionRecord]:
    specs = [
        (QualityMetricConfusionClass.TRUE_POSITIVE, manifest.generated_true_positive_count),
        (QualityMetricConfusionClass.FALSE_POSITIVE, manifest.generated_false_positive_count),
        (QualityMetricConfusionClass.FALSE_NEGATIVE, manifest.generated_false_negative_count),
        (QualityMetricConfusionClass.TRUE_NEGATIVE, manifest.generated_true_negative_count),
        (QualityMetricConfusionClass.ABSTAIN, manifest.generated_abstain_count),
        (QualityMetricConfusionClass.UNSUPPORTED, manifest.generated_unsupported_count),
        (QualityMetricConfusionClass.NEEDS_REVIEW, manifest.generated_needs_review_count),
    ]
    records: list[FieldConfusionRecord] = []
    index = 1
    for confusion_class, count in specs:
        for _ in range(count):
            records.append(_generated_record(manifest.id, index, confusion_class))
            index += 1
    return records


def _generated_record(
    fixture_id: str,
    index: int,
    confusion_class: QualityMetricConfusionClass,
) -> FieldConfusionRecord:
    record_id = f"field-confusion:{fixture_id}:{index:04d}"
    return FieldConfusionRecord(
        id=record_id,
        field_evaluation_ref=f"field-evaluation:{fixture_id}:{index:04d}",
        schema_ref=f"schema:{(index % 8) + 1:02d}",
        website_pattern_ref=f"pattern:{(index % 5) + 1:02d}",
        source_type_ref=f"source-type:{(index % 4) + 1:02d}",
        rendering_mode_ref="rendering:browser" if index % 3 == 0 else "rendering:http",
        confidence_bucket_ref=f"confidence:{(index % 5) + 1}",
        confusion_class=confusion_class,
        critical_field=index <= 201,
        evidence_packet_refs=[f"evidence-packet:{fixture_id}:{index:04d}"],
        publication_gate_refs=[f"publication-gate:{fixture_id}:{index:04d}"],
        artifact_refs=[f"artifact:{fixture_id}:{index:04d}"],
        content_hash_refs=[f"content-hash:{fixture_id}:{index:04d}"],
        policy_decision_refs=[f"policy:quality-metrics:{fixture_id}:{index:04d}"],
        command_record_refs=[f"command:upstream:{fixture_id}:{index:04d}"],
        event_cursor_refs=[f"event-cursor:upstream:{fixture_id}:{index:04d}"],
        outbox_refs=[f"outbox:upstream:{fixture_id}:{index:04d}"],
        replay_bundle_ref=f"replay-bundle:field-confusion:{fixture_id}:{index:04d}",
    )


def _record_confusion_event(
    manifest_id: str,
    record: FieldConfusionRecord,
    store: ProductionPersistenceStore,
) -> FieldConfusionRecord:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{record.id}",
        command_type="record_quality_metric_confusion",
        target_aggregate_type="FieldConfusionRecord",
        target_aggregate_id=record.id,
        event_type="quality_metric_confusion_recorded",
        output_refs=[record.id],
        policy_decision_refs=record.policy_decision_refs,
        store=store,
    )
    updated = record.model_copy(
        update={
            "command_record_refs": sorted(set(record.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(record.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(record.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("quality_metric_confusion_records", updated.id, updated)
    return updated


def _build_slice_metrics(
    manifest_id: str,
    records: list[FieldConfusionRecord],
) -> list[PrecisionRecallSliceMetric]:
    slices = [
        (QualityMetricSliceDimension.CORPUS, "corpus"),
        (QualityMetricSliceDimension.SCHEMA, "schema:01"),
        (QualityMetricSliceDimension.WEBSITE_PATTERN, "pattern:01"),
        (QualityMetricSliceDimension.SOURCE_TYPE, "source-type:01"),
        (QualityMetricSliceDimension.RENDERING_MODE, "rendering:http"),
        (QualityMetricSliceDimension.CONFIDENCE_BUCKET, "confidence:1"),
    ]
    metrics = []
    for dimension, slice_ref in slices:
        selected = records if dimension == QualityMetricSliceDimension.CORPUS else [
            record for record in records if _record_in_slice(record, dimension, slice_ref)
        ]
        metrics.append(_metric_for_records(manifest_id, dimension, slice_ref, selected))
    return metrics


def _record_in_slice(
    record: FieldConfusionRecord,
    dimension: QualityMetricSliceDimension,
    slice_ref: str,
) -> bool:
    field_name = {
        QualityMetricSliceDimension.SCHEMA: "schema_ref",
        QualityMetricSliceDimension.WEBSITE_PATTERN: "website_pattern_ref",
        QualityMetricSliceDimension.SOURCE_TYPE: "source_type_ref",
        QualityMetricSliceDimension.RENDERING_MODE: "rendering_mode_ref",
        QualityMetricSliceDimension.CONFIDENCE_BUCKET: "confidence_bucket_ref",
    }.get(dimension)
    return bool(field_name and getattr(record, field_name) == slice_ref)


def _metric_for_records(
    manifest_id: str,
    dimension: QualityMetricSliceDimension,
    slice_ref: str,
    records: list[FieldConfusionRecord],
) -> PrecisionRecallSliceMetric:
    tp = _count(records, QualityMetricConfusionClass.TRUE_POSITIVE)
    fp = _count(records, QualityMetricConfusionClass.FALSE_POSITIVE)
    fn = _count(records, QualityMetricConfusionClass.FALSE_NEGATIVE)
    tn = _count(records, QualityMetricConfusionClass.TRUE_NEGATIVE)
    abstain = _count(records, QualityMetricConfusionClass.ABSTAIN)
    unsupported = _count(records, QualityMetricConfusionClass.UNSUPPORTED)
    needs_review = _count(records, QualityMetricConfusionClass.NEEDS_REVIEW)
    total = max(1, tp + fp + fn + tn + abstain + unsupported + needs_review)
    precision = _safe_rate(tp, tp + fp)
    recall = _safe_rate(tp, tp + fn)
    f1 = _safe_rate(2 * precision * recall, precision + recall)
    return PrecisionRecallSliceMetric(
        id=f"quality-slice:{manifest_id}:{dimension.value}:{slice_ref}",
        dimension=dimension,
        slice_ref=slice_ref,
        true_positive_count=tp,
        false_positive_count=fp,
        false_negative_count=fn,
        true_negative_count=tn,
        abstain_count=abstain,
        unsupported_count=unsupported,
        needs_review_count=needs_review,
        precision=precision,
        recall=recall,
        f1=f1,
        false_positive_rate=_safe_rate(fp, fp + tn),
        false_negative_rate=_safe_rate(fn, fn + tp),
        abstention_rate=abstain / total,
        unsupported_rate=unsupported / total,
        needs_review_rate=needs_review / total,
        field_confusion_refs=[record.id for record in records],
    )


def _build_report(
    manifest: QualityMetricManifest,
    records: list[FieldConfusionRecord],
    slice_metrics: list[PrecisionRecallSliceMetric],
) -> PrecisionRecallQualityReport:
    corpus = slice_metrics[0]
    critical_records = [record for record in records if record.critical_field]
    critical_precision = _safe_rate(
        _count(critical_records, QualityMetricConfusionClass.TRUE_POSITIVE),
        _count(critical_records, QualityMetricConfusionClass.TRUE_POSITIVE)
        + _count(critical_records, QualityMetricConfusionClass.FALSE_POSITIVE),
    )
    failure_type, diagnostics, missing = _threshold_failure(
        manifest,
        corpus,
        critical_precision,
    )
    passing = failure_type is None
    return PrecisionRecallQualityReport(
        id=f"precision-recall-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        corpus_metric_ref=corpus.id,
        slice_metric_refs=[item.id for item in slice_metrics],
        field_confusion_refs=[item.id for item in records],
        precision=corpus.precision,
        recall=corpus.recall,
        f1=corpus.f1,
        critical_field_precision=critical_precision,
        false_positive_rate=corpus.false_positive_rate,
        false_negative_rate=corpus.false_negative_rate,
        abstention_rate=corpus.abstention_rate,
        unsupported_rate=corpus.unsupported_rate,
        needs_review_rate=corpus.needs_review_rate,
        evidence_packet_refs=_collect("evidence_packet_refs", records),
        publication_gate_refs=_collect("publication_gate_refs", records),
        artifact_refs=_collect("artifact_refs", records),
        content_hash_refs=_collect("content_hash_refs", records),
        policy_decision_refs=_collect("policy_decision_refs", records),
        command_record_refs=_collect("command_record_refs", records),
        event_cursor_refs=_collect("event_cursor_refs", records),
        outbox_refs=_collect("outbox_refs", records),
        replay_bundle_refs=_collect_one("replay_bundle_ref", records),
        failure_report_refs=[f"failure:{manifest.id}:{failure_type.value}"]
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "quality_metrics_completed",
        completion_result=CompletenessResult.PASS if passing else CompletenessResult.FAIL,
    )


def _threshold_failure(
    manifest: QualityMetricManifest,
    corpus: PrecisionRecallSliceMetric,
    critical_precision: float,
) -> tuple[QualityMetricFailureType | None, list[str], list[str]]:
    if corpus.precision < manifest.thresholds.min_precision:
        return (
            QualityMetricFailureType.PRECISION_BELOW_THRESHOLD,
            ["corpus precision below threshold"],
            ["precision"],
        )
    if corpus.recall < manifest.thresholds.min_recall:
        return (
            QualityMetricFailureType.RECALL_BELOW_THRESHOLD,
            ["corpus recall below threshold"],
            ["recall"],
        )
    if corpus.f1 < manifest.thresholds.min_f1:
        return (
            QualityMetricFailureType.F1_BELOW_THRESHOLD,
            ["corpus F1 below threshold"],
            ["f1"],
        )
    if critical_precision < manifest.thresholds.min_critical_field_precision:
        return (
            QualityMetricFailureType.CRITICAL_PRECISION_BELOW_THRESHOLD,
            ["critical field precision below threshold"],
            ["critical_field_precision"],
        )
    return None, [], []


def _direct_failure_report(
    manifest: QualityMetricManifest,
    records: list[FieldConfusionRecord],
    failure: QualityMetricFailureType,
    missing: str,
) -> PrecisionRecallQualityReport:
    return PrecisionRecallQualityReport(
        id=f"precision-recall-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        field_confusion_refs=[item.id for item in records],
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"quality metrics blocked by scenario: {failure.value}"],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _record_report_event(
    manifest_id: str,
    report: PrecisionRecallQualityReport,
    store: ProductionPersistenceStore,
) -> PrecisionRecallQualityReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:quality-metrics-report",
        command_type="record_quality_metric_report",
        target_aggregate_type="PrecisionRecallQualityReport",
        target_aggregate_id=report.id,
        event_type="quality_metric_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:quality-metrics-benchmark",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{command_id}:dispatched",
    )
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id


def _count(records: Iterable[FieldConfusionRecord], klass: QualityMetricConfusionClass) -> int:
    return sum(1 for record in records if record.confusion_class == klass)


def _safe_rate(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
