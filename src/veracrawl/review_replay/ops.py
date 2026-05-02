"""Ops console replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.ops import OpsConsoleReport


def missing_ops_replay_refs(report: OpsConsoleReport) -> list[str]:
    required = {
        "review_item_refs": report.review_item_refs,
        "replay_audit_view_refs": report.replay_audit_view_refs,
        "quality_report_refs": report.quality_report_refs,
        "dashboard_snapshot_ref": report.dashboard_snapshot_ref,
        "dr_restore_report_refs": report.dr_restore_report_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def ops_console_replay_passes(report: OpsConsoleReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not missing_ops_replay_refs(
        report
    )
