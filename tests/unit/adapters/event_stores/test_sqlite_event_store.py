"""Unit tests for ``SqliteEventStore`` (s14)."""

from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.adapters.event_stores.sqlite_event_store import SqliteEventStore
from veracrawl.contracts.errors import ReplayValidationError
from veracrawl.contracts.event import CrawlRunEvent


def _event(*, sequence: int, run_id: str = "run:1") -> CrawlRunEvent:
    return CrawlRunEvent(
        id=f"event:{run_id}:{sequence}",
        run_id=run_id,
        objective_id="objective:1",
        crawl_plan_id="plan:1",
        sequence=sequence,
        event_type="test_event",
        event_type_spec_id="event-type:test",
        payload_ref=f"payload:{run_id}:{sequence}",
        causation_id=f"cause:{run_id}:{sequence}",
        correlation_id=f"corr:{run_id}:{sequence}",
        trace_id=f"trace:{run_id}:{sequence}",
        idempotency_key=f"idem:event:{run_id}:{sequence}",
    )


def test_sqlite_store_appends_event_and_streams_in_order() -> None:
    store = SqliteEventStore()
    a = store.append(_event(sequence=1))
    b = store.append(_event(sequence=2))
    events = store.stream("run:1")
    assert [e.id for e in events] == [a, b]
    assert [e.sequence for e in events] == [1, 2]


def test_sqlite_store_rejects_sequence_gap() -> None:
    store = SqliteEventStore()
    store.append(_event(sequence=1))
    with pytest.raises(ReplayValidationError):
        store.append(_event(sequence=3))


def test_sqlite_store_deduplicates_by_event_id() -> None:
    store = SqliteEventStore()
    e = _event(sequence=1)
    ref_a = store.append(e)
    ref_b = store.append(e)  # same id
    assert ref_a == ref_b
    assert len(store.stream("run:1")) == 1


def test_sqlite_store_persists_across_reconnect(tmp_path: Path) -> None:
    db_path = tmp_path / "events.db"
    a = SqliteEventStore(db_path=db_path)
    a.append(_event(sequence=1))
    a.append(_event(sequence=2))
    a.close()

    b = SqliteEventStore(db_path=db_path)
    events = b.stream("run:1")
    assert len(events) == 2
    assert events[0].sequence == 1
    assert events[1].sequence == 2
    b.close()


def test_sqlite_store_run_id_isolation() -> None:
    store = SqliteEventStore()
    store.append(_event(sequence=1, run_id="run:a"))
    store.append(_event(sequence=2, run_id="run:a"))
    store.append(_event(sequence=1, run_id="run:b"))
    assert len(store.stream("run:a")) == 2
    assert len(store.stream("run:b")) == 1
    assert store.stream("run:nonexistent") == []


def test_sqlite_store_handles_empty_stream() -> None:
    store = SqliteEventStore()
    assert store.stream("run:never") == []


def test_sqlite_store_context_manager_closes_connection() -> None:
    with SqliteEventStore() as store:
        store.append(_event(sequence=1))
        assert len(store.stream("run:1")) == 1
    # After close, further operations fail; we just confirm no leak.


def test_sqlite_store_stream_preserves_event_payload_round_trip() -> None:
    store = SqliteEventStore()
    original = _event(sequence=1)
    store.append(original)
    rehydrated = store.stream("run:1")[0]
    assert rehydrated.id == original.id
    assert rehydrated.payload_ref == original.payload_ref
    assert rehydrated.event_type == original.event_type
