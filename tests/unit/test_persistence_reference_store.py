from __future__ import annotations

from pathlib import Path

from veracrawl.control.runtime import create_runtime_command
from veracrawl.persistence.runtime import run_persistence_queue_runtime
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def test_reference_store_dedupes_after_reopen(tmp_path: Path) -> None:
    store = ReferencePersistenceStore(tmp_path)
    command = create_runtime_command(
        command_id="cmd:persistence-dedupe",
        command_type="durable_commit_command",
        target_aggregate_type="PersistenceFixture",
        target_aggregate_id="fixture:dedupe",
        payload_ref="payload:dedupe",
    )
    _, _, _, first_idempotency, first_duplicate = store.handle_command_once(
        command,
        run_ref="run:dedupe",
        objective_ref="objective:dedupe",
        plan_ref="plan:dedupe",
        event_type="persistence_runtime_reported",
        output_refs=["artifact:dedupe"],
    )
    reopened = store.reopen()
    _, _, _, duplicate_idempotency, second_duplicate = reopened.handle_command_once(
        command.model_copy(update={"id": "cmd:persistence-dedupe:retry"}),
        run_ref="run:dedupe",
        objective_ref="objective:dedupe",
        plan_ref="plan:dedupe",
        event_type="persistence_runtime_reported",
        output_refs=["artifact:dedupe"],
    )
    assert first_duplicate is False
    assert second_duplicate is True
    assert duplicate_idempotency.duplicate_of_ref == first_idempotency.id
    assert len(reopened.stream_events("run:dedupe")) == 1
    assert len(reopened.list_outbox("run:dedupe")) == 1


def test_reference_store_persists_queue_operations(tmp_path: Path) -> None:
    result = run_persistence_queue_runtime(
        fixture_id="unit-queue-recovery",
        scenario="queue-lease-recovery-success",
        root=tmp_path,
        policy_decision_refs=["policy:unit:persistence"],
    )
    reopened = ReferencePersistenceStore(tmp_path)
    operations = reopened.list_queue_operations()
    assert result.report.completion_result.value == "pass"
    assert len(operations) >= 5
    assert any(operation.dead_letter_ref for operation in operations)
