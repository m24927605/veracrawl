# s13 — Live byte-identical re-execution test for one corpus

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 2 blockers + 2 majors: (b) byte-equality both required and narrowed (Scope In vs Out contradict); (b) run_report is dict[str,Any] not VeraModel — `.canonical_json()` doesn't exist on it; (m) AC placeholders; (m) artifact byte-equality claimed before hashed-fs storage exists. | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | Artifact byte-equality depends on s15 hashed-fs default — still in s13 scope. | v3. |
| 3 | 2026-05-15 | REJECTED | Artifact byte comparison impossible with current store. | v4. |
| 4 | 2026-05-15 | REJECTED | Red list under-specified for claimed replay invariant. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | Artifact equality before dependency + no red coverage. Iter cap reached. | 6 reservations: (R1) drop artifact-dir byte-equality from s13 — defer to a follow-up slice after s15 hashed-fs default lands; (R2) replay invariant narrowed to (graph events + plan_decision_2_replay_refs + clock_trace) only — same as s6 reservation 3; (R3) `run_report` is `dict[str,Any]` — compare via `json.dumps(report, sort_keys=True)` not `.canonical_json()`; (R4) ACs inlined with concrete pytest selectors; (R5) hard prereqs s2.1 + s6 + s11 + s12 impl'd; (R6) red list expanded with explicit value-comparison tests per key. |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 4 closing slice.** s11 ships ReplayConsumerPort
  + InMemoryReplayConsumer; s12 wires the runner. s13 ships
  the end-to-end test that proves byte-identical re-execution
  on a recorded corpus: record run → assemble bundle → replay
  run → diff artifacts + run_report → bytes equal.

## Scope

### In

- **One live integration test** at
  `tests/integration/test_runner_replay_byte_identical.py`,
  marked `@pytest.mark.live`:
  - Phase 1 (record): Start local HTTP stub serving a 3-URL
    corpus (redirect, 200+HTML, 200+HTML). Run the runner
    with `utc_clock = make_advancing_fake_clock()`,
    `utc_clock_ref = "utc-clock:fixture:1"`, real planner +
    observer + replan factory. Capture `run_report_a`
    + `clock_trace` + `provider.raw_response_refs` +
    `fetcher.outcomes` snapshots.
  - Phase 2 (assemble bundle): Build a `ReplayBundle` from
    captured state — clock_trace, model_response_refs (from
    s2.1's persisted refs), fetch_outcome_refs (from fetcher
    history), seed_refs (deterministic per spec.id).
  - Phase 3 (replay): Construct `InMemoryReplayConsumer(bundle)`,
    new `ExternalCrawlRunner` with `replay_consumer=consumer`
    + same spec. Run. Capture `run_report_b`.
  - Phase 4 (compare): Assert
    `run_report_a.canonical_json() ==
    run_report_b.canonical_json()` byte-equal. Also assert
    artifact dir contents byte-equal where applicable.

- **Compare helper** at
  `tests/integration/_replay_compare.py` (or inline in test):
  - Strips inherently-wall-clock fields not yet in s6-7's
    replay scope (e.g., `started_at`, log timestamps) before
    comparison. Documented in §Out below.

- **Tests** (red list 5).

### Out

- Full `run_report.canonical_json()` byte-equality. s6
  reservation 3 noted that inherited `_now()` calls in fields
  like `started_at` make full-report byte-equality infeasible
  until a separate slice tightens those. s13 scope is
  **narrowed**: byte-equality on (a) graph events, (b)
  `plan_decision_*` keys, (c) `plan_decision_2_*` keys,
  (d) artifact content hashes, (e) `replay_consumer_ref` —
  but NOT `started_at`-class fields.
- Live network tests against real external sites. The HTTP
  stub is fully local.
- Multi-corpus replay. One corpus only.

## Design

### Module map

```
tests/integration/test_runner_replay_byte_identical.py   # new — ≤ 380 LOC (live mark)
tests/integration/_replay_compare.py                     # new — ≤  90 LOC (compare helpers)
tests/fixtures/replay_corpus/                            # new — fixture HTML files (3 pages)
```

NO source LOC delta. s13 is test-only.

### Replay invariant

This test IS the invariant. The narrowed scope (per §Out) is
the binding form until a follow-up slice resolves the
inherited `_now()` fields.

## Dependencies

- s11 (ReplayBundle + ReplayConsumerPort + InMemoryReplayConsumer
  impl'd).
- s12 (runner wiring impl'd).
- s2.1 (raw_response_ref persistence impl'd — bundle's
  `model_response_refs` must resolve through artifact store).
- s6 (clock_trace producer impl'd).

**Hard prerequisite**: s2.1, s6, s11, s12 all impl'd before s13.

## Test Strategy

### `tests/integration/test_runner_replay_byte_identical.py`

1. `test_record_phase_produces_clock_trace_and_raw_response_refs`.
2. `test_bundle_assembly_includes_all_recorded_refs`.
3. `test_replay_phase_uses_replay_consumer_for_clock_and_lookups`.
4. `test_record_and_replay_graph_events_byte_equal`.
5. `test_record_and_replay_plan_decision_keys_byte_equal`.

## Acceptance Criteria

1. **Pytest gate (live mark)** —
   `pytest -m live tests/integration/test_runner_replay_byte_identical.py -v`
   exits 0 with **5** collected, **5** passed.
2. **No regression on existing integration suite** —
   `pytest tests/integration/ -m "not live" -q` exits 0.
3. **LOC budget** — source delta is 0; test-only. Confirm via
   `git diff --numstat <plan_first>..HEAD -- src/` returns 0
   lines.
4. **Plan-review** grep ≥ 1.
5. **Task-review per commit** — s6 AC7 shape adapted.

## Rollback

s13 only adds test files. Revert removes them.

## Open Questions

1. **Full report byte-equality**: deferred to a follow-up
   slice that systematically removes `_now()` from
   non-graph-event fields.
2. **Artifact dir byte-equality**: assumes the artifact store
   adapter is deterministic per content-hash. s15 lands the
   hashed-fs adapter as default.
