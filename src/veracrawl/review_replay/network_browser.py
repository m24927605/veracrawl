"""Network and browser acquisition replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.network import NetworkAcquisitionReport


def missing_network_browser_replay_refs(report: NetworkAcquisitionReport) -> list[str]:
    required = {
        "network_request_ref": report.network_request_ref,
        "source_acquisition_report_ref": report.source_acquisition_report_ref,
        "artifact_refs": report.artifact_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "recovery_report_refs": report.recovery_report_refs,
    }
    if not (report.network_response_ref or report.browser_step_ref):
        required["network_response_or_browser_step_ref"] = None
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def network_browser_replay_passes(report: NetworkAcquisitionReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_network_browser_replay_refs(report)
    )
