from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.durable import DurableCommandRecord, EventCursorRecord, OutboxRecord
from veracrawl.contracts.enums import (
    CompletenessResult,
    DurableCommandRecordStatus,
    FrontierItemStatus,
    OutboxStatus,
    QueueLeaseStatus,
)
from veracrawl.contracts.recovery import DurableReplayRecoveryReport
from veracrawl.contracts.scheduler import FrontierItem, QueueLease, SchedulerRecoveryReport


def test_durable_command_record_requires_refs_when_committed() -> None:
    with pytest.raises(ValidationError):
        DurableCommandRecord(
            id="durable-command:bad",
            command_ref="cmd:bad",
            command_type="durable_commit_command",
            target_aggregate_type="DurableFixture",
            target_aggregate_id="fixture:bad",
            idempotency_key="idem:bad",
            status=DurableCommandRecordStatus.COMMITTED,
        )


def test_outbox_and_event_cursor_validation() -> None:
    with pytest.raises(ValidationError):
        OutboxRecord(
            id="outbox:bad",
            run_ref="run:bad",
            command_result_ref="result:bad",
            event_ref="event:bad",
            dispatch_topic="topic:test",
            payload_ref="payload:bad",
            idempotency_key="outbox:bad",
            status=OutboxStatus.DISPATCHED,
        )
    with pytest.raises(ValidationError):
        EventCursorRecord(
            id="cursor:bad",
            run_ref="run:bad",
            from_sequence=1,
            to_sequence=2,
            event_refs=["event:1"],
            contiguous=True,
        )


def test_frontier_lease_and_recovery_contract_validation() -> None:
    with pytest.raises(ValidationError):
        FrontierItem(
            id="frontier:bad",
            run_ref="run:bad",
            source_ref="source:bad",
            priority=1,
            status=FrontierItemStatus.LEASED,
        )
    with pytest.raises(ValidationError):
        QueueLease(
            id="lease:bad",
            frontier_item_ref="frontier:bad",
            run_ref="run:bad",
            lease_token_ref="token:bad",
            holder_ref="worker:bad",
            status=QueueLeaseStatus.EXPIRED,
            expires_at_ref="clock:bad",
        )
    with pytest.raises(ValidationError):
        SchedulerRecoveryReport(
            id="scheduler-recovery:bad",
            run_ref="run:bad",
            operator_status="scheduler_recovered",
            completeness_result=CompletenessResult.PASS,
            expired_lease_refs=["lease:bad"],
        )


def test_durable_replay_recovery_requires_gap_details_for_non_pass() -> None:
    with pytest.raises(ValidationError):
        DurableReplayRecoveryReport(
            id="durable-recovery:bad",
            run_ref="run:bad",
            operator_status="event_gap",
            completeness_result=CompletenessResult.FAIL,
        )
