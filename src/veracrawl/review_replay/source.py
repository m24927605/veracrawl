"""Source acquisition replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.source_runtime import SourceAcquisitionReport


def missing_source_replay_refs(report: SourceAcquisitionReport) -> list[str]:
    required = {
        "source_adapter_result_ref": report.source_adapter_result_ref,
        "fetch_attempt_refs": report.fetch_attempt_refs,
        "fetch_result_refs": report.fetch_result_refs,
        "artifact_refs": report.artifact_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "recovery_report_refs": report.recovery_report_refs,
        "frontier_item_ref": report.frontier_item_ref,
        "lease_ref": report.lease_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def source_replay_passes(report: SourceAcquisitionReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not missing_source_replay_refs(
        report
    )
