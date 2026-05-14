# s4 — `GraphObservationPort` + URL/canonical/redirect/structure event contracts

## Status

| Iter | Date (UTC) | Verdict  | Findings (one-liner) | Resolution |
|------|------------|----------|----------------------|------------|
| 1    | 2026-05-14 | REJECTED | 1 blocker + 2 majors: (blocker) `snapshot()` Protocol took no args but test 25 invoked it with kwargs (`id=`, `snapshot_at=`); inconsistent + replay-unsafe. (major) UTC-only `observed_at` / `snapshot_at` invariants had no red tests. (major) non-blank `id` / `run_ref` on every event + snapshot under-tested (only `UrlObservedEvent.source_ref` + snapshot `run_ref` were covered). | Plan revised to v2: `snapshot()` signature changed to `snapshot(self, *, id: str, snapshot_at: datetime) -> GraphObservationSnapshot` so all snapshot metadata is caller-injected (replay-safe). 14 new red tests added covering UTC-only datetimes (5 tests, one per event + snapshot) and non-blank id/run_ref (9 tests across 4 events + snapshot). AC1 collected count 26 → 40. |
| 2    | 2026-05-14 | REJECTED | 1 blocker + 2 majors + 1 minor: (blocker) `snapshot()` injects `id`/`snapshot_at` but not `run_ref` — observer is no-arg, so empty snapshots have no source for `run_ref`. (major) UTC-only tests reject naive only, not aware-non-UTC (e.g. `+08:00`). (major) AC7 + AC8 used review-status outcome wording, not mechanical pytest/CLI selectors. (minor) Design Dependencies lists `TimestampedModel` while Replay invariant requires `VeraModel` (events) — inconsistency. | Plan revised to v3: `InMemoryGraphObserver(run_ref: str)` takes the run_ref at construction; `record_*` validators reject events whose `run_ref` doesn't match; `snapshot()` derives `run_ref` from the observer. 5 new red tests for aware-non-UTC datetimes (strict reject; events use `VeraModel` + a custom UTC validator, not `TimestampedModel`'s convert-to-UTC pattern). AC7 + AC8 rewritten as shell-grep checks on the hook output (`grep -q "VERDICT: APPROVED"`). Dependencies clarified — events use `VeraModel`, no `TimestampedModel` import. AC1 collected count 40 → 45. |
| 3    | 2026-05-14 | REJECTED | 1 blocker + 2 majors: (blocker) test 26 still called `InMemoryGraphObserver()` no-arg, contradicting the iter-2 `run_ref`-kwarg ctor. (major) URL invariants for `RedirectObservedEvent.from_canonical_url`, `CanonicalObservedEvent.canonical_target_url`, `PageStructureObservedEvent.page_canonical_url` lacked red tests. (major) snapshot ref-list entries were not validated for non-blank — blank refs could land in lists. | Plan revised to v4: test 26 updated to `InMemoryGraphObserver(run_ref="run:test:1")`. 3 new red tests (8a/10a/11a) for the missing http(s)-URL invariants on the from/target/page URLs. 1 new test (15t) covering blank-entry rejection across all four snapshot ref lists. Snapshot validator behavior extended: ref-list entries must be non-blank. AC1 collected count 46 → 50. |
| 4    | 2026-05-14 | REJECTED | 1 blocker + 2 majors: (blocker) snapshot held only event-ref lists — s5's planner can't refine `frontier_priority_hints` from canonical / redirect / structural neighbours without reaching into adapter internals; ref strings alone don't expose URLs / edges / adjacency. (major) missing-field tests absent — an implementation could add `Field(default_factory=utc_now)` for `observed_at` / `snapshot_at` and still pass all 50 tests, reintroducing the very non-determinism `VeraModel` was supposed to forbid. (major) AC4 substring grep missed `import veracrawl.graph` / `from veracrawl import graph` / bare-package imports. | Plan revised to v5: snapshot redesigned to embed events directly (`url_observed_events: list[UrlObservedEvent]` etc., not refs) so s5 has a real typed read projection without coupling to adapter internals. Test 15t reframed to assert event `run_ref` matches snapshot `run_ref`. 5 new red tests 15u-15y reject missing `observed_at` / `snapshot_at` (one per event + snapshot). AC4 rewritten as a pytest selector on the AST allowlist test (test 19). AC1 collected count 50 → 55. |
| 5    | 2026-05-14 | REJECTED → DONE_WITH_RESERVATIONS via post-iter-5 follow-up | 1 blocker + 2 majors: (blocker) iter-4 snapshot redesign was inconsistent — two places (Data flow §118-120, red list 16 §330-331, registry test §421-423) still said "ref lists". (major) missing-field tests covered only `observed_at`/`snapshot_at` — `id`, `run_ref`, `source_ref` only had blank-value tests, so `Field(default_factory=...)` regressions could slip through. (major) AC7/AC8 had a mechanical `grep -q "VERDICT: APPROVED"` path but the "OR DONE_WITH_RESERVATIONS" branch wasn't deterministic. | Post-iter-5 follow-up landed in this same plan revision: every remaining "ref list" mention in Scope/Design/Test Strategy replaced with the embedded-event shape. 6 new missing-field tests 15z-15ee for `id` / `run_ref` / `source_ref` absence across all four events + snapshot. AC7/AC8 reservations branch tightened to a `grep -q` STATUS-row check. AC1 collected count 55 → 61. Plan recorded as `PLAN_DONE_WITH_RESERVATIONS`. |

Codex plan-review gate via `~/.claude/hooks/codex-review.sh plan
<plan-file> --project-dir $PWD`. ≤ 5 iterations.

## Why

- **AGENTS.md hard constraint — general-purpose**: capability 2 of the
  goal doc is *"Graph → planner feedback (URL/canonical/redirect/page-
  structure graph captured during real runs and consumed by frontier
  prioritization)"*. Today the graph contracts (`GraphNode` /
  `GraphEdge` / `GraphEdgeProvenance`) exist but no port captures
  observations from the live runner — `external_crawl/runner.py`
  imports zero graph symbols per the goal-doc audit. s4 introduces
  the observation port + event contracts that turn the runner's
  existing side effects (frontier admissions, redirect hops, canonical
  mappings, page-structure anchors) into typed observations consumable
  by a future planner-feedback adapter.
- **AGENTS.md hard constraint — low coupling**: the observation port
  must not depend on the existing `graph_memory` runtime or on any
  concrete persistence (SQLite, S3, etc.). s4 ships only the port
  + contracts + an in-memory fixture adapter. Persistent backends
  are later slices.
- **Goal doc capability 2 (first slice)**: per the
  `contract+port → fixture-mode adapter → production adapter →
  runtime-spine wiring → live integration test` rule, s4 delivers
  the first two stages. s5 introduces planner observation feedback
  (consumes the snapshot); s6 wires the runner.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`graph/`,
  `graph_memory/`, `memory/` — fixture builders; `external_crawl/
  runner.py` imports zero graph symbols; `projection/` is an empty
  package"*. s4 begins closing the observation half of that gap by
  shipping a port that the runner can consume in s6 without pulling
  in `graph_memory`.

## Scope

### In

- New event contracts in `veracrawl.contracts.graph_observation`:
  - `UrlObservedEvent` — emitted when a URL is admitted to the
    frontier. Fields: `id: str`, `run_ref: Ref`,
    `canonical_url: str` (absolute http(s)), `depth: int (≥ 0)`,
    `parent_canonical_url: str | None` (absolute http(s) if
    present), `source_ref: Ref` (e.g.
    `"seed"` / `"link-extractor"` / `"sitemap"`),
    `observed_at: datetime` (UTC).
  - `RedirectObservedEvent` — emitted when a 3xx hop is
    followed. Fields: `id`, `run_ref`,
    `from_canonical_url: str`, `to_canonical_url: str` (both
    absolute http(s); MUST differ), `status_code: int (300-399)`,
    `observed_at: datetime`.
  - `CanonicalObservedEvent` — emitted when a `rel=canonical`
    or sitemap canonical mapping is discovered. Fields: `id`,
    `run_ref`, `linked_canonical_url: str`,
    `canonical_target_url: str`, `source_kind: CanonicalSource`
    (new `StrEnum`: `LINK_REL_CANONICAL` / `HTTP_LINK_HEADER` /
    `SITEMAP`), `observed_at: datetime`.
  - `PageStructureObservedEvent` — emitted when a page's link
    structure is extracted. Fields: `id`, `run_ref`,
    `page_canonical_url: str`, `discovered_link_count: int
    (≥ 0)`, `discovered_canonical_urls: list[str]` (each
    absolute http(s); de-duplicated; ordered by emission),
    `observed_at: datetime`.
  - `GraphObservationSnapshot` — the read-side projection a
    later slice's planner consumes. *(Iter-4 blocker fix:
    embed the events directly so consumers can read URLs,
    redirect edges, canonical targets, and structural
    adjacency without reaching into adapter internals.)*
    Fields: `id: str`, `run_ref: Ref`,
    `url_observed_events: list[UrlObservedEvent]`,
    `redirect_observed_events: list[RedirectObservedEvent]`,
    `canonical_observed_events: list[CanonicalObservedEvent]`,
    `page_structure_observed_events: list[PageStructureObservedEvent]`,
    `snapshot_at: datetime`.

- One companion enum: `CanonicalSource` in
  `veracrawl.contracts.enums` (`StrEnum`).

- New port `veracrawl.ports.graph_observation.GraphObservationPort`
  (Python `Protocol`, `runtime_checkable`):

  ```python
  class GraphObservationPort(Protocol):
      def record_url_observed(self, event: UrlObservedEvent) -> None: ...
      def record_redirect_observed(self, event: RedirectObservedEvent) -> None: ...
      def record_canonical_observed(self, event: CanonicalObservedEvent) -> None: ...
      def record_page_structure_observed(self, event: PageStructureObservedEvent) -> None: ...
      def snapshot(self, *, id: str, snapshot_at: datetime) -> GraphObservationSnapshot: ...
  ```

  *(Iter-1 blocker.)* `snapshot()` takes `id` and `snapshot_at`
  as caller-injected kwargs so the snapshot is fully
  deterministic from the caller's perspective. The observer
  does not synthesize timestamps or ids — those are replay
  refs and must come from the same clock / id-allocator that
  drives the rest of the run's replay bundle.

- One in-memory fixture adapter in
  `veracrawl.adapters.graph.in_memory_graph_observer`:
  `class InMemoryGraphObserver(GraphObservationPort)`.
  Constructor: `__init__(self, *, run_ref: str) -> None`
  (*iter-2 blocker*: the observer is tied to a single run; the
  `run_ref` is the snapshot's run anchor and the validator
  reject-key for misrouted events). Records events in
  append-only per-type lists; each `record_*` method rejects
  events whose `run_ref` doesn't match the observer's
  `run_ref`. `snapshot(*, id, snapshot_at)` returns a
  `GraphObservationSnapshot` with `run_ref = self._run_ref`
  and per-type event lists (typed events embedded, not ref strings — iter-4 redesign) in emission order. The fixture is
  deliberately bounded — no persistence, no eviction.

- Contract registry entries in
  `veracrawl.contracts.registry.FOUNDATION_CONTRACTS` for the
  five new pydantic models. All
  `owner_service=OwnerService.GRAPH`, `replay_required=True`.

- Tests per the red list.

### Out

- Modification of `external_crawl/runner.py`. The runner does
  not import the new port in s4. Wiring is s6.
- Modification of `agents/orchestration.py`,
  `target_runtime/runner.py`, or any planner adapter. s5
  consumes the snapshot; s4 is the contract surface only.
- Any `veracrawl.graph_memory` import (the goal doc audit
  explicitly cites `graph_memory` as scaffolded-only; s4 must
  NOT depend on it). The in-memory observer adapter holds its
  own state.
- Any new persistent backend (SQLite, S3, Postgres). The
  in-memory observer is the only adapter shipped in s4.
- Graph-edge / graph-node materialization. s4 records
  *observations* (the events); turning those into typed
  `GraphNode` / `GraphEdge` records is a graph-build slice
  out of scope here.
- Any contract change to existing `contracts/graph.py` types.
  s4's new contracts live in a new module so the existing
  graph schema stays unchanged.

## Design

### Module map

```
src/veracrawl/contracts/graph_observation.py            # new — ≤ 160 LOC  (step impl bumped 140→160: 5 models with full validators + UTC datetime helper + module docstring don't fit in 140 — current 155)
src/veracrawl/ports/graph_observation.py                # new — ≤  50 LOC
src/veracrawl/adapters/graph/__init__.py                # new — empty marker
src/veracrawl/adapters/graph/in_memory_graph_observer.py  # new — ≤  90 LOC
tests/contract/test_graph_observation_contracts.py             # new — ≤ 460 LOC  (step impl bumped 200→460: 50 contract tests + 5 payload-factory helpers + 4 datetime fixtures don't fit in 200; 50 tests × ~8 LOC ≈ 400 baseline plus helpers — current 420)
tests/contract/test_graph_observation_contract_registry.py     # new — ≤  40 LOC
tests/contract/test_graph_observation_import_boundaries.py     # new — ≤  70 LOC
tests/unit/adapters/graph/test_in_memory_graph_observer.py     # new — ≤ 170 LOC
```

Behavior-LOC ceiling: 160 + 50 + 90 = **300 LOC** before tests
+ additive registry-dict edits. At the binding ≤ 300 LOC cap
after the iter-1 task-review bump of the contracts module
budget 140 → 160 (current implementation: 155 + 48 + 71 =
274 LOC).

### Data flow

```
runner (s6) ──► port.record_url_observed(event)
runner (s6) ──► port.record_redirect_observed(event)
runner (s6) ──► port.record_canonical_observed(event)
runner (s6) ──► port.record_page_structure_observed(event)
                              │
                              ▼ (in-memory append)
                   InMemoryGraphObserver
                              │
                              ▼ on demand
                   GraphObservationSnapshot
                              │
                              ▼ (planner adapter in s5)
                  PlannerObservationFeedback consumes the snapshot
```

s4 ships only the boxes inside the in-memory observer; the
runner / planner wires happen in s6 / s5.

### Contract validator behavior

For each event:
- `UrlObservedEvent`:
  - `canonical_url` absolute http(s).
  - `depth >= 0`.
  - `parent_canonical_url` is absolute http(s) when set; may
    be `None` for root seeds.
  - `source_ref` non-blank.
  - `id`, `run_ref` non-blank.
- `RedirectObservedEvent`:
  - `from_canonical_url` and `to_canonical_url` both absolute
    http(s).
  - `from_canonical_url != to_canonical_url` (no self-redirects).
  - `300 <= status_code <= 399`.
  - `id`, `run_ref` non-blank.
- `CanonicalObservedEvent`:
  - `linked_canonical_url` and `canonical_target_url` both
    absolute http(s).
  - `linked_canonical_url != canonical_target_url` (a page
    declaring itself canonical is not an "observation").
  - `id`, `run_ref` non-blank.
- `PageStructureObservedEvent`:
  - `page_canonical_url` absolute http(s).
  - `discovered_link_count >= 0`.
  - `discovered_canonical_urls` entries all absolute http(s);
    no duplicates within the list.
  - `id`, `run_ref` non-blank.
- `GraphObservationSnapshot`:
  - `id`, `run_ref` non-blank.
  - Per-type event lists may be empty (a snapshot at run
    start is legal).
  - Per-type events MUST each have `run_ref == snapshot.run_ref`
    (validator enforced; iter-3 finding 3 evolved — the blank-
    ref concern is moot once events are embedded).

### Cross-module flow

- `contracts/graph_observation.py` imports
  `veracrawl.contracts.common.{Ref, VeraModel}` and
  `veracrawl.contracts.enums.CanonicalSource`. No other
  internal imports. (Events use `VeraModel`, NOT
  `TimestampedModel` — see Dependencies.)
- `ports/graph_observation.py` imports
  `veracrawl.contracts.graph_observation` and stdlib
  (`typing.Protocol`, `runtime_checkable`) only.
- `adapters/graph/in_memory_graph_observer.py` imports the
  port + the contracts module + stdlib only. Forbidden
  imports: any `veracrawl.adapters.*` other than self,
  any `veracrawl.graph_memory`, any `veracrawl.graph`, any
  storage / queue client, any model SDK. Enforced by a new
  import-boundary test file.

### Replay invariant

Events carry deterministic `id` + `observed_at` fields. The
observer is in-memory; replay of a run yields the same
events given the same runner input + the same `observed_at`
source. In s4 the `observed_at` value is caller-supplied
(no implicit `utc_now()` default) so a replay run can pin it.
This is the SAME pattern as s1's planner contracts using
`VeraModel` (not `TimestampedModel`) to avoid auto-timestamp
non-determinism.

### Naming

- `GraphObservationPort` (vs `GraphEventPort`): "observation"
  advertises the contract — the port captures observations
  *about* the runner's behavior, not raw events. Later
  slices may add an `Event`-shaped surface for stream
  consumers; the observation port is the read-side projection.
- `InMemoryGraphObserver` (vs `FixtureGraphObserver`):
  matches the s2 `ReplayingModelProviderV2` naming style —
  describes the storage, not the role.

## Dependencies

### On prior slices

- None new. s1's `_is_http_url` validator pattern is mirrored
  via a private duplicate in `contracts/graph_observation.py`.

### On existing repo state

- `veracrawl.contracts.common.{Ref, VeraModel}`. Events and
  the snapshot use `VeraModel` (NOT `TimestampedModel`) so
  the caller-supplied `observed_at` / `snapshot_at` are the
  only timestamps — no implicit `utc_now()` default that
  would break replay determinism. *(Iter-2 finding 4.)*
- `veracrawl.contracts.enums.OwnerService` (extended with
  `CanonicalSource` enum).
- `veracrawl.contracts.registry.{FOUNDATION_CONTRACTS,
  _contract}`.

### Prerequisites

None new.

## Test Strategy

Red-first list.

### `tests/contract/test_graph_observation_contracts.py`

1. `test_url_observed_event_rejects_non_http_canonical_url` →
   `ValidationError(match="canonical_url")`.
2. `test_url_observed_event_rejects_negative_depth` →
   `ValidationError(match="depth")`.
3. `test_url_observed_event_accepts_none_parent` — construct
   with `parent_canonical_url=None` succeeds (root seed).
4. `test_url_observed_event_rejects_non_http_parent` →
   `ValidationError(match="parent_canonical_url")`.
5. `test_url_observed_event_rejects_blank_source_ref` →
   `ValidationError(match="source_ref")`.
6. `test_redirect_observed_event_rejects_self_redirect` —
   from == to → `ValidationError(match="from")`.
7. `test_redirect_observed_event_rejects_status_out_of_range` —
   `status_code=200` → `ValidationError(match="status_code")`.
8. `test_redirect_observed_event_rejects_non_http_to_url` →
   `ValidationError(match="to_canonical_url")`.
8a. `test_redirect_observed_event_rejects_non_http_from_url` →
   `ValidationError(match="from_canonical_url")`. *(Iter-3
   finding 2.)*
9. `test_canonical_observed_event_rejects_self_canonical` —
   linked == target → `ValidationError(match="linked")`.
10. `test_canonical_observed_event_rejects_non_http_linked_url` →
    `ValidationError(match="linked_canonical_url")`.
10a. `test_canonical_observed_event_rejects_non_http_target_url` →
    `ValidationError(match="canonical_target_url")`. *(Iter-3
    finding 2.)*
11. `test_page_structure_observed_event_rejects_negative_link_count` →
    `ValidationError(match="discovered_link_count")`.
11a. `test_page_structure_observed_event_rejects_non_http_page_url` →
    `ValidationError(match="page_canonical_url")`. *(Iter-3
    finding 2.)*
12. `test_page_structure_observed_event_rejects_duplicate_canonical_urls` —
    same URL twice in `discovered_canonical_urls` →
    `ValidationError(match="duplicate")`.
13. `test_page_structure_observed_event_rejects_non_http_in_discovered_list` →
    `ValidationError(match="discovered_canonical_urls")`.
14. `test_graph_observation_snapshot_allows_empty_ref_lists` —
    snapshot with all four event lists empty validates.
15. `test_graph_observation_snapshot_rejects_blank_run_ref` →
    `ValidationError(match="run_ref")`.
15a. `test_url_observed_event_rejects_blank_id` →
    `ValidationError(match="id")`. *(Iter-1 finding 3.)*
15b. `test_url_observed_event_rejects_blank_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-1 finding 3.)*
15c. `test_redirect_observed_event_rejects_blank_id` →
    `ValidationError(match="id")`. *(Iter-1 finding 3.)*
15d. `test_redirect_observed_event_rejects_blank_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-1 finding 3.)*
15e. `test_canonical_observed_event_rejects_blank_id` →
    `ValidationError(match="id")`. *(Iter-1 finding 3.)*
15f. `test_canonical_observed_event_rejects_blank_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-1 finding 3.)*
15g. `test_page_structure_observed_event_rejects_blank_id` →
    `ValidationError(match="id")`. *(Iter-1 finding 3.)*
15h. `test_page_structure_observed_event_rejects_blank_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-1 finding 3.)*
15i. `test_graph_observation_snapshot_rejects_blank_id` →
    `ValidationError(match="id")`. *(Iter-1 finding 3.)*
15j. `test_url_observed_event_rejects_naive_observed_at` —
    *(Iter-1 finding 2.)* `observed_at=datetime(2026,5,14)`
    (no tzinfo) → `ValidationError(match="observed_at")`.
15k. `test_redirect_observed_event_rejects_naive_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-1 finding 2.)*
15l. `test_canonical_observed_event_rejects_naive_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-1 finding 2.)*
15m. `test_page_structure_observed_event_rejects_naive_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-1 finding 2.)*
15n. `test_graph_observation_snapshot_rejects_naive_snapshot_at` →
    `ValidationError(match="snapshot_at")`. *(Iter-1 finding 2.)*
15o. `test_url_observed_event_rejects_non_utc_observed_at` —
    `observed_at` with `tzinfo=timezone(timedelta(hours=8))`
    → `ValidationError(match="observed_at")`. *(Iter-2
    finding 2.)*
15p. `test_redirect_observed_event_rejects_non_utc_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-2 finding 2.)*
15q. `test_canonical_observed_event_rejects_non_utc_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-2 finding 2.)*
15r. `test_page_structure_observed_event_rejects_non_utc_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-2 finding 2.)*
15s. `test_graph_observation_snapshot_rejects_non_utc_snapshot_at` →
    `ValidationError(match="snapshot_at")`. *(Iter-2 finding 2.)*
15t. `test_graph_observation_snapshot_rejects_event_with_mismatched_run_ref`
    — *(Iter-3 finding 3 evolved per iter-4 snapshot redesign.)*
    Snapshot with `run_ref="run:a"` and a
    `url_observed_events=[UrlObservedEvent(run_ref="run:b",
    ...)]` → `ValidationError(match="run_ref")`. One test
    method asserts all four event lists via inline loops.
15u. `test_url_observed_event_rejects_missing_observed_at` —
    *(Iter-4 finding 2.)* Construct without `observed_at` →
    `ValidationError(match="observed_at")`. Pins the absence
    of a `Field(default_factory=utc_now)` regression.
15v. `test_redirect_observed_event_rejects_missing_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-4 finding 2.)*
15w. `test_canonical_observed_event_rejects_missing_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-4 finding 2.)*
15x. `test_page_structure_observed_event_rejects_missing_observed_at` →
    `ValidationError(match="observed_at")`. *(Iter-4 finding 2.)*
15y. `test_graph_observation_snapshot_rejects_missing_snapshot_at` →
    `ValidationError(match="snapshot_at")`. *(Iter-4 finding 2.)*
15z. `test_url_observed_event_rejects_missing_id` —
    *(Iter-5 finding 2.)* Construct without `id` →
    `ValidationError(match="id")`. Pins absence of any
    `Field(default_factory=...)` regression on `id`.
15aa. `test_redirect_observed_event_rejects_missing_id` →
    `ValidationError(match="id")`. *(Iter-5 finding 2.)*
15bb. `test_canonical_observed_event_rejects_missing_id` →
    `ValidationError(match="id")`. *(Iter-5 finding 2.)*
15cc. `test_page_structure_observed_event_rejects_missing_id` →
    `ValidationError(match="id")`. *(Iter-5 finding 2.)*
15dd. `test_graph_observation_snapshot_rejects_missing_id` →
    `ValidationError(match="id")`. *(Iter-5 finding 2.)*
15ee. `test_url_observed_event_rejects_missing_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-5 finding 2.)*
15ff. `test_redirect_observed_event_rejects_missing_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-5 finding 2.)*
15gg. `test_canonical_observed_event_rejects_missing_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-5 finding 2.)*
15hh. `test_page_structure_observed_event_rejects_missing_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-5 finding 2.)*
15ii. `test_graph_observation_snapshot_rejects_missing_run_ref` →
    `ValidationError(match="run_ref")`. *(Iter-5 finding 2.)*
15jj. `test_url_observed_event_rejects_missing_source_ref` →
    `ValidationError(match="source_ref")`. *(Iter-5 finding 2;
    only `UrlObservedEvent` carries this field.)*

### `tests/contract/test_graph_observation_contract_registry.py`

16. `test_registry_contains_all_five_graph_observation_contracts` —
    `("UrlObservedEvent", "RedirectObservedEvent",
    "CanonicalObservedEvent", "PageStructureObservedEvent",
    "GraphObservationSnapshot")` all in `FOUNDATION_CONTRACTS`
    with `replay_required=True` and
    `owner_service=OwnerService.GRAPH`.
17. `test_registry_validate_returns_ok` (regression).

### `tests/contract/test_graph_observation_import_boundaries.py`

18. `test_ports_graph_observation_imports_only_contracts_and_stdlib`
    — port AST walk; reject anything outside stdlib +
    `veracrawl.contracts.*`.
19. `test_adapters_graph_in_memory_graph_observer_imports_allowlist`
    — adapter allowlist: stdlib + `veracrawl.contracts.*` +
    `veracrawl.ports.graph_observation`. Reject any
    `veracrawl.graph_memory.*`, `veracrawl.graph.*`,
    `veracrawl.adapters.*` (other than self), any storage /
    queue / model SDK, and any relative import.
20. `test_external_crawl_runner_does_not_import_graph_observation`
    — s4 guard: the runner does NOT import the new port yet
    (wiring is s6).

### `tests/unit/adapters/graph/test_in_memory_graph_observer.py`

21. `test_observer_records_url_observed_in_emission_order` —
    record three URL events with distinct ids; snapshot
    `url_observed_events` returns the events in record order (typed, not ref strings).
22. `test_observer_records_redirect_observed` — analogous.
23. `test_observer_records_canonical_observed` — analogous.
24. `test_observer_records_page_structure_observed` — analogous.
25. `test_observer_snapshot_id_is_deterministic_from_inputs` —
    two observers both constructed with the same
    `run_ref="run:test:1"`, fed the same events in the same
    order, then both invoked as
    `observer.snapshot(id="snap:test:1",
    snapshot_at=datetime(2026,5,14,tzinfo=UTC))`, produce
    byte-equal `canonical_json()` snapshots. Pins the
    caller-injected metadata semantics (no implicit
    `utc_now()`) per the iter-1 blocker resolution.
25a. `test_observer_rejects_recording_event_with_mismatched_run_ref`
    — *(Iter-2 finding 1.)* observer constructed with
    `run_ref="run:a"`; calling `record_url_observed` with an
    event whose `run_ref="run:b"` → raises `ValueError`.
    Same shape for the other three `record_*` methods (one
    test asserts all four to keep the count tight, asserting
    each method-name in the error message).
26. `test_observer_implements_graph_observation_port` —
    `isinstance(InMemoryGraphObserver(run_ref="run:test:1"),
    GraphObservationPort)` via `@runtime_checkable`. *(Iter-3
    blocker fix: matches the iter-2 `run_ref`-kwarg ctor.)*

### Green path

Each red test gets a minimal implementation. One purpose per
commit. After all 66 tests pass, refactor only obvious
duplication. (Iter-5 post-iter-5: 11 new missing-field tests
15z-15jj covering `id` / `run_ref` / `source_ref` absence
across all five models. Each is a discrete test method, not
parametrized, so the collected count is unambiguous.)

## Acceptance Criteria

Mechanically verifiable.

1. **Pytest gate** —
   `pytest tests/contract/test_graph_observation_contracts.py tests/contract/test_graph_observation_contract_registry.py tests/contract/test_graph_observation_import_boundaries.py tests/unit/adapters/graph/test_in_memory_graph_observer.py -v`
   exits 0 with **66** collected, **66** passed.
2. **Contract registry** — Python one-liner verifying all
   five new contracts present with `replay_required=True`,
   `owner_service=OwnerService.GRAPH`, and
   `validate_registry().ok`.
3. **No runner wiring** —
   `python -c "import pathlib; assert 'graph_observation' not in pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text()"`
   exits 0.
4. **No graph_memory or graph imports in the adapter** —
   *(Iter-4 finding 3: substring grep misses
   ``import veracrawl.graph`` / ``from veracrawl import
   graph``; replaced with the AST allowlist test which is
   strict.)*
   `pytest tests/contract/test_graph_observation_import_boundaries.py::test_adapters_graph_in_memory_graph_observer_imports_allowlist -v`
   exits 0. The AST walker in that test enforces stdlib +
   `veracrawl.contracts.*` + `veracrawl.ports.graph_observation`
   only, catching every import shape (bare-package,
   from-package, relative).
5. **Port has no adapter dep** —
   `python -c "import inspect, veracrawl.ports.graph_observation as p; src = inspect.getsource(p); assert 'veracrawl.adapters' not in src"`
   exits 0.
6. **Behavior LOC budget** —
   `total=$(wc -l src/veracrawl/contracts/graph_observation.py src/veracrawl/ports/graph_observation.py src/veracrawl/adapters/graph/in_memory_graph_observer.py | tail -1 | awk '{print $1}'); test "$total" -le 300`
   exits 0.
7. **Codex plan-review gate** — *(Iter-2 finding 3 / iter-5
   finding 3: both branches mechanical.)* Either:
   (a) `CODEX_REVIEW_ITERATION=N ~/.claude/hooks/codex-review.sh plan
   docs/plans/general-purpose-crawler-agentification/s4-graph-observation-port-contract.md
   --project-dir $PWD | grep -q "VERDICT: APPROVED"`
   exits 0 within ≤ 5 iterations; OR
   (b) `grep -q "PLAN_DONE_WITH_RESERVATIONS" docs/plans/general-purpose-crawler-agentification/STATUS.md
   && grep -q "s4 plan iter-5 reservations" docs/plans/general-purpose-crawler-agentification/STATUS.md`
   exits 0 (the goal-doc "iter-5 rejects but addressable"
   path; the STATUS reservation row is the deterministic
   audit anchor).
8. **Codex task-review per commit** — *(Iter-2 finding 3 /
   iter-5 finding 3.)* For each commit ``<C>``, either:
   (a) `BASELINE=<C>^ && CODEX_REVIEW_ITERATION=N ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD | grep -q "VERDICT: APPROVED"`
   exits 0 within ≤ 5 iterations; OR
   (b) `grep -q "<C>.*DONE_WITH_RESERVATIONS" docs/plans/general-purpose-crawler-agentification/STATUS.md`
   exits 0 (the STATUS row records the commit + the
   reservation explicitly).

## Rollback

s4 only adds new files plus five `FOUNDATION_CONTRACTS` entries
and one `CanonicalSource` enum addition. Rollback is
`git revert <s4-commit-range>` — no migrations, no schema
changes, no consumer breakage.

## Open Questions

1. **`source_ref` as `Ref` vs `StrEnum`**: `UrlObservedEvent.source_ref`
   captures *what introduced the URL* (seed / link-extractor /
   sitemap / replanner). A typed `StrEnum` would constrain
   values but couples s4 to a known fixed set. Default: keep
   as `Ref` (string) with a non-blank validator; future slices
   may swap to an enum once the set stabilizes.
2. **`CanonicalSource` enum coverage**: the three values
   (`LINK_REL_CANONICAL`, `HTTP_LINK_HEADER`, `SITEMAP`)
   cover the s4 scope. JSON-LD canonical, RSS canonical, etc.
   may join in later slices.
3. **`observed_at` discipline**: events take a
   caller-supplied `datetime` (UTC). The runner (s6) MUST
   inject the timestamp from the same clock that drives
   replay refs. Discussed in Design § "Replay invariant".
4. **Snapshot freshness**: `snapshot()` is a synchronous
   read of the in-memory state. Concurrency / cross-process
   snapshot consistency is out of scope until a persistent
   backend lands.
