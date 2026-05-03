"""Precision/recall quality metric replay helpers."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.quality_metrics import (
    FieldConfusionRecord,
    PrecisionRecallQualityReport,
)


def missing_confusion_record_replay_refs(record: FieldConfusionRecord) -> list[str]:
    required = {
        "evidence_packet_refs": record.evidence_packet_refs,
        "publication_gate_refs": record.publication_gate_refs,
        "artifact_refs": record.artifact_refs,
        "content_hash_refs": record.content_hash_refs,
        "policy_decision_refs": record.policy_decision_refs,
        "command_record_refs": record.command_record_refs,
        "event_cursor_refs": record.event_cursor_refs,
        "outbox_refs": record.outbox_refs,
        "replay_bundle_ref": record.replay_bundle_ref,
    }
    return sorted(name for name, value in required.items() if not value)


def confusion_record_replay_passes(record: FieldConfusionRecord) -> bool:
    return not missing_confusion_record_replay_refs(record)


def missing_quality_metric_report_replay_refs(
    report: PrecisionRecallQualityReport,
) -> list[str]:
    required = {
        "corpus_metric_ref": report.corpus_metric_ref,
        "slice_metric_refs": report.slice_metric_refs,
        "field_confusion_refs": report.field_confusion_refs,
        "evidence_packet_refs": report.evidence_packet_refs,
        "publication_gate_refs": report.publication_gate_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def quality_metric_report_replay_passes(report: PrecisionRecallQualityReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_quality_metric_report_replay_refs(report)
    )
