# s14 — SQLite `EventStorePort` adapter as default

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1    | TBD        | TBD     | TBD      | TBD        |
| 2    | TBD        | TBD     | TBD      | TBD        |
| 3    | TBD        | TBD     | TBD      | TBD        |
| 4    | TBD        | TBD     | TBD      | TBD        |
| 5    | TBD        | TBD     | TBD      | TBD        |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 5 first slice.** Production backend: SQLite
  `EventStorePort` adapter replaces `InMemoryEventStore` as
  the default in `control/runtime.py`. The adapter already
  exists in the repo (per goal-doc note); s14 is the wiring +
  migration + regression tests.

## Scope

### In

- **Confirm SQLite EventStorePort adapter exists.** Survey:
  `src/veracrawl/adapters/event_stores/sqlite_event_store.py`
  or similar. If absent, draft impl is in s14 scope (≤ 180
  LOC). If present, s14 is wiring-only.

- **`control/runtime.py` default change**: replace
  `InMemoryEventStore` default factory with SQLite-backed.
  Caller can still inject InMemory explicitly for tests.

- **Migration test**: existing tests that didn't inject an
  event store must continue passing.

- **Tests** (red list ≥ 12):
  - SQLite adapter unit tests (CRUD, dedup, ordering).
  - Runtime default test (factory yields SQLite by default).
  - Regression: existing event-bound tests still pass.

### Out

- New event types / schema migrations.
- Cross-process event store sharing (single-process only).

## Design

### Module map (assumes SQLite adapter exists)

```
src/veracrawl/control/runtime.py                         # modify — ≤  30 LOC (default factory swap)
tests/unit/control/test_runtime_default_event_store.py   # new — ≤ 100 LOC
tests/unit/adapters/event_stores/test_sqlite_event_store_regression.py  # new — ≤ 220 LOC (if not already covered)
```

If SQLite adapter doesn't exist:

```
src/veracrawl/adapters/event_stores/sqlite_event_store.py  # new — ≤ 180 LOC
src/veracrawl/control/runtime.py                         # modify — ≤  30 LOC
tests/unit/adapters/event_stores/test_sqlite_event_store.py  # new — ≤ 280 LOC
tests/unit/control/test_runtime_default_event_store.py   # new — ≤ 100 LOC
```

Behavior LOC: 180 + 30 = **210 LOC** (or 30 if wiring-only).
Under ≤ 300 cap either way.

### Replay invariant

- SQLite adapter must be deterministic per (event sequence) →
  (stream output). No clock or RNG in event store.
- Existing replay tests against InMemoryEventStore must work
  identically against the SQLite default after migration.

## Dependencies

- Existing `EventStorePort` (`veracrawl.ports.stores`).
- Existing `InMemoryEventStore` (whatever module).
- Existing `control/runtime.py` composition root.

**Prereq**: none specific — independent slice. Can land
without waiting on capability 1-4 slices.

## Test Strategy

### `tests/unit/adapters/event_stores/test_sqlite_event_store.py` (if new)

1. `test_sqlite_store_appends_event_and_streams_in_order`.
2. `test_sqlite_store_deduplicates_by_event_id`.
3. `test_sqlite_store_persists_across_reconnect`.
4. `test_sqlite_store_run_id_isolation` — events for run A
   not surfaced by stream(run_id="B").
5. `test_sqlite_store_handles_empty_stream`.
6. `test_sqlite_store_extra_field_validation`.

### `tests/unit/control/test_runtime_default_event_store.py`

7. `test_default_runtime_uses_sqlite_event_store`.
8. `test_caller_can_override_with_in_memory_event_store`.
9. `test_default_event_store_path_configurable_via_env`.

### `tests/unit/adapters/event_stores/test_sqlite_event_store_regression.py`

10. `test_runner_run_completes_with_sqlite_default`.
11. `test_event_stream_after_run_matches_in_memory_baseline` —
    side-by-side comparison.
12. `test_outbox_processing_with_sqlite_default`.

## Acceptance Criteria

1. Pytest gate: 12 collected, 12 passed.
2. Existing test suite green: `pytest tests/ -q` exits 0.
3. LOC budget shell ≤ 300.
4. Plan-review grep ≥ 1.
5. Task-review per commit — s6 AC7 shape.

## Rollback

s14 only changes the default factory in `control/runtime.py`.
Revert restores InMemoryEventStore default; existing tests
keep working (they didn't depend on persistence).

## Open Questions

1. **DB file location**: configurable via env
   (`VERACRAWL_EVENT_STORE_PATH`); default
   `~/.veracrawl/events.db`.
2. **Concurrent access**: SQLite WAL mode for safety. Out of
   strict scope but trivial setting on the adapter.
