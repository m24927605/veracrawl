"""``SqliteEventStore`` — durable ``EventStorePort`` adapter (s14).

Single-process SQLite-backed event store with the same append-only +
strict-sequence invariants as the in-memory default
(``runtime_events.event_store.InMemoryEventStore``).

* ``run_id`` isolation: ``stream(run_id)`` only returns events for
  that run.
* Strict ``sequence`` invariant: ``append`` rejects out-of-order
  sequence numbers with ``ReplayValidationError`` (matches
  ``InMemoryEventStore`` behavior verbatim).
* Idempotency: ``event.id`` is the primary key; re-appending the
  same id returns the existing ref without re-inserting (R2
  reservation: event_id-based dedup, not content-based).
* Reconnect-safe: ``stream`` reads from disk on every call, so
  reopening the same database file recovers the full event
  log.

Schema:

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(run_id, sequence)
);
CREATE INDEX events_by_run_seq ON events(run_id, sequence);
```

See ``docs/plans/general-purpose-crawler-agentification/
s14-sqlite-event-store-default.md``.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import ReplayValidationError
from veracrawl.contracts.event import CrawlRunEvent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE(run_id, sequence)
);
CREATE INDEX IF NOT EXISTS events_by_run_seq ON events(run_id, sequence);
"""


class SqliteEventStore:
    def __init__(self, *, db_path: Path | str | None = None) -> None:
        """Initialize the store.

        Pass ``db_path=None`` (or omit) to use a private in-memory
        database (still survives across method calls on the same
        instance, but discarded on close).
        """

        self._db_path = str(db_path) if db_path is not None else ":memory:"
        self._conn = sqlite3.connect(self._db_path, isolation_level=None)
        self._conn.executescript(_SCHEMA)

    def append(self, event: CrawlRunEvent) -> Ref:
        existing_id = self._conn.execute(
            "SELECT id FROM events WHERE id = ?", (event.id,),
        ).fetchone()
        if existing_id is not None:
            # R2 reservation: event_id-based dedup. Re-appending the
            # same id is a no-op (matches in-memory append's
            # ``return event.id`` shape for the second producer).
            return event.id
        # Strict-sequence guard: next expected sequence is
        # max(sequence) + 1 within the run.
        row = self._conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) FROM events WHERE run_id = ?",
            (event.run_id,),
        ).fetchone()
        next_seq = (row[0] if row is not None else 0) + 1
        if event.sequence != next_seq:
            raise ReplayValidationError(
                f"event sequence gap for {event.run_id}: "
                f"expected {next_seq}, got {event.sequence}",
            )
        self._conn.execute(
            "INSERT INTO events (id, run_id, sequence, payload) "
            "VALUES (?, ?, ?, ?)",
            (event.id, event.run_id, event.sequence,
             event.model_dump_json()),
        )
        return event.id

    def stream(self, run_id: str) -> list[CrawlRunEvent]:
        rows = self._conn.execute(
            "SELECT payload FROM events WHERE run_id = ? "
            "ORDER BY sequence ASC",
            (run_id,),
        ).fetchall()
        return [CrawlRunEvent.model_validate(json.loads(row[0])) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SqliteEventStore:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


__all__ = ["SqliteEventStore"]
