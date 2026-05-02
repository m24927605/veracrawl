from __future__ import annotations

from veracrawl.control.runtime import create_runtime_command
from veracrawl.runtime_support.durable_store import DeterministicDurableStore


def test_duplicate_command_returns_original_result_without_duplicate_event_or_outbox() -> None:
    store = DeterministicDurableStore()
    command = create_runtime_command(
        command_id="cmd:dedupe",
        command_type="durable_commit_command",
        target_aggregate_type="DurableFixture",
        target_aggregate_id="fixture:dedupe",
        payload_ref="payload:dedupe",
    )
    first_record, first_result, first_outbox, first_duplicate = store.handle_command(
        command,
        run_ref="run:dedupe",
        objective_ref="objective:dedupe",
        plan_ref="plan:dedupe",
        event_type="durable_command_committed",
        output_refs=["artifact:dedupe"],
    )
    second_record, second_result, second_outbox, second_duplicate = store.handle_command(
        command.model_copy(update={"id": "cmd:dedupe:retry"}),
        run_ref="run:dedupe",
        objective_ref="objective:dedupe",
        plan_ref="plan:dedupe",
        event_type="durable_command_committed",
        output_refs=["artifact:dedupe"],
    )
    assert first_duplicate is False
    assert second_duplicate is True
    assert second_record.duplicate_of_ref == first_record.id
    assert second_result.id == first_result.id
    assert second_outbox.id == first_outbox.id
    assert len(store.stream_events("run:dedupe")) == 1
    assert len(store.list_outbox("run:dedupe")) == 1
