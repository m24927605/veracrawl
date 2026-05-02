from __future__ import annotations

from pathlib import Path

from veracrawl.adapters.persistence.sqlite import SQLitePersistenceAdapter, sqlite_adapter_spec
from veracrawl.contracts.enums import (
    PersistenceAdapterKind,
    PersistenceMigrationStatus,
    PersistentQueueOperation,
)
from veracrawl.contracts.persistence import PersistenceMigrationRecord
from veracrawl.persistence.adapter_conformance import run_sqlite_adapter_conformance


def test_sqlite_adapter_spec_declares_all_target_capabilities() -> None:
    spec = sqlite_adapter_spec("unit", ["policy:unit:persistence-adapter"])
    assert spec.adapter_kind == PersistenceAdapterKind.SQLITE
    assert spec.transaction_supported is True
    assert spec.idempotency_supported is True
    assert spec.lease_supported is True


def test_sqlite_adapter_reopens_and_preserves_migration_records(tmp_path: Path) -> None:
    adapter = SQLitePersistenceAdapter(tmp_path / "adapter.db")
    migration = PersistenceMigrationRecord(
        id="persistence-migration:unit:001",
        adapter_ref="persistence-adapter:unit:sqlite",
        migration_name="001_unit",
        from_version="0",
        to_version="1",
        status=PersistenceMigrationStatus.APPLIED,
        applied_at_ref="clock:unit:migration",
        rollback_plan_ref="rollback-plan:unit:001",
        validation_event_cursor_ref="event-cursor:unit",
    )
    adapter.save_migration_record(migration)
    reopened = adapter.reopen()
    assert [record.id for record in reopened.list_migration_records()] == [migration.id]


def test_sqlite_queue_recovery_records_nack_and_dead_letter(tmp_path: Path) -> None:
    fixture_id = "sqlite-queue-recovery-success"
    policy_refs = [f"policy:{fixture_id}:persistence-adapter"]
    result = run_sqlite_adapter_conformance(
        fixture_id=fixture_id,
        scenario=fixture_id,
        store=SQLitePersistenceAdapter(tmp_path / "adapter.db"),
        adapter_spec=sqlite_adapter_spec(fixture_id, policy_refs),
        policy_decision_refs=policy_refs,
    )
    operations = {operation.operation for operation in result.queue_operations}
    assert PersistentQueueOperation.NACK in operations
    assert PersistentQueueOperation.DEAD_LETTER in operations
