"""Durable replay recovery validation."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import CompletenessResult, OutboxStatus
from veracrawl.contracts.recovery import DurableReplayRecoveryReport
from veracrawl.contracts.scheduler import SchedulerRecoveryReport


def validate_durable_recovery(
    *,
    run_ref: Ref,
    command_record_refs: list[Ref],
    event_cursors: list[EventCursorRecord],
    outbox_records: list[OutboxRecord],
    artifact_refs: list[Ref],
    expected_artifact_refs: list[Ref],
    frontier_item_refs: list[Ref],
    lease_refs: list[Ref],
    scheduler_report: SchedulerRecoveryReport | None = None,
    report_id: str | None = None,
) -> DurableReplayRecoveryReport:
    missing: list[str] = []
    gaps: list[Ref] = []
    if not command_record_refs:
        missing.append("command_record_refs")
    if not event_cursors:
        missing.append("event_cursor_refs")
    for cursor in event_cursors:
        if not cursor.contiguous:
            gaps.append(cursor.id)
            missing.append("event_cursor_gap")
    if not outbox_records:
        missing.append("outbox_refs")
    pending_outbox = [
        record.id for record in outbox_records if record.status == OutboxStatus.PENDING
    ]
    if pending_outbox:
        missing.append("pending_outbox_refs")
    missing_artifacts = [ref for ref in expected_artifact_refs if ref not in set(artifact_refs)]
    if missing_artifacts:
        missing.append("artifact_refs")
        gaps.extend(missing_artifacts)
    if not frontier_item_refs:
        missing.append("frontier_item_refs")
    if not lease_refs:
        missing.append("lease_refs")
    if (
        scheduler_report is not None
        and scheduler_report.completeness_result != CompletenessResult.PASS
    ):
        gaps.append(scheduler_report.id)
        if scheduler_report.operator_status not in missing:
            missing.append(scheduler_report.operator_status)

    if any(item in missing for item in ["event_cursor_gap", "artifact_refs", "invalid_lease"]):
        result = CompletenessResult.FAIL
    elif (
        scheduler_report is not None
        and scheduler_report.completeness_result == CompletenessResult.FAIL
    ):
        result = CompletenessResult.FAIL
    elif missing or gaps:
        result = CompletenessResult.NEEDS_REVIEW
    else:
        result = CompletenessResult.PASS

    if result == CompletenessResult.PASS:
        operator_status = "durable_recovered"
    elif "pending_outbox_refs" in missing:
        operator_status = "pending_outbox"
    elif "artifact_refs" in missing:
        operator_status = "missing_artifact"
    elif "event_cursor_gap" in missing:
        operator_status = "event_gap"
    elif scheduler_report is not None:
        operator_status = scheduler_report.operator_status
    else:
        operator_status = "durable_recovery_incomplete"

    return DurableReplayRecoveryReport(
        id=report_id or f"durable-recovery:{run_ref}",
        run_ref=run_ref,
        command_record_refs=command_record_refs,
        event_cursor_refs=[cursor.id for cursor in event_cursors],
        outbox_refs=[record.id for record in outbox_records],
        artifact_refs=artifact_refs,
        frontier_item_refs=frontier_item_refs,
        lease_refs=lease_refs,
        scheduler_recovery_report_refs=[scheduler_report.id] if scheduler_report else [],
        missing_ref_fields=sorted(set(missing)),
        gap_report_refs=gaps,
        operator_status=operator_status,
        completeness_result=result,
    )
