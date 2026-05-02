"""Normalize/extract replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.processing import NormalizeExtractReport


def missing_process_replay_refs(report: NormalizeExtractReport) -> list[str]:
    required = {
        "network_acquisition_report_ref": report.network_acquisition_report_ref,
        "normalized_document_ref": report.normalized_document_ref,
        "normalization_manifest_ref": report.normalization_manifest_ref,
        "anchor_map_ref": report.anchor_map_ref,
        "page_type_classification_ref": report.page_type_classification_ref,
        "site_model_ref": report.site_model_ref,
        "extraction_strategy_ref": report.extraction_strategy_ref,
        "extraction_candidate_ref": report.extraction_candidate_ref,
        "artifact_refs": report.artifact_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def process_replay_passes(report: NormalizeExtractReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_process_replay_refs(report)
    )
