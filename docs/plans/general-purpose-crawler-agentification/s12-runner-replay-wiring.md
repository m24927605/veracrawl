# s12 — `ExternalCrawlRunner` reads `replay_config_ref` and routes through `ReplayConsumerPort`

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 2 blockers + 2 majors: (b) `lookup_fetch_outcome` returns Ref not FetchOutcome — replay path can't reconstruct; (b) model-response replay not wired through runner — factory signature only receives feedback. (m) runner imports adapter contradicted by no-adapter-imports AC; (m) ACs placeholders + Out contradicts Module map (replay_assembler in/out). | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | Iter-1 findings not closed. | v3. |
| 3 | 2026-05-15 | REJECTED | Bundle assembly both in/out of scope. | v4. |
| 4 | 2026-05-15 | REJECTED | Scope + ACs self-contradictory. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | ACs placeholders + cumulative issues. Iter cap reached. | 6 reservations: (R1) `replay_assembler` either in §Scope OR out, not both; (R2) fetch-outcome replay must materialize full `FetchOutcome` not Ref (needs an artifact-resolver helper that reads bytes via ArtifactStorePort.read + reconstructs); (R3) model-response replay path through runner must be typed (extend factory signature OR add a separate replay seam); (R4) inline ACs concrete; (R5) `ReplayingHttpFetcher` injection through composition root only (no adapter import in runner); (R6) hard prereqs: s11, s2.1, s6 all impl'd before s12 impl. |

Codex plan-review ≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5
per established pattern.

## Why

- **Capability 4 second slice.** s11 ships `ReplayConsumerPort`
  + in-memory fixture adapter. s12 wires the runner to consult
  the port when `spec.replay_config_ref` is set: clock, RNG,
  model responses, fetch outcomes all route through the
  consumer instead of wall sources. s13 runs the byte-equal
  re-execution test corpus end-to-end.

## Scope

### In

- **Runner ctor change**: new opt-in `replay_consumer:
  ReplayConsumerPort | None = None`. When set, runner uses it
  for clock + lookups; when None, runner uses existing
  wall-clock / live behavior. No breaking change.

- **Runner integration points**:
  - **Clock**: `self._utc_clock = self._replay_consumer.next_utc`
    when replay_consumer is set (overrides any caller-supplied
    `utc_clock`).
  - **Model responses**: `feedback_aware_planner_factory`
    closure pulls from `replay_consumer.lookup_model_response`
    when present (caller wires this via injected factory).
  - **Fetch outcomes**: `fetcher` is replaced with a wrapping
    `ReplayingHttpFetcher` that consults
    `replay_consumer.lookup_fetch_outcome` per URL.
  - **RNG seeds**: any random.Random instances seeded via
    `replay_consumer.next_seed(name)`.

- **Run report additions** (keyed-always):
  - `replay_consumer_ref: str | None` — identifier for the
    replay bundle in use.
  - `replay_invocation_count: int` — total
    `next_utc`/`lookup_*` calls.

- **`ReplayingHttpFetcher`** new adapter wrapping any
  `CrawlHttpFetcherPort` to substitute fetch outcomes from the
  replay consumer when the URL is in the bundle.

- **Tests** (red list 16).

### Out

- Bundle producer side. The runner already writes `clock_trace`
  via s6's producer. s12 doesn't add new producer wiring;
  bundle assembly (combining clock_trace + raw_response_refs +
  fetch_outcome_refs into a `ReplayBundle`) is the caller's
  responsibility.
- Byte-identical full-run test (s13).
- Streaming bundle / cross-run replay.

## Design

### Module map

```
src/veracrawl/external_crawl/runner.py                   # modify — ≤  50 LOC
src/veracrawl/adapters/network/replaying_http_fetcher.py # new — ≤  90 LOC
src/veracrawl/external_crawl/replay_assembler.py         # new — ≤  60 LOC (helper to build ReplayBundle from run state)
tests/unit/external_crawl/test_runner_with_replay_consumer.py  # new — ≤ 320 LOC
tests/unit/adapters/network/test_replaying_http_fetcher.py     # new — ≤ 180 LOC
tests/contract/test_replay_wiring_import_boundaries.py   # new — ≤ 100 LOC
```

Behavior LOC: 50 + 90 + 60 = **200 LOC**. Under ≤ 300 cap.

### Replay invariant

- When `replay_consumer` is set: clock + model responses +
  fetch outcomes all sourced from the bundle. Two runs with
  the SAME bundle produce byte-equal `run_report`.
- When `replay_consumer` is None: wall-clock + live providers/
  fetchers (existing behavior). No replay.

## Dependencies

- s11 (`ReplayConsumerPort`, `ReplayBundle`,
  `InMemoryReplayConsumer`).
- s2.1 (raw_response_ref persistence — bundle's
  `model_response_refs` entries must resolve).
- s6 (clock_trace producer side — bundle's clock_trace is
  recorded by the runner's existing s6 wiring).
- Existing `CrawlHttpFetcherPort`.

**Hard prerequisite**: s11 implemented; s6 already done; s2.1
should be impl'd (replay loop won't actually round-trip without
it but s12 doesn't depend on s2.1 source).

## Test Strategy

### `tests/unit/external_crawl/test_runner_with_replay_consumer.py`

1. `test_runner_no_replay_consumer_uses_wall_clock`.
2. `test_runner_with_replay_consumer_uses_next_utc_for_observed_at`.
3. `test_runner_replay_consumer_used_for_planner_factory_responses`.
4. `test_runner_replay_consumer_used_for_fetch_outcomes`.
5. `test_runner_records_replay_consumer_ref_in_run_report`.
6. `test_runner_records_replay_invocation_count_in_run_report`.
7. `test_runner_replay_consumer_overrides_utc_clock_when_both_set`.
8. `test_two_replay_runs_with_same_bundle_produce_byte_equal_graph_events`.
9. `test_replay_run_decision_2_replay_refs_byte_equal_to_recorded`.
10. `test_replay_consumer_exhausted_raises_replay_exhausted_error`.
11. `test_replay_consumer_lookup_miss_raises_replay_lookup_miss_error`.

### `tests/unit/adapters/network/test_replaying_http_fetcher.py`

12. `test_replaying_fetcher_returns_outcome_from_bundle_when_url_present`.
13. `test_replaying_fetcher_falls_through_to_wrapped_when_url_absent`.
14. `test_replaying_fetcher_raises_when_strict_mode_and_lookup_miss`.

### `tests/contract/test_replay_wiring_import_boundaries.py`

15. `test_runner_imports_replay_consumer_port_only`.
16. `test_replaying_http_fetcher_imports_allowlist`.

## Acceptance Criteria

1. Pytest gate: 16 collected, 16 passed.
2. Existing s6 + s3 suites green (no regression).
3. No `veracrawl.adapters.*` import in runner (existing AST
   test extended to cover replay imports).
4. LOC budget shell ≤ 300.
5. Plan-review grep ≥ 1.
6. Task-review per commit, same shape as s6 AC7.

## Rollback

s12 only adds opt-in behavior + new files. Revert removes
files; default runner unchanged.

## Open Questions

1. **`replay_consumer` vs `utc_clock` precedence**: when both
   set, replay_consumer wins. Documented.
2. **Strict-mode `ReplayingHttpFetcher`**: when fall-through to
   live wrapped fetcher should be allowed. Default: strict
   (no fall-through; lookup_miss raises).
