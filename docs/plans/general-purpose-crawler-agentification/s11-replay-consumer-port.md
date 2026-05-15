# s11 — `ReplayConsumerPort` + deterministic fixture adapter

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 7 findings (port shape underspec, deps not listed, validator coverage incomplete, ReplayLookupMissError already exists with different semantics, STATUS row missing). | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | README s11 row stale relative to scope. | v3. |
| 3 | 2026-05-15 | REJECTED | ACs not mechanically specified. | v4. |
| 4 | 2026-05-15 | REJECTED | Rollback text inaccurate. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | Dependencies inaccurate and underdeclared (s6 clock_trace + s2/s2.1 dependencies omitted). Iter cap reached. | 7 reservations: (R1) ReplayLookupMissError reused needs backward-compat extension OR rename to ReplayConsumerLookupMissError to avoid collision with provider-specific error; (R2) Dependencies must list s6 (clock_trace producer) + s2.1 (raw_response_ref provenance) explicitly; (R3) ACs all inlined with concrete shell; (R4) validator coverage extended to blank dict-keys, blank fetch_outcome_refs values, missing-required-fields, extra-field rejection; (R5) UTC-only invariant for clock_trace strings needs explicit validator (not just "ISO 8601"); (R6) topic README s11 row added; (R7) Rollback text accurate to actual files added. |

Codex plan-review ≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5
per established pattern.

## Why

- **Capability 4 first slice.** Goal-doc capability 4
  (deterministic replay) needs a port that the runner consults
  before any non-deterministic source (clock, RNG,
  model-response, fetch-output). s11 ships the port + a
  deterministic fixture adapter that reads a recorded bundle
  and provides canned outputs. s12 wires the runner; s13 runs
  the live byte-identical re-execution test.

## Scope

### In

- **`ReplayBundle` contract**
  (`veracrawl.contracts.replay_bundle`):
  - `id: str`, `run_ref: Ref`, `recorded_at: datetime` (UTC),
    `clock_trace: list[str]` (ISO 8601 UTC),
    `model_response_refs: dict[str, Ref]` (request_id → raw_response_ref),
    `seed_refs: dict[str, int]` (RNG seed name → integer),
    `fetch_outcome_refs: dict[str, Ref]` (url+host_key → fetch_outcome_ref).
  - Validators on all sub-fields.

- **`ReplayConsumerPort`**
  (`veracrawl.ports.replay_consumer.ReplayConsumerPort`):
  - `load_bundle(bundle_ref: Ref) -> ReplayBundle`.
  - `next_utc(...) -> datetime` — consumes one entry from
    `clock_trace`.
  - `lookup_model_response(request_id: str) -> Ref` — returns
    `raw_response_ref` for the request id.
  - `next_seed(name: str) -> int` — RNG seed by name.
  - `lookup_fetch_outcome(url: str) -> Ref` — fetch_outcome_ref.

- **Fixture adapter**
  `veracrawl.adapters.replay.in_memory_replay_consumer.InMemoryReplayConsumer`:
  - Constructor: `bundle: ReplayBundle`.
  - Implements all 4 port methods deterministically.
  - `next_utc` cursors through `clock_trace`; raises
    `ReplayExhaustedError` on overrun.
  - `lookup_*` raise `ReplayLookupMissError` on miss.

- **Registry entry** for `ReplayBundle`.

- **Tests** (red list 22).

### Out

- Runner wiring (s12).
- Live re-execution test (s13).
- Bundle producer side — caller assembles `ReplayBundle` from
  `run_report.clock_trace`, `provider.raw_response_refs`, etc.
  (Producer wiring lands in s12.)

## Design

### Module map

```
src/veracrawl/contracts/replay_bundle.py                 # new — ≤ 110 LOC
src/veracrawl/contracts/registry.py                      # modify — ≤ 10 LOC
src/veracrawl/ports/replay_consumer.py                   # new — ≤  50 LOC
src/veracrawl/adapters/replay/in_memory_replay_consumer.py  # new — ≤ 100 LOC
src/veracrawl/contracts/errors.py                        # modify — ≤ 20 LOC (ReplayExhaustedError + ReplayLookupMissError)
tests/contract/test_replay_bundle_contracts.py           # new — ≤ 280 LOC
tests/contract/test_replay_bundle_contract_registry.py   # new — ≤  30 LOC
tests/contract/test_replay_consumer_import_boundaries.py # new — ≤  90 LOC
tests/unit/adapters/replay/test_in_memory_replay_consumer.py  # new — ≤ 280 LOC
```

Behavior LOC: 110 + 10 + 50 + 100 + 20 = **290 LOC**. Under ≤300 cap.

### Replay invariant

- The whole point of this slice is *the consumer side* of the
  replay loop. Producer side (recording) lands in s12 — runner
  populates a `ReplayBundle` from its run_report-equivalent
  state and persists it.
- s2.1's `ReplayingModelProviderV2` reservation 1 (deterministic
  request→raw_response_ref resolver) is satisfied by
  `ReplayConsumerPort.lookup_model_response(request_id)`. The
  s2.1 impl can delegate to this port.

## Dependencies

- Existing `Ref`, `VeraModel`, `TimestampedModel` (UTC-only
  pattern).
- Existing `contracts.errors.VeraCrawlError` /
  `FatalError` base classes.

**No prereq slice dependencies** — s11 is foundational; lands
without waiting on s7-s10.

## Test Strategy

### `tests/contract/test_replay_bundle_contracts.py`

1. `test_replay_bundle_rejects_blank_id`.
2. `test_replay_bundle_rejects_blank_run_ref`.
3. `test_replay_bundle_rejects_naive_recorded_at`.
4. `test_replay_bundle_rejects_aware_non_utc_recorded_at`.
5. `test_replay_bundle_rejects_non_iso_clock_trace_entry`.
6. `test_replay_bundle_rejects_empty_clock_trace`.
7. `test_replay_bundle_rejects_blank_model_response_ref_value`.
8. `test_replay_bundle_rejects_negative_seed_value`.
9. `test_replay_bundle_canonical_json_is_deterministic`.
10. `test_replay_bundle_extra_fields_forbidden`.

### `tests/contract/test_replay_bundle_contract_registry.py`

11. `test_registry_contains_replay_bundle`.
12. `test_registry_validate_ok`.

### `tests/contract/test_replay_consumer_import_boundaries.py`

13. `test_port_imports_allowlist`.
14. `test_in_memory_consumer_imports_allowlist`.

### `tests/unit/adapters/replay/test_in_memory_replay_consumer.py`

15. `test_next_utc_returns_canned_iso_datetimes_in_order`.
16. `test_next_utc_raises_replay_exhausted_on_overrun`.
17. `test_lookup_model_response_returns_raw_response_ref`.
18. `test_lookup_model_response_raises_replay_lookup_miss_on_unknown_request_id`.
19. `test_next_seed_returns_canned_integer_by_name`.
20. `test_next_seed_raises_on_unknown_name`.
21. `test_lookup_fetch_outcome_returns_ref`.
22. `test_lookup_fetch_outcome_raises_on_unknown_url`.

## Acceptance Criteria

1. **Pytest gate** —
   `pytest tests/contract/test_replay_bundle_contracts.py tests/contract/test_replay_bundle_contract_registry.py tests/contract/test_replay_consumer_import_boundaries.py tests/unit/adapters/replay/test_in_memory_replay_consumer.py -v`
   exits 0 with **22** collected, **22** passed.
2. **Registry** — one-line inline check.
3. **No runner wiring** —
   `grep -q ReplayConsumerPort src/veracrawl/external_crawl/runner.py && exit 1 || exit 0`.
4. **LOC budget shell** (≤ 300).
5. **Plan-review** grep ≥ 1.
6. **Task-review per commit** — s6 AC7 shape adapted.

## Rollback

s11 only adds files. Revert removes them.

## Open Questions

1. **Bundle persistence format**: JSON vs MessagePack. s11
   keeps in-memory only; s12 picks format.
2. **Multi-run bundle**: each run gets its own bundle. No
   cross-run replay in s11.
