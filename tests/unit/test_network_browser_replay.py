from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.network import NetworkAcquisitionReport
from veracrawl.review_replay.network_browser import (
    missing_network_browser_replay_refs,
    network_browser_replay_passes,
)


def _passing_report() -> NetworkAcquisitionReport:
    return NetworkAcquisitionReport(
        id="network-acquisition:ok",
        run_ref="run:ok",
        network_request_ref="network-request:ok",
        network_response_ref="network-response:ok",
        source_acquisition_report_ref="source-acquisition:ok",
        artifact_refs=["artifact:raw"],
        policy_decision_refs=["policy:network"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["cursor:ok"],
        outbox_refs=["outbox:ok"],
        recovery_report_refs=["recovery:ok"],
        operator_status="network_acquired",
        completion_result=CompletenessResult.PASS,
    )


def test_network_browser_replay_passes_with_all_refs() -> None:
    report = _passing_report()
    assert missing_network_browser_replay_refs(report) == []
    assert network_browser_replay_passes(report)


def test_network_browser_replay_reports_missing_refs() -> None:
    report = _passing_report().model_copy(update={"artifact_refs": [], "missing_ref_fields": []})
    assert "artifact_refs" in missing_network_browser_replay_refs(report)
    assert not network_browser_replay_passes(report)
