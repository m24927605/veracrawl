# s3 — `ExternalCrawlRunner` wires `CrawlPlannerPort` (planned-seed scheduling + replay refs)

## Status

| Iter | Date (UTC) | Verdict  | Findings (one-liner) | Resolution |
|------|------------|----------|----------------------|------------|
| 1    | 2026-05-14 | REJECTED | 2 blockers (FIFO frontier can't honor priority hints; replay consumer deferred) + 2 majors (synthetic lineage refs; `adapter_priors` claimed but not consumed) + 1 minor (AC6 not executable). | Plan revised to v2: scope narrowed to **planned-seed ordering only**; `frontier_priority_hints` and `adapter_priors` are recorded into the run report for future consumers but NOT applied by s3 (FIFO frontier + single-adapter fetcher = wrong layer to consume them). Synthetic-ref default builder dropped — `planner` and `plan_request_builder` must both be provided or both omitted. New unit test 13-replay demonstrates same-slice runner-level byte-equal replay via `ReplayingModelProviderV2` injected into `LlmCrawlPlanner`. AC6 rewritten as a shell assertion. Topic README s3 row narrowed. |
| 2    | 2026-05-14 | REJECTED | 1 blocker + 3 majors + 1 minor: (blocker) replay test asserted only 2 of 5 plan_decision_* report keys; missed `planned_seeds`/`frontier_priority_hints`/`adapter_priors` which the LLM planner ALSO projects from `parsed_output`. (major) AC4 referenced non-existent `tests/unit/test_external_crawl_runner*.py`; actual existing tests are under `tests/integration/`. (major) `plan_decision_planned_seeds` claimed "actually enqueued" but recorded pre-enqueue sorted URLs (frontier can reject). (major) AC6 LOC budget used `HEAD~1..HEAD` — only checks latest commit, splits across commits bypass the cap. (minor) Open Question 1 about topic README was stale (already updated). | Plan revised to v3: (1) test 13-replay extended to assert ALL 5 `plan_decision_*` keys are byte-equal; (2) AC4 path corrected to `tests/integration/test_external_crawl_runner.py`; (3) report field renamed `plan_decision_planned_seeds` → `plan_decision_planned_seed_order` and re-documented as "the planner's intended order (not admission outcomes)"; (4) AC6 uses the s3 baseline commit `4283766` (s2 closure) instead of `HEAD~1`; (5) Open Question 1 closed (README is already updated). |
| 3    | 2026-05-14 | REJECTED | 1 blocker + 1 major: (blocker) Design §Replay invariant still listed only 2 keys, while the red list 13-replay claimed all 5 — an implementer following the Design section could leave the prior replay blocker intact. (major) AC6 only checked `runner.py` LOC delta; an implementer could move behavior into a new production module and bypass the cap. | Plan revised to v4: Design §Replay invariant rewritten to enumerate ALL 5 keys (matching red test 13 verbatim). AC6 scope expanded to `src/veracrawl/**` (any new production source file counts toward the ≤50 LOC s3 delta). |
| 4    | 2026-05-14 | REJECTED | 1 blocker: `LlmPlanProposal.extraction_strategy_refs` is LLM-derived (`LlmCrawlPlanner._project` projects it into `PlanDecision.extraction_strategy_refs`), but s3's report only persisted 5 keys and red test 13 only asserted 5 — `extraction_strategy_refs` was an uncovered model-output field. | Plan revised to v5: report adds 6th key `plan_decision_extraction_strategy_refs`; new red test 10a (`test_runner_records_extraction_strategy_refs_without_applying`); replay test 13 extended to assert all 6 keys; absence test 12 extended to all 6 keys. Unit test count 13 → 14. |
| 5    | 2026-05-14 | REJECTED → DONE_WITH_RESERVATIONS via post-iter-5 follow-up | 1 major + 2 minors: (major) stable-tie order specified but no equal-priority red test pinned it. (minor) Design §Replay invariant prose still said "all 5" while scope/red list now require 6. (minor) topic README s3 row still listed 5 keys, missing `extraction_strategy_refs`. | Post-iter-5 follow-up landed in this same plan revision (no re-review per goal-doc workflow): new red test 6a `test_runner_preserves_emission_order_on_priority_ties` with equal priorities and non-alphabetical input order; Design §Replay invariant prose corrected to "all 6"; topic README s3 row rewritten to enumerate all 6 persisted keys + add the extraction-strategy execution reference to s10. Unit test count 14 → 15; AC1 collected count 14 → 15. Plan recorded as `PLAN_DONE_WITH_RESERVATIONS`. |

Codex plan-review gate via the documented hook
`~/.claude/hooks/codex-review.sh plan <plan-file> --project-dir $PWD`
(Reservation 2 discharged in s1 prereq landing). ≤ 5 iterations.

## Why

- **AGENTS.md hard constraint — general-purpose**: s1 + s2 shipped
  `CrawlPlannerPort` + two adapters. Until the runner consumes the
  port, the agent planning loop is half-built — the contract surface
  exists but no runtime path exercises it. s3 closes the loop by
  wiring the port into `ExternalCrawlRunner` so a real crawl run goes
  through `planner.plan(request)` before any URL gets enqueued.
- **AGENTS.md hard constraint — low coupling**: the runner is the
  composition root. s3 wires it via constructor injection (an
  optional `planner: CrawlPlannerPort` parameter). The runner imports
  `veracrawl.ports.crawl_planner` only — no concrete adapter is
  imported by the runner itself.
- **Goal doc capability 1**: *"Agent planning loop wired into
  `ExternalCrawlRunner`"*. s3 is the *runtime-spine wiring* stage
  in the goal doc's
  `contract+port → fixture-mode adapter → production adapter →
  runtime-spine wiring → live integration test` decomposition.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`external_crawl/
  runner.py` imports zero graph symbols"* and *"no
  objective→plan→adaptive-frontier loop"*. s3 begins closing that
  gap by introducing the objective→plan→frontier loop.
- **Iter-1 narrowing rationale**: the FIFO `ExternalCrawlFrontier`
  cannot honor per-URL `frontier_priority_hints` and the single-
  fetcher runner cannot honor per-adapter `adapter_priors` without
  significant scope expansion (priority queue + multi-adapter
  dispatch). s3 scopes itself to **planned-seed ordering** — the
  one consumption pattern the existing frontier supports — and
  *records* the unused hint / prior refs in the run report so a
  future slice that adds the missing infrastructure can pick them
  up without re-running the planner.

## Scope

### In

- **Two new constructor parameters on `ExternalCrawlRunner`**:
  - `planner: CrawlPlannerPort | None = None`.
  - `plan_request_builder: Callable[[CrawlJobSpec, Path], PlanRequest] | None = None`.

  Both are accepted together or omitted together. The runner
  raises `ValueError` at construction if exactly one is provided
  (no silent synthetic defaults — *iter-1 finding 3*). When both
  are `None`, the runner falls back to the legacy
  `spec.seed_urls` enqueue path (existing behavior preserved).

- **Planner invocation in `ExternalCrawlRunner.run`**: at the start
  of `run()`, before the existing seed-enqueue loop:
  1. If `self._planner is None`, skip planning entirely.
  2. Otherwise call
     `plan_request = self._plan_request_builder(self._spec, self._run_root)`
     and `decision = self._planner.plan(plan_request)`.
  3. Sort `decision.planned_seeds` descending by
     `priority_score` (stable sort; ties broken by emission
     order).
  4. Enqueue each `PlannedSeed.canonical_url` via
     `self._frontier.enqueue(seed.canonical_url, depth=0,
     parent_canonical_url=None)` — the FIFO frontier turns the
     sort order into fetch order.

- **`PlanDecision` recorded into `run_report.json`**: add to the
  report dict (under existing report-writing code):
  - `plan_decision_ref: str` (the decision's `id`).
  - `plan_decision_replay_refs: list[str]` (`decision.replay_refs`
    verbatim — the s2 7-entry list, including the LLM's
    `raw_response_ref` if planning ran through the LLM adapter).
  - `plan_decision_frontier_priority_hints: list[dict]`
    (`[h.model_dump() for h in decision.frontier_priority_hints]`)
    — recorded but not applied; future priority-queue-frontier
    slice consumes them.
  - `plan_decision_adapter_priors: list[dict]`
    (`[p.model_dump() for p in decision.adapter_priors]`) —
    recorded but not applied; future multi-adapter-dispatch slice
    consumes them.
  - `plan_decision_planned_seed_order: list[str]` (the sorted
    seed URLs the planner emitted — the *intended* order, NOT
    admission outcomes; the frontier's own `events.jsonl`
    records admission/skip per URL). *(Iter-2 finding 3.)*
  - `plan_decision_extraction_strategy_refs: list[str]`
    (`list(decision.extraction_strategy_refs)`). *(Iter-4
    finding 1.)* This field is LLM-derived in s2's
    `LlmCrawlPlanner._project`, so it MUST land in the report
    + the replay-consumer test, same as the other four
    LLM-derived keys.

  When `planner=None`, all six keys are **omitted** from the
  report (preserve legacy report shape exactly).

- **Tests per the red list below.**

### Out

- Frontier-priority application. The FIFO
  `ExternalCrawlFrontier` cannot honor per-URL priority hints
  without a priority queue. *(Iter-1 blocker 1.)* `frontier_priority_hints`
  is recorded into the report as future-consumer data; it does
  **not** alter fetch order in s3. A later slice that introduces
  a priority-queue frontier consumes the recorded hints.
- Adapter-prior consumption. The runner uses one
  `CrawlHttpFetcherPort` at a time; multi-adapter dispatch
  (HTTP / sitemap / RSS / browser) is a separate slice. *(Iter-1
  major 4.)* `adapter_priors` is recorded into the report as
  future-consumer data.
- Synthetic-default `plan_request_builder`. Production callers
  thread real lineage refs; s3 does not invent placeholders.
  *(Iter-1 major 3.)*
- Mid-run re-invocation of the planner on frontier-empty
  events. *(s5 / s6 territory.)*
- Live LLM planning. The integration test uses s1's
  `DeterministicCrawlPlanner`. Live LLM requires s2.1
  (provider-artifact wiring).
- New port introductions. s3 only consumes the existing
  `veracrawl.ports.crawl_planner`.
- A `FrontierPriorityShim` module. *(Iter-1 blocker 1 — the
  shim would have been a no-op against the FIFO frontier.)*

## Design

### Module map

```
src/veracrawl/external_crawl/runner.py                              # modified — Δ ≤  50 LOC
tests/unit/external_crawl/test_runner_plans_with_crawl_planner.py   # new      — ≤ 220 LOC
tests/integration/test_runner_plans_against_httpbin.py              # new      — ≤  80 LOC
```

Behavior-LOC ceiling: **≤ 50 LOC** runner delta. Well under
the binding ≤ 300 LOC cap.

### Data flow

```
ExternalCrawlRunner.run():
  │
  ├─► if self._planner is None: skip to legacy enqueue (current behavior)
  │
  ├─► plan_request = self._plan_request_builder(self._spec, self._run_root)
  │
  ├─► decision = self._planner.plan(plan_request)        # s1 deterministic OR s2 LLM
  │
  ├─► sorted_seeds = sorted(decision.planned_seeds,
  │                         key=lambda s: -s.priority_score)   # stable, ties → emission order
  │
  ├─► for seed in sorted_seeds:
  │     frontier.enqueue(seed.canonical_url, depth=0, parent_canonical_url=None)
  │
  ├─► (existing fetch / extract / discover loop runs unchanged)
  │
  └─► run_report.update({
        "plan_decision_ref": decision.id,
        "plan_decision_replay_refs": list(decision.replay_refs),
        "plan_decision_frontier_priority_hints": [h.model_dump() for h in decision.frontier_priority_hints],
        "plan_decision_adapter_priors": [p.model_dump() for p in decision.adapter_priors],
        "plan_decision_planned_seed_order": [s.canonical_url for s in sorted_seeds],
        "plan_decision_extraction_strategy_refs": list(decision.extraction_strategy_refs),
      })
```

### Cross-module flow

- `external_crawl/runner.py` adds imports:
  - `veracrawl.contracts.crawl_planner` (for `PlanDecision` /
    `PlannedSeed` / `PlanRequest` typing).
  - `veracrawl.ports.crawl_planner` (for `CrawlPlannerPort`).
  - `pathlib.Path` (already imported), `collections.abc.Callable`
    (already imported via `Callable` typing usage).

  Forbidden imports: any adapter module
  (`veracrawl.adapters.planning.*`,
  `veracrawl.adapters.model_providers.*`). The existing
  `tests/contract/test_crawl_planner_import_boundaries.py`'s
  test 22 (which rejected ANY `crawl_planner` import in the
  runner) is **replaced** with test 22a that accepts
  `veracrawl.contracts.crawl_planner` and
  `veracrawl.ports.crawl_planner` but rejects any
  `veracrawl.adapters.*`. *(Test-22 replacement landed in
  step 5 of s3 if test-file delta is desired; otherwise inline
  with the runner change.)*

### Replay invariant (same-slice consumer wiring)

s2 already shipped `ReplayingModelProviderV2` as the in-product
replay consumer at the *model-provider* layer. s3 introduces a
new code path — the *runner* now produces non-deterministic
artifacts (the planner's `PlanDecision` flowing into the run
report) when wired with the LLM planner.

**Same-slice consumer wiring** (*iter-1 blocker 2; iter-2
blocker 1 extends the scope to all 5 plan_decision_* keys*):

s3 ships unit test **13-replay**
`test_runner_run_report_is_byte_identical_when_planner_uses_replaying_model_provider`.
Flow:
1. Run 1: a runner is configured with
   `LlmCrawlPlanner(model_provider=FakeModelProviderV2(canned),
   ...)`. After the run, capture all 6
   `plan_decision_*` keys from `run_report.json`:
   `plan_decision_ref`, `plan_decision_replay_refs`,
   `plan_decision_frontier_priority_hints`,
   `plan_decision_adapter_priors`,
   `plan_decision_planned_seed_order`,
   `plan_decision_extraction_strategy_refs`. Capture `canned`
   (the canned `ProviderResponse`).
2. Run 2: a new runner is configured with
   `LlmCrawlPlanner(model_provider=ReplayingModelProviderV2(
   {provider_request_id: canned}), ...)`. After the run, read
   all 6 keys from the second `run_report.json`.
3. Assert ALL 6 keys are byte-equal across the two runs:
   `plan_decision_ref`, `plan_decision_replay_refs`,
   `plan_decision_frontier_priority_hints`,
   `plan_decision_adapter_priors`,
   `plan_decision_planned_seed_order`,
   `plan_decision_extraction_strategy_refs`. The
   `LlmCrawlPlanner` projects four of those keys from
   `ProviderResponse.parsed_output` directly
   (`adapter_priors`, `frontier_priority_hints`,
   `planned_seed_order`, `extraction_strategy_refs`), so each
   is part of the non-deterministic artifact surface the
   replay consumer must reproduce.

This is the in-slice consumer: the recorded `replay_refs` from
run 1, when threaded through `ReplayingModelProviderV2`,
produce byte-equal run-report planner artifacts in run 2.

### Naming

- `plan_request_builder` (vs `plan_request_factory`): mirrors
  the existing `link_extractor`, `pdf_extractor`, `robots_port`,
  `rate_limiter` constructor parameters — named for what they
  produce.

## Dependencies

### On prior slices

- s1 (`CrawlPlannerPort` + `PlanRequest` / `PlanDecision` /
  `PlannedSeed` / `AdapterPrior` / `FrontierPriorityHint`).
- s2 (`LlmCrawlPlanner` + `ReplayingModelProviderV2`). The
  integration test uses s1's `DeterministicCrawlPlanner`; the
  unit test 13-replay wires s2's `ReplayingModelProviderV2`
  for the same-slice replay-consumer demonstration.

### On existing repo state

- `veracrawl.external_crawl.runner.ExternalCrawlRunner` (modified).
- `veracrawl.external_crawl.frontier.ExternalCrawlFrontier`
  (read-only; FIFO behavior preserved).
- `veracrawl.contracts.crawl_job.CrawlJobSpec` (read-only).
- `veracrawl.contracts.crawl_planner` (read-only).
- `veracrawl.ports.crawl_planner` (read-only).

### Prerequisites

None new.

## Test Strategy

Red-first list. A small `_FakeCrawlPlanner` (records
`plan(request)` invocations, returns a configurable
`PlanDecision`) drives the unit tests. The replay-consumer
demo test wires the real `ReplayingModelProviderV2` from s2.

### `tests/unit/external_crawl/test_runner_plans_with_crawl_planner.py`

1. `test_runner_skips_planning_when_planner_is_none` — runner
   constructed without `planner` enqueues `spec.seed_urls`
   directly (current behavior preserved). The fake's call count
   is 0 because no fake is wired.
2. `test_runner_raises_when_planner_provided_without_builder` —
   `planner=fake` with `plan_request_builder=None` raises
   `ValueError` at construction.
3. `test_runner_raises_when_builder_provided_without_planner` —
   symmetric: `planner=None` with `plan_request_builder=fn`
   raises `ValueError`.
4. `test_runner_invokes_planner_before_enqueue` — fake planner
   records exactly one `plan(request)` call; frontier is
   non-empty after the call.
5. `test_runner_uses_caller_supplied_plan_request_builder` —
   custom callable returns a known `PlanRequest`; fake planner
   sees the custom request (no auto-synthesis).
6. `test_runner_enqueues_planned_seeds_in_priority_order` —
   fake planner returns 3 `PlannedSeed`s with priorities
   `[0.3, 0.9, 0.6]`. The runner enqueues in descending
   priority: URLs corresponding to `[0.9, 0.6, 0.3]`. Assertion:
   `frontier.events()` order matches.
6a. `test_runner_preserves_emission_order_on_priority_ties`
   — *(Iter-5 post-iter-5 follow-up; iter-5 finding 1)*. Fake
   planner returns 3 `PlannedSeed`s all with
   `priority_score=0.5` and canonical URLs
   `["https://b.example/", "https://a.example/",
   "https://c.example/"]` (deliberately NOT in alphabetical
   order). The runner's stable sort must preserve planner
   emission order: assertion enqueues match the input order
   `["https://b.example/", "https://a.example/",
   "https://c.example/"]`. This pins the "ties broken by
   emission order" invariant against a future regression that
   adds a secondary URL sort.
7. `test_runner_persists_plan_decision_ref_in_run_report` —
   after the run, `run_report["plan_decision_ref"] ==
   decision.id`.
8. `test_runner_persists_plan_decision_replay_refs_verbatim` —
   `run_report["plan_decision_replay_refs"] ==
   list(decision.replay_refs)`.
9. `test_runner_records_frontier_priority_hints_without_applying` —
   fake planner emits a `FrontierPriorityHint`; the runner
   records `[hint.model_dump()]` in
   `run_report["plan_decision_frontier_priority_hints"]` BUT
   the fetch order is **only** determined by planned-seed
   priority (hints are recorded-but-not-applied).
10. `test_runner_records_adapter_priors_without_applying` —
    `run_report["plan_decision_adapter_priors"] ==
    [p.model_dump() for p in decision.adapter_priors]`; the
    runner does not branch on adapter type (single-adapter
    fetcher path unchanged).
10a. `test_runner_records_extraction_strategy_refs_without_applying`
    — *(Iter-4 finding 1.)*
    `run_report["plan_decision_extraction_strategy_refs"] ==
    list(decision.extraction_strategy_refs)`; the runner does
    not branch on strategy refs (extraction strategy is s7
    territory).
11. `test_runner_records_planned_seed_order_in_sorted_order` —
    `run_report["plan_decision_planned_seed_order"]` matches
    the sorted seed URLs (the planner's intended order). The
    test does NOT claim these were all admitted by the
    frontier; the frontier's `events.jsonl` records admission
    outcomes separately.
12. `test_runner_omits_plan_decision_keys_when_planner_is_none` —
    none of the 6 `plan_decision_*` keys appear in
    `run_report` (`plan_decision_ref`, `_replay_refs`,
    `_frontier_priority_hints`, `_adapter_priors`,
    `_planned_seed_order`, `_extraction_strategy_refs`).
    (Pin the exact "absent vs `null`" choice: keys are
    **absent**.)
13. `test_runner_run_report_is_byte_identical_when_planner_uses_replaying_model_provider`
    — *(Iter-1 blocker 2; iter-2 blocker 1 — extended to all
    plan_decision_* keys; iter-4 blocker 1 — extended to the
    6th key extraction_strategy_refs)*. See Design § "Replay
    invariant". Asserts ALL SIX `plan_decision_*` keys are
    byte-equal across record + replay runs:
    `plan_decision_ref`, `plan_decision_replay_refs`,
    `plan_decision_frontier_priority_hints`,
    `plan_decision_adapter_priors`,
    `plan_decision_planned_seed_order`,
    `plan_decision_extraction_strategy_refs`. The
    `LlmCrawlPlanner` projects four of those keys from
    `ProviderResponse.parsed_output` directly, so each is part
    of the non-deterministic artifact surface that the replay
    consumer must reproduce byte-equal.

### `tests/integration/test_runner_plans_against_httpbin.py`

14. `test_runner_plans_with_deterministic_planner_against_httpbin`
    — `@pytest.mark.live`. Builds a runner with
    `DeterministicCrawlPlanner` + a tiny
    `plan_request_builder` that synthesizes a `PlanRequest`
    from `spec` + a `httpbin.org` seed. Run completes;
    `run_report.json` has `plan_decision_ref != None` and at
    least one document fetched. Test is intentionally light —
    its purpose is to prove the planner wiring path runs
    end-to-end against real HTTP.

### Import-boundary extension (in `tests/contract/test_crawl_planner_import_boundaries.py`)

The existing s1 test 22 forbids ANY `crawl_planner` import in
the runner. s3 lifts that restriction (the whole point of
this slice). Replace test 22 in-place with **test 22a**
`test_external_crawl_runner_imports_crawl_planner_only_via_contracts_and_ports`:

- Accept imports of `veracrawl.contracts.crawl_planner`
  (typing) and `veracrawl.ports.crawl_planner` (port).
- Reject ANY import under `veracrawl.adapters.*` (the runner
  must not depend on a specific adapter).
- Reject any relative import (consistent with s1's pattern).

Net pytest count in the import-boundary file stays at **5**
(replacement, not addition). *(Iter-1 minor: this is the
correction to test 22's semantics, not a new test.)*

### Green path

Each red test gets a minimal implementation. One purpose per
commit. After all 16 new tests + 5 import-boundary tests pass
(15 unit + 1 integration; the integration is `@pytest.mark.live`
and not in the default suite), refactor only obvious
duplication.

## Acceptance Criteria

Mechanically verifiable from a fresh checkout.

1. **Pytest gate (unit)** —
   `pytest tests/unit/external_crawl/test_runner_plans_with_crawl_planner.py -v`
   exits 0 with **15** collected, **15** passed. (Iter-5
   post-iter-5 added test 6a for priority-tie emission-order
   stability.)
2. **Pytest gate (live integration)** —
   `pytest tests/integration/test_runner_plans_against_httpbin.py -v -m live`
   exits 0 with **1** collected, **1** passed when run in an
   environment with network access. The non-`-m live` default
   suite skips it.
3. **Pytest gate (import-boundary file)** —
   `pytest tests/contract/test_crawl_planner_import_boundaries.py -v`
   exits 0 with **5** collected (test 22 replaced with 22a;
   count unchanged from s2).
4. **Runner regression suite** — *(Iter-2 finding 2: path
   corrected.)*
   `pytest tests/integration/test_external_crawl_runner.py -q`
   exits 0 with all existing tests still passing. The planner
   wiring is strictly additive: `planner=None` short-circuits
   to legacy behavior.
5. **No adapter imports in the runner** —
   `python -c "import pathlib; src = pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text(); assert 'from veracrawl.adapters' not in src and 'import veracrawl.adapters' not in src"`
   exits 0.
6. **Behavior LOC budget** — *(Iter-1 minor 5: deterministic
   assertion; iter-2 finding 4: slice-baseline diff; iter-3
   major 2: scope expanded to ALL `src/veracrawl/**` files so
   an implementer cannot move behavior into a new production
   module to bypass the cap.)*
   ```
   total=$(git diff 4283766..HEAD --numstat -- 'src/veracrawl/**' | awk '{added+=$1; removed+=$2} END {print added}')
   test "${total:-0}" -le 50
   ```
   exits 0. (`4283766` is the s2 closure commit — the slice
   baseline; net additions across the ENTIRE production source
   tree ≤ 50 lines for s3, mirroring the Design module-map
   declaration that the only behavior change is the
   `runner.py` delta.)
7. **Codex plan-review gate** —
   `~/.claude/hooks/codex-review.sh plan
   docs/plans/general-purpose-crawler-agentification/s3-runner-wires-crawl-planner.md
   --project-dir $PWD` returns `VERDICT: APPROVED` in ≤ 5
   iterations, OR `DONE_WITH_RESERVATIONS` per goal doc.
8. **Codex task-review per commit** — each commit passes
   `~/.claude/hooks/codex-review.sh task <BASELINE> --project-dir
   $PWD` in ≤ 5 iterations, or carries a recorded reservation.

## Rollback

s3 modifies `external_crawl/runner.py` additively (new optional
constructor params + a guarded planning block before the
existing enqueue loop). Rollback is `git revert <s3-commit-range>`
— the legacy enqueue path is preserved as the fall-through, so
reverting strips the planning block without touching the
existing crawl flow. No on-disk schema changes; the
`plan_decision_*` keys in `run_report.json` are additive and
absent when `planner=None`.

## Open Questions

1. ~~**Topic README update**~~ — *(Iter-2 minor 5: closed.)*
   The topic README s3 row has been updated to record-but-not-
   apply semantics; placeholder rows s3.1 (priority-queue
   frontier) + s3.2 (multi-adapter dispatch) are added. No
   further action required for s3.
2. **Synthetic refs for integration test 14**: the live test
   needs SOME `objective_ref` / `budget_ref` / etc. to satisfy
   the `PlanRequest` validator. Decision: the test's
   `plan_request_builder` synthesizes refs scoped to the test
   (`f"objective:test:{spec.id}"` etc.). This is test-only
   synthesis — explicit, not a default behavior — and does not
   re-introduce the iter-1 blocker.
3. **Future priority-queue frontier**: a follow-up slice can
   swap `ExternalCrawlFrontier` for a heap-based priority
   queue, then *apply* the recorded
   `plan_decision_frontier_priority_hints`. The recorded refs
   in the run report enable this without re-running the
   planner.
4. **Future multi-adapter dispatch**: a follow-up slice can
   route URLs to different fetcher adapters based on
   `plan_decision_adapter_priors`. The recorded refs enable
   this without re-running the planner.
