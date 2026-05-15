# s16 — `WorkerLeasePort` + queue-consumer loop (fixture mode)

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | red list under-spec; WorkOutcome + BudgetGate undefined; rollback contradicts module map. | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | Red list under-spec. | v3. |
| 3 | 2026-05-15 | REJECTED | Rollback contradicts module map. | v4. |
| 4 | 2026-05-15 | REJECTED | ACs + rollback not mechanically verifiable. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | Cross-slice STATUS + rollback inconsistent. Iter cap reached. | 6 reservations: (R1) `WorkOutcome` + `BudgetGate` defined as new contracts in s16; (R2) Rollback text aligned with actual files added; (R3) red list expanded with named tests for each Pydantic invariant; (R4) ACs inlined; (R5) topic STATUS s16 row added; (R6) confirm/add AIMD primitive at impl-time. |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 6 first slice.** Multi-process scale: a port
  for leased work consumption honoring AIMD + budget gates.
  s16 ships the port + a deterministic single-process fixture
  adapter; s17 ships a real multi-process worker pool.

## Scope

### In

- **`WorkerLease` contract** (`veracrawl.contracts.worker_lease`):
  `id: str`, `lease_ref: Ref`, `work_item_ref: Ref`,
  `worker_id: str`, `acquired_at: datetime` (UTC),
  `expires_at: datetime` (UTC), `aimd_state_ref: Ref`,
  `budget_ref: Ref`.
- **`WorkerLeasePort`**: `acquire(*, worker_id, budget_ref,
  utc_clock) -> WorkerLease | None`; `renew(lease) -> WorkerLease`;
  `release(lease, outcome: WorkOutcome) -> None`.
- **`InMemoryWorkerLeaseAdapter`** fixture impl:
  single-process queue + AIMD state machine; honors a
  `BudgetGate` callable.
- **Tests** (red list 15).

### Out

- Real multi-process queue (s17).
- Cross-host lease coordination.

## Design

### Module map

```
src/veracrawl/contracts/worker_lease.py                   # new — ≤  90 LOC
src/veracrawl/contracts/registry.py                       # modify — ≤  10 LOC
src/veracrawl/ports/worker_lease.py                       # new — ≤  50 LOC
src/veracrawl/adapters/work_queue/in_memory_worker_lease.py  # new — ≤ 140 LOC
tests/contract/test_worker_lease_contracts.py             # new — ≤ 240 LOC
tests/contract/test_worker_lease_registry.py              # new — ≤  30 LOC
tests/unit/adapters/work_queue/test_in_memory_worker_lease.py  # new — ≤ 280 LOC
tests/contract/test_worker_lease_import_boundaries.py     # new — ≤  80 LOC
```

Behavior LOC: 90 + 10 + 50 + 140 = **290 LOC**. Under ≤300.

### Replay invariant

- Lease ids derived deterministically from `(worker_id,
  work_item_ref, acquired_at)`. No clock-derived random
  components.
- `acquire/renew/release` are pure given (state, args).

## Dependencies

- Existing `Ref`, `VeraModel`, `TimestampedModel`.
- AIMD state machine — existing in repo? Confirm at impl.

## Test Strategy

### `tests/contract/test_worker_lease_contracts.py`

1-7. Validator coverage: blank ids/refs, naive/aware-non-UTC
datetimes, expires_at ≤ acquired_at rejection,
extra-field forbidden.

### `tests/contract/test_worker_lease_registry.py`

8. `test_registry_contains_worker_lease`.
9. `test_registry_validate_ok`.

### `tests/unit/adapters/work_queue/test_in_memory_worker_lease.py`

10. `test_acquire_returns_none_when_queue_empty`.
11. `test_acquire_returns_lease_with_correct_worker_id`.
12. `test_renew_extends_expires_at`.
13. `test_release_with_success_updates_aimd_state_increase`.
14. `test_release_with_failure_updates_aimd_state_multiplicative_decrease`.

### `tests/contract/test_worker_lease_import_boundaries.py`

15. `test_adapter_imports_allowlist`.

## Acceptance Criteria

1. Pytest gate: 15 collected, 15 passed.
2. Registry inline check.
3. No runner wiring: `grep -q WorkerLease src/veracrawl/external_crawl/runner.py && exit 1 || exit 0`.
4. LOC budget ≤ 300.
5. Plan-review grep ≥ 1.
6. Task-review per commit (s6 AC7 shape).

## Rollback

s16 adds new files only.

## Open Questions

1. **AIMD reuse**: confirm existing AIMD state machine module
   at impl; if absent, add deterministic AIMD primitive in
   s16 scope (~40 LOC).
2. **Lease expiry policy**: configurable on adapter ctor;
   default 60s.
