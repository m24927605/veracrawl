"""Export replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.export import ExportReconciliationReport


def missing_export_replay_refs(report: ExportReconciliationReport) -> list[str]:
    required = {
        "export_target_spec_refs": report.export_target_spec_refs,
        "export_job_refs": report.export_job_refs,
        "export_attempt_refs": report.export_attempt_refs,
        "delivery_receipt_refs": report.delivery_receipt_refs,
        "destination_object_mapping_refs": report.destination_object_mapping_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def export_replay_passes(report: ExportReconciliationReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_export_replay_refs(report)
    )
