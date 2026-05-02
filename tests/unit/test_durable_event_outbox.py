from __future__ import annotations

import pytest

from veracrawl.contracts.enums import OutboxStatus
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.control.runtime import create_runtime_command
from veracrawl.runtime_support.durable_store import DeterministicDurableStore


def _event(sequence: int) -> CrawlRunEvent:
    return CrawlRunEvent(
        id=f"event:gap:{sequence}",
        run_id="run:gap",
        objective_id="objective:gap",
        crawl_plan_id="plan:gap",
        sequence=sequence,
        event_type="durable_command_committed",
        event_type_spec_id="event-type:durable_command_committed",
        payload_ref=f"payload:{sequence}",
        causation_id="cmd:gap",
        correlation_id="corr:gap",
        trace_id=f"trace:{sequence}",
        idempotency_key=f"event:{sequence}",
    )


def test_durable_event_append_requires_contiguous_sequences() -> None:
    store = DeterministicDurableStore()
    store.append_event(_event(1))
    with pytest.raises(ValueError):
        store.append_event(_event(3))


def test_event_cursor_reports_forced_fixture_gap() -> None:
    store = DeterministicDurableStore()
    store.force_append_event_for_fixture(_event(1))
    store.force_append_event_for_fixture(_event(3))
    cursor = store.build_event_cursor("run:gap")
    assert cursor.contiguous is False
    assert cursor.missing_sequence_numbers == [2]


def test_outbox_dispatch_is_idempotent_and_pending_visible() -> None:
    store = DeterministicDurableStore()
    command = create_runtime_command(
        command_id="cmd:outbox",
        command_type="durable_commit_command",
        target_aggregate_type="DurableFixture",
        target_aggregate_id="fixture:outbox",
    )
    _, _, outbox, _ = store.handle_command(
        command,
        run_ref="run:outbox",
        objective_ref="objective:outbox",
        plan_ref="plan:outbox",
        event_type="durable_command_committed",
        output_refs=["artifact:outbox"],
    )
    assert [record.id for record in store.list_pending_outbox("run:outbox")] == [outbox.id]
    dispatched = store.mark_outbox_dispatched(outbox.id, dispatched_at_ref="clock:outbox")
    dispatched_again = store.mark_outbox_dispatched(outbox.id, dispatched_at_ref="clock:again")
    assert dispatched.status == OutboxStatus.DISPATCHED
    assert dispatched_again.attempt_count == dispatched.attempt_count
    assert store.list_pending_outbox("run:outbox") == []
