# s6 — `ExternalCrawlRunner` wires `GraphObservationPort` + replan via feedback-aware planner

## Status

| Iter | Date (UTC) | Verdict | Findings (one-liner) | Resolution |
|------|------------|---------|----------------------|------------|
| 1    | 2026-05-14 | REJECTED | 1 blocker + 2 majors + 1 minor: (blocker) clock-and-replay design is incompatible with the runner's existing `_clock: Callable[[], float]` (monotonic for deadlines); graph_observation events require UTC `datetime`. (major) ctor-mode validation said "all 4 set or all None" but also preserved s3 pair-mode — self-contradictory; no red test covered the s3-pair-only path. (major) AC4 import-boundary check used a narrow grep on `from veracrawl.adapters.(graph|planning)` — misses `import veracrawl.adapters`, relative imports, etc. (minor) topic README s6 row said "runner constructs an observer adapter per run" — contradicts the plan's composition-root wiring rule. | Plan revised to v2: new `utc_clock: Callable[[], datetime]` ctor param (separate from `_clock`'s float monotonic for deadlines); validators on injected UTC clock; replay invariant relies on `utc_clock` being injected by the caller (test fakes use a frozen UTC clock). Ctor-mode rules made precise: exactly **three** valid configurations (legacy 0-set, s3 2-set with `planner+plan_request_builder`, s6 5-set with `+utc_clock+graph_observer+feedback_aware_planner_factory`). New red tests: explicit s3-pair-only "no observe / no replan" regression test; rewritten AC4 + new test 18 covering AST allowlist on `runner.py` for ALL `veracrawl.*` imports (rejects `Import` of `veracrawl.adapters` and aliased forms). README s6 row reworded — caller wires the observer + factory at the composition root. AC1 18 → 19 (new s3-pair regression test) + AC4 strengthened. |
| 2    | 2026-05-14 | REJECTED | 2 blockers + 2 majors + 1 minor: (blocker) replay-invariant section still said `observed_at`/`snapshot_at` came from `self._clock()` (the monotonic float clock) — the iter-1 fix had only patched the §Scope event-recording prose; the §Replay invariant prose kept the wrong reference. (blocker) feedback `run_ref` set to `spec.id`, but the s5 v2 adapter requires `feedback.run_ref == request.run_ref` — existing test builders use `run_ref=f"run:test:{spec.id}"`, not `spec.id`; the replan call could fail. (major) ctor validation red tests covered observer-only, factory-only, and observer+factory-without-s3-pair, but did NOT cover `utc_clock`-only, `utc_clock+observer-without-factory`, or `observer+factory-without-utc_clock` — implementations could leave `utc_clock` out of validation. (major) §Scope said "record `canonical_url = item.canonical_url`" for every enqueue including seeds, but `_frontier.enqueue(...)` for seeds takes a URL string directly (no `item`); test 6 also didn't explicitly pin each child URL. (minor) §Green path still said "After all 18 tests pass" while §Test Strategy lists 20 and AC1 requires 20. | Plan revised to v3: §Replay invariant rewritten — `observed_at`/`snapshot_at` source switched to `self._utc_clock()` everywhere, replay-stability claim **narrowed** to the s4 events + plan_decision_2 keys (the runner already writes wall-clock `_now()` into pre-existing report fields like `started_at` — that's an inherited s3-and-earlier non-determinism, not new in s6). Feedback `run_ref` rule made explicit: all 4 event types use `run_ref = original_plan_request.run_ref` (NOT `spec.id`); feedback derive call uses the same; v2 adapter's `feedback.run_ref == request.run_ref` invariant therefore holds by construction. Ctor validation: 3 new red tests (1c utc_clock-only, 1d utc_clock+observer-without-factory, 1e observer+factory-without-utc_clock). Event-recording site descriptions rewritten to name the URL parameter at the call site (seed: the seed URL string; discovery: the child canonical URL). Test 6 extended to pin each child URL. Test-count prose synced 18 → 20. AC1 20 → 23 (new 1c/1d/1e ctor tests). |
| 3    | 2026-05-14 | REJECTED | 2 blockers + 1 major: (blocker) import-boundary test 18 said "name starts with `veracrawl.adapters.`" but `from veracrawl import adapters as a` normalizes `ImportFrom.module` to `"veracrawl"` (with `name="adapters"` in the alias) — would pass test 18 and silently let the adapter package leak into the runner. (blocker) `utc_clock` introduces new non-determinism but the run_report has no `utc_clock_ref` and no replay consumer is wired in s6 or a directly dependent slice — violates the standing replay-refs-and-consumer rule. (major) test 16 still required byte-equal `run_report` JSON across runs, but §Replay invariant explicitly says the full report is NOT byte-equal due to inherited wall-clock `_now()` fields. Self-contradictory. | Plan revised to v4: test 18's AST walk extended to ALSO inspect every `ImportFrom.names` alias when `module == "veracrawl"`, rejecting any `alias.name in {"adapters"}`; positive companion test 19 stays. Runner ctor gains `utc_clock_ref: Ref` (a non-blank string, required when `utc_clock` is set; rejected when `utc_clock` is None). The ref is persisted into the run_report as `utc_clock_ref: str | None` and into both `decision.replay_refs` and `feedback.id`'s lineage. Test 16 rewritten as "byte-equal **graph_event_ids list** + byte-equal **plan_decision_2_replay_refs** across runs" (narrower, mechanically matches §Replay invariant scope). 2 new red tests added: 4d (`utc_clock_ref` blank/missing rejection), 16b (replay-bundle completeness: `utc_clock_ref in run_report`). AC1 23 → 25. |
| 4    | 2026-05-14 | REJECTED | 1 blocker + 3 majors: (blocker) `utc_clock_ref` was only persisted in the run_report; the replay consumer was deferred to s11/s12 (not directly dependent on s6) — violates the standing rule that new non-determinism must wire the consumer in the same or a directly dependent slice. (major) §Why still claimed byte-equal `run_report`, contradicting §Replay invariant. (major) `utc_clock_ref` validation tests missed the "non-blank `utc_clock_ref` with `utc_clock=None`" case (the reverse partial). (major) discovery URL recording could record the raw href instead of the canonical URL returned by `EnqueueOutcome`; test 6 used pre-canonicalized fixtures and would not catch it. | Plan revised to v5: new same-slice replay adapter `ReplayingUtcClock` added to s6 scope (at `src/veracrawl/adapters/clocks/replaying_utc_clock.py`, ~30 LOC) — closes the "wire the consumer in same/directly-dependent slice" rule; takes a `utc_clock_ref` + pre-recorded `datetime` sequence and replays them deterministically. §Why prose narrowed to match §Replay invariant — claim now reads "byte-equal graph-event lists + plan_decision_2 keys across runs with the same fixture-wired UTC clock". 1 new red test 4e (`utc_clock_ref` non-blank with `utc_clock=None` rejection). Discovery-recording rule rewritten: event uses `EnqueueOutcome.canonical_url` (the post-canonicalization value returned by the frontier), not the raw href; test 6 extended with a discovery URL that requires canonicalization (`https://seed.example/path?utm=x#frag` → frontier canonicalizes to `https://seed.example/path` — event must record the canonical). AC1 25 → 28 (4e, plus 2 new tests for the replay adapter: test 20 `test_replaying_utc_clock_returns_canned_datetimes_in_order`, test 21 `test_runner_with_replaying_utc_clock_produces_byte_equal_graph_event_ids`). |
| 5    | 2026-05-14 | PLAN_DONE_WITH_RESERVATIONS | 1 blocker + 2 majors + 1 minor: (blocker) `ReplayingUtcClock` consumed caller-provided `canned` datetimes — no same-slice **producer** recorded the actual clock sequence into the replay bundle, so the consumer-side wiring still wasn't closed. (major) `ReplayingUtcClock` adapter import boundaries had no AST test — could leak imports of runtime modules. (major) AC7's commit-path audit omitted the new replay-adapter source + test paths. (minor) iter-4 trail prose said AC1 "25 → 28" while the actual count is 29. | v6 fixes landed in same plan revision (NOT re-reviewed per goal-doc workflow, iter budget exhausted): (1) runner now records every `utc_clock()` invocation into a `clock_trace: list[str]` (ISO 8601 UTC datetimes) field on the run_report — this IS the producer side. New helper `replaying_utc_clock_from_run_report(run_report, utc_clock_ref)` constructs a `ReplayingUtcClock` from that recorded trace; test 21 rewritten to use this real producer-consumer round-trip. (2) New test 22 `test_replaying_utc_clock_import_boundaries` (AST allowlist on the new adapter file — stdlib only). (3) AC7 `s6_exclusive_paths` extended with `src/veracrawl/adapters/clocks/replaying_utc_clock.py` + `tests/unit/adapters/clocks/test_replaying_utc_clock.py`. (4) Iter-4 stale row prose corrected. AC1 29 → 30 (test 22). Plan recorded as `PLAN_DONE_WITH_RESERVATIONS` with 4 reservations (see STATUS subsection). |

Codex plan-review gate via `~/.claude/hooks/codex-review.sh plan
<plan-file> --project-dir $PWD`. ≤ 5 iterations.

## Why

- **Goal-doc capability 2 closes here.** s4 shipped the graph-
  observation port + 4 event contracts + the deterministic
  fixture observer. s5 shipped the feedback contract + the
  feedback-aware fixture planner adapter (v2). s6 makes the
  loop run inside the live `ExternalCrawlRunner`: records
  graph events as fetches/redirects/parses happen, snapshots
  the observer when the frontier drains for the first time
  after ≥ 1 fetch, derives a `PlannerObservationFeedback`,
  invokes a *feedback-aware* planner via an injected
  factory, and enqueues any new planned seeds.
- **AGENTS.md hard constraint — low coupling.** The runner
  must depend on the **port** (`veracrawl.ports.graph_observation.
  GraphObservationPort`) and the **factory** signature, never
  on the adapter implementations. The s6 caller wires
  `InMemoryGraphObserver` (s4) and `lambda fb:
  DeterministicCrawlPlannerV2(feedback=fb)` (s5) at the
  composition root.
- **AGENTS.md hard constraint — replay invariant.** Two
  runs with the same `CrawlJobSpec` + same fixture-wired
  `utc_clock` (`ReplayingUtcClock`) + same fake fetcher
  produce **byte-equal graph-event lists** and
  **byte-equal `plan_decision_2_*` keys** (s5 v2 adapter's
  pure-function property). The snapshot / feedback /
  plan-req-2 ids are derived from the spec id
  (deterministic). The full `run_report.canonical_json()`
  is NOT yet byte-equal across runs — the runner has
  pre-existing wall-clock `_now()` fields (`started_at`,
  etc.) outside s6 scope. See §Replay invariant for the
  precise stability scope.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`graph/`,
  `graph_memory/`, `memory/` — fixture builders;
  `external_crawl/runner.py` imports zero graph symbols"*.
  After s6 the runner imports
  `veracrawl.ports.graph_observation.GraphObservationPort`
  and the s5 derive helper, and a graph signal flows into
  the second `PlanDecision`. The audit gap closes.

## Scope

### In

- **Runner ctor (new opt-in trio + UTC clock)** — added
  alongside the s3 `planner` + `plan_request_builder` pair
  and the existing `_clock: Callable[[], float]` (which
  stays as the monotonic deadline clock):
  - `utc_clock: Callable[[], datetime] | None = None` — a
    **separate** clock that returns a timezone-aware UTC
    `datetime`. Used to stamp `observed_at` /
    `snapshot_at` on the s4 events. Required for s6 mode
    because graph-observation contracts validate UTC-only
    (`graph_observation.py:_utc(...)`); the existing
    `_clock` is monotonic float for deadline math and is
    NOT interchangeable. Caller injects a fake-frozen
    UTC clock in tests (replay-stable); production wires
    `lambda: datetime.now(UTC)`.
  - `utc_clock_ref: Ref | None = None` — a deterministic
    caller-supplied ref naming the clock source used by
    `utc_clock`. Required (non-blank) when `utc_clock` is
    set; rejected when `utc_clock` is `None`. Example:
    `"utc-clock:wall:lambda-now-utc"` for production, or
    `"utc-clock:fixture:frozen-2026-05-14T12:00:00Z"` for
    tests. The runner persists this ref into the run
    report (see Run report additions) so the replay
    bundle contains the full clock-source provenance.
    This satisfies the AGENTS.md
    "new-non-determinism-must-write-replay-refs" rule —
    the replay consumer (deferred to s11/s12) reads the
    ref + spec id + same fixture inputs to rehydrate
    `utc_clock` deterministically.
  - `graph_observer: GraphObservationPort | None = None`.
  - `feedback_aware_planner_factory:
    Callable[[PlannerObservationFeedback], CrawlPlannerPort] | None = None`.

- **Ctor-mode rules — exactly three valid configurations,
  every other combination raises `ValueError` at
  construction time**:

  | Mode | s3 pair (`planner` + `plan_request_builder`) | s6 quartet (`utc_clock` + `utc_clock_ref` + `graph_observer` + `feedback_aware_planner_factory`) | Behavior |
  |------|---|---|----------|
  | **legacy** | both None | all None | seed_urls → frontier (no plan / no observe) |
  | **s3** | both set | all None | plan once, FIFO frontier, no observe, no replan |
  | **s6** | both set | all set | plan, observe events, snapshot + replan once when frontier drains after ≥ 1 fetch |

  Validation pseudocode (runs in `__init__`):
  ```python
  s3_set = planner is not None and plan_request_builder is not None
  s3_none = planner is None and plan_request_builder is None
  s6_set = (
      utc_clock is not None
      and utc_clock_ref is not None
      and graph_observer is not None
      and feedback_aware_planner_factory is not None
  )
  s6_none = (
      utc_clock is None
      and utc_clock_ref is None
      and graph_observer is None
      and feedback_aware_planner_factory is None
  )
  if not ((s3_set or s3_none) and (s6_set or s6_none)):
      raise ValueError(...partial-arg message...)
  if s6_set and not s3_set:
      raise ValueError("s6 args require the s3 pair to also be set")
  if utc_clock_ref is not None and not utc_clock_ref.strip():
      raise ValueError("utc_clock_ref must be non-blank when set")
  ```
  This makes the three modes mechanically distinguishable:
  legacy = both pairs None; s3 = s3 pair set, s6 trio None;
  s6 = both set. (The reverse — s3 trio set, s3 pair None —
  is illegal because the s6 replan path needs the original
  `PlanRequest` from the builder.)

- **Event recording — 3 sites in `runner.run()`** (all
  event `run_ref` values are
  `self._original_plan_request.run_ref`, captured once
  after the first `plan_request_builder(...)` call; see
  §Replay invariant for why):
  1. **`UrlObservedEvent`** — recorded at every successful
     `_frontier.enqueue(...)` admission. Two call sites:
     - **Seed enqueue** (in `run()` after the s3 planner
       step): the URL passed to `enqueue` is
       `seed.canonical_url` (from
       `decision.planned_seeds`); event fields:
       `canonical_url=seed.canonical_url`, `depth=0`,
       `parent_canonical_url=None`,
       `source_ref="frontier-admit:seed"`.
     - **Discovery enqueue** (in
       `_discover_and_enqueue(...)`): the runner currently
       calls `_frontier.enqueue(raw_href, ...)` and the
       frontier returns an `EnqueueOutcome` containing
       `canonical_url` (the post-canonicalization value).
       The event MUST use that
       `EnqueueOutcome.canonical_url`, NOT the raw href
       passed in. Event fields:
       `canonical_url=outcome.canonical_url`,
       `depth=parent.depth + 1`,
       `parent_canonical_url=parent.canonical_url`,
       `source_ref="frontier-admit:discovery"`.
       Recording only happens when `outcome.admitted is
       True` — denied URLs are NOT observed (frontier
       admission is the canonical "URL entered the
       crawl" signal).
     Shared fields: `id=f"url-obs:{spec.id}:{seq}"`
     (seq monotonic per run, 0-indexed),
     `run_ref=self._original_plan_request.run_ref`,
     `observed_at=self._utc_clock()`.
  2. **`RedirectObservedEvent`** — recorded for each entry
     in `fetch_outcome.redirect_history` (one event per
     hop). Fields: `id=f"redirect-obs:{spec.id}:{seq}"`,
     `run_ref=self._original_plan_request.run_ref`,
     `from_canonical_url=hop.from_url`,
     `to_canonical_url=hop.to_url`,
     `status_code=hop.status_code`,
     `observed_at=self._utc_clock()`.
  3. **`PageStructureObservedEvent`** — recorded once per
     fetched + parsed page at the top of
     `_discover_and_enqueue(...)` BEFORE the discovery-
     enqueue loop. Fields:
     `id=f"page-obs:{spec.id}:{seq}"`,
     `run_ref=self._original_plan_request.run_ref`,
     `page_canonical_url=item.canonical_url`,
     `discovered_link_count=len(extracted_anchors)`,
     `discovered_canonical_urls=[]` (empty list — s6
     defers canonical-link DOM detection to s6.1),
     `observed_at=self._utc_clock()`.

- **Replan trigger — exactly once per run**:
  - When the frontier becomes empty AND `fetch_count >= 1`
    AND the runner has not already re-planned in this run.
  - Flow:
    1. `snap = self._graph_observer.snapshot(
       id=f"snap:{spec.id}:1",
       snapshot_at=self._utc_clock())`
    2. `fb = derive_planner_observation_feedback(
       id=f"fb:{spec.id}:1",
       run_ref=self._original_plan_request.run_ref,
       snapshot=snap)`
    3. `req2 = original_plan_request.model_copy(update={
       "id": f"plan-req:{spec.id}:2",
       "observed_state_refs":
         [*original_plan_request.observed_state_refs, fb.id],
       })`
    4. `planner2 = self._feedback_aware_planner_factory(fb)`
    5. `decision2 = planner2.plan(req2)`
    6. **Enqueue** each `planned_seed` from `decision2`
       whose `canonical_url` has not already been admitted
       to the frontier in this run. Same priority-sort as
       s3.
    7. Continue the fetch loop until the frontier drains
       again (no third invocation — strictly one replan).

- **Run report additions** — alongside s3's 6
  `plan_decision_*` keys, s6 adds (keyed always so they're
  in the JSON shape even when the replan didn't fire — in
  that case the values are `None`):
  - `plan_decision_2_ref: str | None`
  - `plan_decision_2_replay_refs: list[str] | None`
  - `plan_decision_2_planned_seed_order: list[str] | None`
  - `plan_decision_2_adapter_priors: list[dict] | None`
  - `plan_decision_2_frontier_priority_hints: list[dict] | None`
  - `plan_decision_2_extraction_strategy_refs: list[str] | None`
  - `observation_snapshot_ref: str | None`
  - `observation_feedback_ref: str | None`
  - `utc_clock_ref: str | None` — non-None whenever
    `utc_clock` was set (i.e., s6 mode), regardless of
    whether a replan fired. The s6 replay-bundle anchor
    for graph-event clock provenance.
  - `clock_trace: list[str] | None` — non-None whenever
    `utc_clock` was set; one entry per `utc_clock()`
    invocation during the run, in invocation order,
    serialized as ISO 8601 UTC strings (e.g.,
    `"2026-05-14T12:00:00+00:00"`). This is the
    **producer-side** replay record: a second run
    constructed via
    `replaying_utc_clock_from_run_report(report,
    utc_clock_ref)` produces byte-equal graph events.
    Closes the AGENTS.md "wire the consumer in same or
    directly-dependent slice" rule by pairing the
    `ReplayingUtcClock` consumer with the runner's
    producer side.
  - `replan_invoked: bool` (always present, `False` for
    s3-only and zero-fetch runs).

- **Same-slice replay-consumer adapter for `utc_clock`** —
  `src/veracrawl/adapters/clocks/replaying_utc_clock.py`
  (≤ 30 LOC behavior):
  - `class ReplayingUtcClock`: `__init__(self, *,
    utc_clock_ref: str, canned: list[datetime])`;
    validators reject blank ref and empty canned list.
  - `__call__(self) -> datetime`: pops and returns
    `canned[self._cursor]`; advances cursor; if exhausted,
    raises
    `ValueError(match="ReplayingUtcClock exhausted")`.
  - Property `utc_clock_ref: str`.
  - **Module-level helper**
    `replaying_utc_clock_from_run_report(
    run_report: dict, utc_clock_ref: str) ->
    ReplayingUtcClock`: reads `run_report["clock_trace"]`
    (a `list[str]` of ISO 8601 UTC strings),
    deserializes each via `datetime.fromisoformat(...)`,
    and constructs `ReplayingUtcClock(
    utc_clock_ref=utc_clock_ref, canned=<deserialized>)`.
    Raises `ValueError` when
    `run_report["clock_trace"]` is missing/None or when
    `run_report["utc_clock_ref"] != utc_clock_ref`.
  - **Purpose**: closes the AGENTS.md
    "new-non-determinism-must-wire-producer-and-consumer-
    in-same-or-directly-dependent-slice" rule. The runner
    is the **producer** — it records every `utc_clock()`
    invocation into `run_report["clock_trace"]`. The
    `replaying_utc_clock_from_run_report` helper is the
    **consumer** — it takes that recorded trace and
    rehydrates a `ReplayingUtcClock` that yields the same
    sequence on a second run. Both producer + consumer
    are wired in s6.
  - No import of anything beyond stdlib (`datetime`,
    `typing`) and `veracrawl.contracts.common.Ref` /
    `VeraModel`-like primitives (it's not a VeraModel —
    it's a callable class; just plain Python). Import-
    boundary test for this adapter is part of test 21.

- **Integration test against a fixture HTTP server**:
  - Single-host HTTP server stub that serves one 301
    redirect plus a destination page with two outbound
    links. Verifies: observer records 1 redirect event +
    ≥ 3 url events + 1 page-structure event; replan
    invoked; `decision2.frontier_priority_hints` includes
    one `HOST_GLOB` hint with `match_value` equal to the
    redirected host. `@pytest.mark.live` is **not** used —
    the test uses a local stub (deterministic + offline)
    so CI can run it. A separate `@pytest.mark.live`
    smoke test against `httpbin.org/redirect/1` may follow
    in s6.1.

- **Tests** (red list ≥ 14 — see §Test Strategy).

### Out

- **CanonicalObservedEvent recording**: requires extending
  `LinkExtractor` (or a new DOM observer) to surface
  `<link rel="canonical">` and the runner currently has no
  hook for it. Deferred to s6.1.
- **Re-plan loop beyond a single replan**: each "frontier-
  empty" event after the first one does NOT trigger
  another replan. s6 strictly does one replan. Multi-round
  re-planning is deferred to a future slice (likely fused
  into priority-queue work s3.1 + s6.1).
- **Hint application** — `decision2.frontier_priority_hints`
  is **recorded** in the run report but the FIFO frontier
  does not apply the deltas. Application lands in s3.1
  (priority-queue frontier).
- **Adapter-priors application** — same: recorded, not
  applied. Application lands in s3.2.
- **Extraction strategy execution** — s10.
- **Backward-compat removal of the s3-only form**: when
  none of the four ctor args is set, the runner falls back
  to the legacy direct `spec.seed_urls → frontier.enqueue`
  path (no plan, no observe, no replan). The s3
  `(planner, plan_request_builder)` pair-only path is also
  preserved (plan once, no observe, no replan).

## Backward compatibility

See the §Scope ctor-mode rules table — three valid modes
(legacy / s3 / s6). The s3 mode added in `7d33df1` and
earlier is preserved verbatim; s6 only adds new opt-in
ctor args without changing existing behavior for callers
that don't pass them.

## Design

### Module map

```
src/veracrawl/external_crawl/runner.py                         # modify — ≤ ~250 LOC behavior delta
src/veracrawl/adapters/clocks/replaying_utc_clock.py           # new — ≤  40 LOC
tests/unit/external_crawl/test_runner_wires_graph_observation.py   # new — ≤ 420 LOC
tests/unit/adapters/clocks/test_replaying_utc_clock.py             # new — ≤  80 LOC
tests/integration/test_runner_with_graph_observation_stub.py       # new — ≤ 160 LOC
tests/contract/test_runner_graph_observation_import_boundaries.py  # new — ≤  90 LOC
```

Behavior LOC delta total: ≤ 290 (runner ≤ 250 + replay
adapter ≤ 40). Under the binding ≤ 300 cap.

Behavior-LOC delta for `runner.py`: **≤ 250 LOC** (counted
as `git diff --shortstat HEAD~ runner.py` net + insertions).
Under the binding ≤ 300 LOC cap with margin for unit-test
hooks (e.g., factoring out a `_record_url_observed` method).

### Replay invariant

s6 introduces three new ids (`snap:{spec.id}:1`,
`fb:{spec.id}:1`, `plan-req:{spec.id}:2`) — all derived
from the spec id, no clock or RNG involved. The four
event-id sequences (`url-obs`, `redirect-obs`, `page-obs`,
plus the seq for re-plan-enqueued URLs which reuses
`url-obs`) are monotonic per run.

**Clock-source rule**: `observed_at` / `snapshot_at`
timestamps are sourced exclusively from
`self._utc_clock()`. This is a **separate** clock from
the existing `self._clock: Callable[[], float]` (which
returns a monotonic float for deadline math and is NOT
interchangeable with the UTC `datetime` required by
graph_observation contracts).

**Run-ref rule**: all 4 event types (`UrlObservedEvent`,
`RedirectObservedEvent`, `CanonicalObservedEvent` — not
recorded by s6 but reserved by contract,
`PageStructureObservedEvent`) use
`run_ref = original_plan_request.run_ref`. The derived
`PlannerObservationFeedback` uses the same `run_ref`. The
second `PlanRequest` (`plan-req:{spec.id}:2`) is a
`model_copy(update=...)` of the original, so its
`run_ref` is identical by construction. Therefore the s5
v2 adapter's `feedback.run_ref == request.run_ref`
invariant **holds by construction** — no caller-side
glue required.

**Replay-stability scope**: two runs with the same
`CrawlJobSpec` + fake-frozen `utc_clock` + fake fetcher
produce byte-equal **graph-event lists** AND byte-equal
`plan_decision_2_*` keys in the run report. The full
`run_report.canonical_json()` is NOT yet byte-equal
across runs because the runner has inherited
wall-clock `_now()` calls into pre-existing fields
(`started_at`, etc.) — that is an s3-and-earlier
non-determinism, not new in s6 and not in scope here.
A future slice (likely paired with s11/s12 replay
work) will fold the full-report invariant in.

### Cross-module flow

- `external_crawl/runner.py` imports:
  - existing: `veracrawl.ports.crawl_planner.CrawlPlannerPort`,
    `veracrawl.contracts.crawl_planner.{PlanRequest,PlanDecision,...}`,
    runner-internal modules.
  - **new**: `veracrawl.ports.graph_observation.GraphObservationPort`,
    `veracrawl.contracts.graph_observation.{UrlObservedEvent,
    RedirectObservedEvent, PageStructureObservedEvent,
    GraphObservationSnapshot}`,
    `veracrawl.contracts.planner_observation_feedback.{
    PlannerObservationFeedback,
    derive_planner_observation_feedback}`.
  - **forbidden** (rejected by test 18's AST walk): ANY
    `veracrawl.adapters.*` import — bare
    `import veracrawl.adapters`, `from veracrawl.adapters
    import …`, `from veracrawl.adapters.graph.…
    import …`, aliased `import veracrawl.adapters as a`,
    relative `from ..adapters import …`. The architectural
    rule is "runner imports ports + contracts only";
    test 18 enforces it by walking every `ast.Import` /
    `ast.ImportFrom` node and asserting the normalized
    dotted name neither starts with `veracrawl.adapters.`
    nor equals `veracrawl.adapters`.
- `tests/integration/test_runner_with_graph_observation_stub.py`
  wires `InMemoryGraphObserver` (s4 adapter) and
  `DeterministicCrawlPlannerV2` (s5 adapter) at the test
  composition root; the runner sees them only as
  `GraphObservationPort` and the factory closure.

## Dependencies

### On prior slices

- s1 (`CrawlPlannerPort` + `PlanRequest` / `PlanDecision`).
- s3 (`runner` already has `planner` + `plan_request_builder`
  ctor args + plan-decision wiring + run_report keys).
- s4 (`GraphObservationPort` + 4 event contracts +
  `InMemoryGraphObserver`).
- s5 (`PlannerObservationFeedback` +
  `derive_planner_observation_feedback` +
  `DeterministicCrawlPlannerV2`).

### Prerequisites

None new.

## Test Strategy

Red-first list.

### `tests/unit/external_crawl/test_runner_wires_graph_observation.py`

1. `test_legacy_mode_unchanged_by_s6` — no s6 ctor args
   AND no s3 ctor args → exactly legacy behavior; run
   report does NOT contain any `plan_decision_2_*` or
   `observation_*` keys with non-None values;
   `replan_invoked == False`.
1a. `test_s3_pair_only_mode_unchanged_by_s6` — `planner`
   + `plan_request_builder` set, all three s6 trio args
   `None` → s3 behavior verbatim (plan once, FIFO
   frontier, no observe, no replan). Run report has the
   6 `plan_decision_*` keys from s3 + the new
   `plan_decision_2_*` / `observation_*` keys all None;
   `replan_invoked == False`. This pins the s3-mode
   regression that s6 must not break.
2. `test_partial_ctor_args_raise_value_error_observer_only` —
   `graph_observer` set, `feedback_aware_planner_factory`
   missing → `ValueError(match="graph_observer and feedback_aware_planner_factory")`.
3. `test_partial_ctor_args_raise_value_error_factory_only` —
   reverse of test 2.
4. `test_partial_ctor_args_raise_value_error_observer_without_s3_pair` —
   `graph_observer` + `factory` + `utc_clock` set,
   `planner` missing → `ValueError`.
4a. `test_partial_ctor_args_raise_value_error_utc_clock_only` —
   `utc_clock` set, `graph_observer` + `factory` missing
   (with s3 pair set) → `ValueError(match="utc_clock and graph_observer and feedback_aware_planner_factory")`.
4b. `test_partial_ctor_args_raise_value_error_observer_factory_without_utc_clock` —
   `graph_observer` + `factory` set, `utc_clock` missing
   (with s3 pair set) → `ValueError`.
4c. `test_partial_ctor_args_raise_value_error_utc_clock_observer_without_factory` —
   `utc_clock` + `graph_observer` set, `factory` missing
   (with s3 pair set) → `ValueError`.
4d. `test_partial_ctor_args_raise_value_error_utc_clock_ref_blank_or_missing` —
   `utc_clock` + `graph_observer` + `factory` + s3 pair
   all set, but (a) `utc_clock_ref=""` → `ValueError(match="utc_clock_ref must be non-blank")`,
   and (b) `utc_clock_ref=None` → `ValueError(match="utc_clock_ref")`.
   Two parametrized cases counted as one test (still 1
   collected for AC1).
4e. `test_partial_ctor_args_raise_value_error_utc_clock_ref_without_utc_clock` —
   `utc_clock_ref="utc-clock:foo"` set, `utc_clock=None`
   (with all other args legal) → `ValueError(match="utc_clock_ref")`.
   Pins the reverse partial.
5. `test_observer_records_url_observed_per_admitted_seed` —
   spec with 2 seeds + observer wired → observer's
   `record_url_observed` called twice with the seed URLs
   in `canonical_url`, both at `depth=0`.
6. `test_observer_records_url_observed_per_admitted_discovery` —
   one seed at `https://seed.example/` with two child
   anchors: `https://seed.example/child-a` (already
   canonical) and `https://seed.example/child-b/?utm=x#frag`
   (REQUIRES canonicalization to
   `https://seed.example/child-b/`). The runner enqueues
   the raw hrefs; the frontier returns `EnqueueOutcome`
   with `canonical_url` set to the canonicalized form.
   The observer's `record_url_observed` call sequence
   must be:
   - call[0]: `canonical_url == "https://seed.example/"`,
     `depth == 0`, `parent_canonical_url is None`,
     `source_ref == "frontier-admit:seed"`.
   - call[1]: `canonical_url ==
     "https://seed.example/child-a"`, `depth == 1`,
     `parent_canonical_url == "https://seed.example/"`,
     `source_ref == "frontier-admit:discovery"`.
   - call[2]: `canonical_url ==
     "https://seed.example/child-b/"` *(canonicalized —
     NOT `…/child-b/?utm=x#frag`)*, `depth == 1`,
     `parent_canonical_url == "https://seed.example/"`,
     `source_ref == "frontier-admit:discovery"`.
   Pins the rule: discovery records use
   `EnqueueOutcome.canonical_url`, not the raw href.
7. `test_observer_records_redirect_observed_per_redirect_hop` —
   spec with one seed; mock fetcher returns
   `redirect_history` = [hop_a, hop_b] → observer's
   `record_redirect_observed` called twice with both
   hops' status codes preserved.
8. `test_observer_records_page_structure_observed_per_fetched_page` —
   spec with two pages each having three links →
   `record_page_structure_observed` called twice with
   `discovered_link_count == 3` each.
9. `test_replan_invoked_once_after_first_frontier_drain` —
   spec with two seeds + observer wired → factory called
   exactly once with a `PlannerObservationFeedback`
   value; `replan_invoked == True`.
10. `test_replan_not_invoked_when_no_fetches_happen` —
    all seeds robots-denied or otherwise unfetched → no
    `record_*` events with fetch context; factory NOT
    called; `replan_invoked == False`.
11. `test_replan_request_threads_feedback_id_in_observed_state_refs` —
    inspect the `PlanRequest` passed to the factory's
    planner: `feedback.id in request.observed_state_refs`,
    `request.id == "plan-req:{spec.id}:2"`.
12. `test_replan_decision_2_enqueues_new_seeds` —
    factory returns a plan with one new seed URL not yet
    in the frontier; verify the new URL is fetched in
    the second drain phase (mock fetcher records the
    fetch).
13. `test_run_report_contains_plan_decision_2_and_observation_refs` —
    run report has non-None values for all 6
    `plan_decision_2_*` keys + `observation_snapshot_ref`
    + `observation_feedback_ref` + `replan_invoked: True`.
14. `test_run_report_replan_invoked_false_when_zero_fetches` —
    same as test 10 but checks the run_report key.
15. `test_event_ids_are_deterministic_from_spec_id` —
    snapshot id = `snap:{spec.id}:1`, feedback id =
    `fb:{spec.id}:1`, plan-req-2 id =
    `plan-req:{spec.id}:2`. No clock leakage into ids.
16. `test_two_runs_produce_byte_equal_graph_event_ids_and_decision2_replay_refs` —
    replay invariant (narrowed scope) — two
    `ExternalCrawlRunner(...).run()` calls with the same
    `CrawlJobSpec` + fake-frozen `utc_clock` + fake
    fetcher produce:
    - byte-equal `run_report["plan_decision_2_replay_refs"]`
      list,
    - byte-equal lists of recorded event ids in each of
      `record_url_observed`, `record_redirect_observed`,
      `record_page_structure_observed` invocations
      (assert via two `InMemoryGraphObserver` instances,
      one per run, compare `snapshot.canonical_json()`).
    Full `run_report.canonical_json()` byte-equality is
    NOT asserted because the runner's inherited
    `_now()` fills inherited wall-clock fields
    (`started_at`, etc.) — see §Replay invariant.
16b. `test_run_report_contains_utc_clock_ref` —
    when `utc_clock_ref="utc-clock:fixture:frozen"` is
    injected at ctor, the resulting `run_report` contains
    `utc_clock_ref == "utc-clock:fixture:frozen"`. This
    is the replay-bundle anchor for the new s6
    non-determinism (the UTC clock source).

### `tests/unit/adapters/clocks/test_replaying_utc_clock.py`

20. `test_replaying_utc_clock_returns_canned_datetimes_in_order` —
    `clock = ReplayingUtcClock(utc_clock_ref="utc-clock:fixture:1",
    canned=[t0, t1, t2])`; `clock() == t0`, `clock() == t1`,
    `clock() == t2`; fourth call raises
    `ValueError(match="ReplayingUtcClock exhausted")`.
20a. `test_replaying_utc_clock_rejects_blank_ref_and_empty_canned` —
    blank `utc_clock_ref` → `ValueError`; empty `canned`
    list → `ValueError`.
20b. `test_helper_round_trips_clock_trace` *(s6 step-1
    iter-1 task-review follow-up)* — helper-direct unit
    test: a `run_report` with `utc_clock_ref` +
    `clock_trace` ISO-string list round-trips through
    `replaying_utc_clock_from_run_report` to a working
    clock. Closes the iter-1 TDD gap: the helper's
    round-trip via the runner (test 21) lands later in
    step 4, but the helper itself ships in step 1 — this
    direct test pins it.
20c. `test_helper_rejects_mismatched_ref` — helper-direct:
    raises `ValueError(match="utc_clock_ref must match")`
    when the supplied `utc_clock_ref` doesn't match
    `run_report["utc_clock_ref"]`.
20d. `test_helper_rejects_missing_or_empty_clock_trace` —
    helper-direct: both `clock_trace=None` and
    `clock_trace=[]` cases raise `ValueError(match="clock_trace")`.
21. `test_runner_clock_trace_round_trip_produces_byte_equal_graph_events` —
    end-to-end producer-consumer wiring:
    1. **Producer run**: construct
       `ExternalCrawlRunner` with a wall-clock fake
       `utc_clock = make_advancing_fake_clock()` (each
       call returns a distinct datetime). Run.
       Capture `run_report_1`.
    2. **Consumer run**: build a replay clock via
       `clock2 = replaying_utc_clock_from_run_report(
       run_report_1, utc_clock_ref=...)`. Construct a
       second `ExternalCrawlRunner` with
       `utc_clock=clock2`, same spec / fetcher.
       Run. Capture `run_report_2`.
    3. **Assert** the two observers' `snapshot.canonical_json()`
       outputs are byte-equal, and the two reports'
       `plan_decision_2_replay_refs` lists are byte-equal.
    Pins the real producer-consumer round-trip — NOT
    just two manual `canned` lists.
22. `test_replaying_utc_clock_import_boundaries` —
    AST walk of
    `src/veracrawl/adapters/clocks/replaying_utc_clock.py`.
    Allowlist: stdlib only (`__future__`, `typing`,
    `datetime`, `collections.abc`). Reject ANY
    `veracrawl.*` import (including
    `veracrawl.contracts.common`, since the adapter
    needs only Python primitives). This forbids the
    adapter from depending on any internal runtime
    module — closes the iter-5 "adapter could import
    runner" gap.

### `tests/integration/test_runner_with_graph_observation_stub.py`

17. `test_local_stub_redirect_produces_host_glob_hint` —
    spin up a local HTTP stub serving:
    - `/start` → `301` redirect to `/target`
    - `/target` → 200 HTML with two link anchors
    Run the runner with `InMemoryGraphObserver` +
    `lambda fb: DeterministicCrawlPlannerV2(feedback=fb)`.
    Verify: `decision_2.frontier_priority_hints`
    contains exactly one `HOST_GLOB` hint with
    `match_value == "localhost"` (or the stub's
    hostname), `priority_delta == 0.6`.

### `tests/contract/test_runner_graph_observation_import_boundaries.py`

18. `test_runner_imports_no_veracrawl_adapters` —
    AST walk of `src/veracrawl/external_crawl/runner.py`,
    five sub-checks (every collected import must satisfy
    all five):
    1. **No relative imports**: every `ast.ImportFrom`
       has `level == 0`.
    2. **`Import` rejects `veracrawl.adapters*`**:
       for every `ast.Import` node and every
       `alias.name`, reject if `alias.name == "veracrawl.adapters"`
       or `alias.name.startswith("veracrawl.adapters.")`.
       This catches `import veracrawl.adapters as a`,
       `import veracrawl.adapters.graph`, etc.
    3. **`ImportFrom.module` rejects `veracrawl.adapters*`**:
       for every `ast.ImportFrom`, reject if
       `module == "veracrawl.adapters"` or
       `module.startswith("veracrawl.adapters.")`.
    4. **`ImportFrom` with `module=="veracrawl"` rejects
       importing `adapters` as a name**: for every
       `ast.ImportFrom` where `module == "veracrawl"`,
       reject if any `alias.name == "adapters"`. This
       catches `from veracrawl import adapters` and
       `from veracrawl import adapters as a`.
    5. **`ImportFrom.module` not equal to `veracrawl`
       without sub-package**: parallel to (4), pin that
       the runner never does bare
       `from veracrawl import X` for **any** `X`
       (force the runner to qualify everything as
       `veracrawl.<pkg>.<…>`).
19. `test_runner_imports_graph_observation_port_and_feedback_contract` —
    positive companion: assert the runner DOES import the
    s6-mandated symbols (`GraphObservationPort` from
    `veracrawl.ports.graph_observation`,
    `derive_planner_observation_feedback` from
    `veracrawl.contracts.planner_observation_feedback`).
    Without this, a vacuously-passing test 18 (e.g., the
    runner module emptied to a stub) would still claim
    boundary-clean.

### Green path

Each red test gets a minimal implementation. One purpose
per commit. After all 33 tests pass, refactor only obvious
duplication.

## Acceptance Criteria

Mechanically verifiable.

1. **Pytest gate** —
   `pytest tests/unit/external_crawl/test_runner_wires_graph_observation.py tests/unit/adapters/clocks/test_replaying_utc_clock.py tests/integration/test_runner_with_graph_observation_stub.py tests/contract/test_runner_graph_observation_import_boundaries.py -v`
   exits 0 with **33** collected, **33** passed.
   (Original v1: 18. v2 added: 1a, 19.
   v3 added: 4a, 4b, 4c.
   v4 added: 4d, 16b; test 16 reworked to the narrower
   replay-stability scope per §Replay invariant.
   v5 added: 4e, 20, 20a, 21.
   v6 follow-up: test 21 rewritten as a real producer-
   consumer round-trip via the new helper
   `replaying_utc_clock_from_run_report`; added test 22
   `test_replaying_utc_clock_import_boundaries`.
   s6 step-1 iter-1 task-review follow-up: added helper-
   direct tests 20b/20c/20d covering
   `replaying_utc_clock_from_run_report` since test 21
   (its runner-level round-trip) lands in step 4.)
2. **Existing suite regression-free** —
   `pytest tests/unit/external_crawl/ tests/integration/ -q`
   exits 0; no test that was passing before s6 begins
   failing after the s6 commits land.
3. **Import-boundary** —
   `pytest tests/contract/test_runner_graph_observation_import_boundaries.py -v`
   exits 0.
4. **No `veracrawl.adapters` imports in runner** —
   the test-18 AST walk is the binding check; this AC
   pins the matching pytest selector:
   `pytest tests/contract/test_runner_graph_observation_import_boundaries.py::test_runner_imports_no_veracrawl_adapters -v`
   exits 0. (The narrower grep that v1 used was rejected
   in iter 1 for missing `import veracrawl.adapters` and
   aliased forms; test 18 covers all those paths via the
   AST walk.)
5. **Behavior LOC budget for runner.py** —
   `delta=$(git diff --shortstat 7d33df1..HEAD -- src/veracrawl/external_crawl/runner.py | awk '{s=0; for(i=1;i<=NF;i++){if($i ~ /^[+-]?[0-9]+$/){s+=$i}}; print s}')`
   ; assert `[ "$delta" -le 300 ]`. (Baseline is the s5
   plan-land commit `7d33df1`.) **Tooling note**: this AC
   counts both insertions and deletions; the operative
   intent is "net behavior delta on runner.py is ≤ 300
   LOC". If `git diff --shortstat` output format varies
   across git versions, the manual check is `[ $(git
   diff 7d33df1..HEAD -- src/veracrawl/external_crawl/runner.py
   | grep -E '^\+|^-' | grep -vE '^(\+\+\+|---)' | wc -l)
   -le 300 ]`.
6. **Codex plan-review gate** — APPROVED in ≤ 5 iterations
   OR `DONE_WITH_RESERVATIONS` audit anchor in STATUS:
   `grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS|PLAN_DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s6-runner-wires-graph-observation.md`
   reports `≥ 1`.
7. **Codex task-review per commit recorded** — every
   commit whose subject begins with `s6:` between the
   s6 plan-land commit (`git log --diff-filter=A
   --pretty=format:'%H' -- docs/plans/general-purpose-
   crawler-agentification/s6-runner-wires-graph-
   observation.md | tail -1`) and `HEAD` MUST have a
   matching `s6-impl-<sha7>` STATUS row with verdict
   `APPROVED` or `DONE_WITH_RESERVATIONS`. Same shell
   recipe shape as s5 AC8 (phase A1 + B), adapted for
   s6 file set:
   ```bash
   set -eu
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' \
     -- docs/plans/general-purpose-crawler-agentification/s6-runner-wires-graph-observation.md \
     | tail -1)
   [ -n "$plan_first" ] || { echo "s6 plan commit not found"; exit 1; }
   s6_exclusive_paths=(
     src/veracrawl/adapters/clocks/replaying_utc_clock.py
     tests/unit/external_crawl/test_runner_wires_graph_observation.py
     tests/unit/adapters/clocks/test_replaying_utc_clock.py
     tests/integration/test_runner_with_graph_observation_stub.py
     tests/contract/test_runner_graph_observation_import_boundaries.py
   )
   s6_shared_paths=(
     src/veracrawl/external_crawl/runner.py
   )
   bad_subject=0
   missing=0
   for sha in $(git log --pretty=format:'%H' "${plan_first}..HEAD" -- "${s6_exclusive_paths[@]}"); do
     subj=$(git log -1 --pretty=format:'%s' "$sha")
     case "$subj" in "s6:"*) ;; *) echo "off-policy: $sha '$subj'"; bad_subject=1 ;; esac
   done
   all=$(git log --pretty=format:'%H %s' "${plan_first}..HEAD" -- "${s6_exclusive_paths[@]}" "${s6_shared_paths[@]}")
   while IFS= read -r line; do
     sha=${line%% *}; subj=${line#* }
     case "$subj" in "s6:"*) ;; *) continue ;; esac
     short=$(git rev-parse --short=7 "$sha")
     grep -qE "s6-impl-${short}\b.* (APPROVED|DONE_WITH_RESERVATIONS)" docs/plans/general-purpose-crawler-agentification/STATUS.md \
       || { echo "missing s6-impl-${short}"; missing=1; }
   done <<<"$all"
   [ $bad_subject -eq 0 ] && [ $missing -eq 0 ]
   ```
   exits 0.

## Rollback

s6 only **adds** behavior. The legacy and s3 ctor-arg
modes remain valid (see §Backward compatibility table).
Rollback is `git revert <s6-commit-range>` — no schema
changes, no consumer breakage.

## Open Questions

1. **Event-id seq scoping**: per-run-global vs per-event-
   type. Default: per-run-global (so `url-obs:{spec}:0`
   precedes `redirect-obs:{spec}:1` etc.) — preserves
   total emission order across event types.
   Alternative: per-type seq (`url-obs:{spec}:0`,
   `url-obs:{spec}:1`, …, `redirect-obs:{spec}:0`, …).
   Default chosen because the s4 snapshot already
   preserves per-list emission order; a global seq
   exposes interleaving for downstream graph reasoning.
2. **Stub server vs real httpbin**: integration test 17
   uses a local stub (deterministic, offline, no flake).
   Real-httpbin smoke test is deferred to s6.1 to keep
   CI green even when external services are degraded.
3. **PageStructureObservedEvent's `discovered_canonical_urls`**:
   s6 leaves it as `[]` (empty). s6.1 will wire DOM
   `<link rel="canonical">` extraction. The empty list
   is allowed by the s4 contract validator.
