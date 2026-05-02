from __future__ import annotations

from veracrawl.contracts.durable import EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import CompletenessResult, OutboxStatus
from veracrawl.review_replay.durable import validate_durable_recovery


def _outbox(status: OutboxStatus = OutboxStatus.DISPATCHED) -> OutboxRecord:
    kwargs = {
        "id": "outbox:1",
        "run_ref": "run:1",
        "command_result_ref": "command-result:1",
        "event_ref": "event:1",
        "dispatch_topic": "topic:test",
        "payload_ref": "payload:1",
        "idempotency_key": "outbox:1",
        "status": status,
    }
    if status == OutboxStatus.DISPATCHED:
        kwargs["dispatched_at_ref"] = "clock:dispatched"
    return OutboxRecord(**kwargs)


def _cursor(contiguous: bool = True) -> EventCursorRecord:
    return EventCursorRecord(
        id="event-cursor:1",
        run_ref="run:1",
        from_sequence=1,
        to_sequence=2,
        event_refs=["event:1", "event:2"] if contiguous else ["event:1"],
        contiguous=contiguous,
        missing_sequence_numbers=[] if contiguous else [2],
    )


def test_durable_recovery_passes_when_refs_are_complete() -> None:
    report = validate_durable_recovery(
        run_ref="run:1",
        command_record_refs=["durable-command:1"],
        event_cursors=[_cursor()],
        outbox_records=[_outbox()],
        artifact_refs=["artifact:1"],
        expected_artifact_refs=["artifact:1"],
        frontier_item_refs=["frontier:1"],
        lease_refs=["lease:1"],
    )
    assert report.completeness_result == CompletenessResult.PASS


def test_durable_recovery_fails_event_gap() -> None:
    report = validate_durable_recovery(
        run_ref="run:1",
        command_record_refs=["durable-command:1"],
        event_cursors=[_cursor(False)],
        outbox_records=[_outbox()],
        artifact_refs=["artifact:1"],
        expected_artifact_refs=["artifact:1"],
        frontier_item_refs=["frontier:1"],
        lease_refs=["lease:1"],
    )
    assert report.completeness_result == CompletenessResult.FAIL
    assert "event_cursor_gap" in report.missing_ref_fields


def test_durable_recovery_needs_review_for_pending_outbox() -> None:
    report = validate_durable_recovery(
        run_ref="run:1",
        command_record_refs=["durable-command:1"],
        event_cursors=[_cursor()],
        outbox_records=[_outbox(OutboxStatus.PENDING)],
        artifact_refs=["artifact:1"],
        expected_artifact_refs=["artifact:1"],
        frontier_item_refs=["frontier:1"],
        lease_refs=["lease:1"],
    )
    assert report.completeness_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "pending_outbox"


def test_durable_recovery_fails_missing_artifact() -> None:
    report = validate_durable_recovery(
        run_ref="run:1",
        command_record_refs=["durable-command:1"],
        event_cursors=[_cursor()],
        outbox_records=[_outbox()],
        artifact_refs=[],
        expected_artifact_refs=["artifact:1"],
        frontier_item_refs=["frontier:1"],
        lease_refs=["lease:1"],
    )
    assert report.completeness_result == CompletenessResult.FAIL
    assert report.operator_status == "missing_artifact"
