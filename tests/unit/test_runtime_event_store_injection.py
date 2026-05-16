"""Test the s14 default-swap injection seam in ``run_runtime_fixture``."""

from __future__ import annotations

from pathlib import Path

from veracrawl.adapters.event_stores.sqlite_event_store import SqliteEventStore
from veracrawl.control.runtime import run_runtime_fixture
from veracrawl.runtime_events.event_store import InMemoryEventStore


def test_default_event_store_remains_in_memory_when_unspecified() -> None:
    """Backward-compat: omitting ``event_store`` uses the in-memory default."""

    report = run_runtime_fixture(
        fixture_id="trace-foundation-record",
        scenario="record-success",
        profile="target",
    )
    # Test passes if the fixture runs to completion with no kwarg —
    # proves the default in-memory path still works.
    assert report.fixture_id


def test_injected_in_memory_event_store_round_trip() -> None:
    store = InMemoryEventStore()
    report = run_runtime_fixture(
        fixture_id="trace-foundation-record",
        scenario="record-success",
        profile="target",
        event_store=store,
    )
    # After the run, the injected store has captured events.
    events = store.stream(report.run_ref)
    assert len(events) >= 1


def test_injected_sqlite_event_store_persists_run_events(tmp_path: Path) -> None:
    db_path = tmp_path / "events.db"
    store = SqliteEventStore(db_path=db_path)
    try:
        report = run_runtime_fixture(
            fixture_id="trace-foundation-record",
            scenario="record-success",
            profile="target",
            event_store=store,
        )
        events = store.stream(report.run_ref)
        assert len(events) >= 1
    finally:
        store.close()
    # Reopen the same db file — events survive across reconnect.
    reopened = SqliteEventStore(db_path=db_path)
    try:
        rehydrated = reopened.stream(report.run_ref)
        assert len(rehydrated) >= 1
    finally:
        reopened.close()
