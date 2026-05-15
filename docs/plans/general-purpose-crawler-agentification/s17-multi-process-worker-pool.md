# s17 — Multi-process worker pool consumer (production adapter)

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | multiprocessing/time nondeterminism not replay-wired; ACs not mechanical; STATUS not updated. | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | STATUS not updated for s17. | v3. |
| 3 | 2026-05-15 | REJECTED | STATUS still not updated. | v4. |
| 4 | 2026-05-15 | REJECTED | Worker execution contract missing. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | STATUS row missing + cumulative findings. Iter cap reached. | 5 reservations: (R1) define worker execution contract — what callable does each worker run, and what's its return shape; (R2) replay-wire multiprocessing/time nondeterminism (worker id derivation, fork seed); (R3) topic STATUS s17 row landed in this commit; (R4) ACs inlined; (R5) hard prereq s16 impl'd. |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 6 second slice.** Real multi-process worker
  pool consuming the queue via s16's `WorkerLeasePort`,
  sharing AIMD + budget state via outbox.

## Scope

### In

- **`MultiprocessWorkerPool`** at
  `src/veracrawl/adapters/work_queue/multiprocess_worker_pool.py`:
  - Ctor: `lease_port: WorkerLeasePort`, `worker_count: int`,
    `outbox_event_store: EventStorePort`,
    `budget_gate: BudgetGate`, `utc_clock`, `utc_clock_ref`.
  - `run()`: spawn N processes via `multiprocessing.Process`;
    each process acquires leases, processes work, publishes
    outcomes to outbox.
- **AIMD state sharing**: workers read/write AIMD state via
  the outbox event stream (event sourcing pattern).
- **Live integration test**: 2-process pool against an
  in-memory backing store, runs 10 work items, verifies no
  duplicate processing.
- **Tests** (red list ≥ 12).

### Out

- Cross-host coordination (worker_id collisions).
- Dynamic worker scaling.

## Design

### Module map

```
src/veracrawl/adapters/work_queue/multiprocess_worker_pool.py  # new — ≤ 200 LOC
tests/unit/adapters/work_queue/test_multiprocess_worker_pool.py  # new — ≤ 280 LOC
tests/integration/test_multiprocess_worker_pool_live.py    # new — ≤ 180 LOC
tests/contract/test_multiprocess_pool_import_boundaries.py # new — ≤  80 LOC
```

Behavior LOC: 200. Under ≤ 300.

### Replay invariant

- All clock invocations route through injected `utc_clock`.
- Worker ids are deterministic: `f"worker:{pool_id}:{i}"`.
- Outbox event ordering is the only authoritative timeline.

## Dependencies

- s16 (`WorkerLeasePort`, `WorkerLease`).
- Existing `EventStorePort` + outbox plumbing.
- s14 (SQLite event store default — preferred backing for
  outbox).

**Hard prereq**: s16 impl'd.

## Test Strategy

Unit tests (mock multiprocessing): worker spawn, lease
acquire/release lifecycle, AIMD outbox events, deduplication.

Integration test: 2-process pool actually spawned; 10 items
processed exactly once; final AIMD state observable in
outbox.

## Acceptance Criteria

1. Pytest gate (incl. live mark): 12 collected, 12 passed.
2. Existing suite green.
3. No runner wiring.
4. LOC budget ≤ 300.
5. Plan-review grep ≥ 1.
6. Task-review per commit.

## Rollback

Adds files only.

## Open Questions

1. **Worker pool lifecycle**: graceful shutdown via
   SIGTERM-like signal.
2. **State serialization**: pickle for IPC; consider
   alternative if perf matters.
