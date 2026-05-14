# s5 — `PlannerObservationFeedback` contract + deterministic feedback-aware planner

## Status

| Iter | Date (UTC) | Verdict | Findings (one-liner) | Resolution |
|------|------------|---------|----------------------|------------|
| 1    | 2026-05-14 | REJECTED | 1 blocker + 3 majors: (blocker) feedback provenance unbound — no tests required `feedback.run_ref == request.run_ref`, `feedback.id in request.observed_state_refs`, `feedback.id in decision.replay_refs`. (major) test 21's allowlist accepted all `veracrawl.contracts.*` — adapter could directly import `GraphObservationSnapshot` instead of going through `PlannerObservationFeedback`. (major) plan claimed structural feedback consumption but `page_neighbour_count_by_url` was derived-only — never affected `frontier_priority_hints`. (major) AC7/AC8 used prose for the APPROVED branch + literal `<C>` placeholder for task-review. | Plan revised to v2: 4 new provenance red tests (v2 enforces feedback↔request consistency); test 21's allowlist switched to explicit per-module allow (`contracts.common`, `contracts.crawl_planner`, `contracts.planner_observation_feedback`, `contracts.enums`) — rejects `contracts.graph_observation` and any other contract module. Hint rule extended: pages with `discovered_link_count ≥ 5` emit a `URL_PREFIX` hint with `+0.2` boost. AC7/AC8 rewritten as deterministic shell-grep checks. AC1 collected count 30 → 36 (4 provenance red tests 28/29/30/33 + 1 hub-page test 26 + 1 no-feedback replay-refs guard test 31, with re-numbering). |
| 2    | 2026-05-14 | REJECTED | 1 blocker + 2 majors + 1 minor: (blocker) prior hidden-coupling not closed — adapter could re-import `GraphObservationSnapshot` via the new feedback contract or reach into `feedback.snapshot.redirect_observed_events`; test 21's module-only allowlist would still pass. (major) tests 20/21 defined "stdlib" as "any top-level module not starting with `veracrawl.`", admitting `openai` / `httpx` / `langchain`. (major) AC8 used `git log master..HEAD`, which is vacuous on master; also excluded `registry.py`. (minor) topic README still describes s5 as taking a `GraphSnapshotRef` input. | Plan revised to v3: test 21 extended with two new AST checks — (i) `from veracrawl.contracts.planner_observation_feedback import …` names must be in `{PlannerObservationFeedback}` only (snapshot/event names rejected); (ii) any `Attribute` node with `attr == "snapshot"` in the adapter module is rejected. Tests 20/21 switch to explicit stdlib allowlist (concrete module names: `__future__`, `typing`, `collections.abc`, `re`, `hashlib`, `urllib.parse`). AC8 rewritten to walk commits from the s5-plan commit forward (subject prefix `s5:`) and to include `registry.py` + the 4 test files. README s5/s6 rows updated to use `PlannerObservationFeedback` + `observed_state_refs`. AC1 collected count 36 → 37 (one new AST test: snapshot-attribute guard; tests 20/21 stdlib tightening is in place, no count change). |
| 3    | 2026-05-14 | REJECTED | 1 blocker + 1 major + 1 minor: (blocker) hidden coupling STILL not closed — aliased `import veracrawl.contracts.planner_observation_feedback as pof` plus `pof.GraphObservationSnapshot` bypasses the per-name `ImportFrom` gate, and `getattr(feedback, "snapshot")` / `feedback.model_dump()["snapshot"]` bypass the `Attribute(attr="snapshot")` AST walk. (major) AC8 silently `continue`s any commit whose subject doesn't begin with `s5:` — an off-policy commit that touches `deterministic_crawl_planner_v2.py` is ignored, not failed. (minor) Open Questions referenced test 27 for hint ordering after the renumbering pushed it to test 28. | Plan revised to v4: **structural fix — drop the public `snapshot: GraphObservationSnapshot` field from `PlannerObservationFeedback`** entirely. Contract carries only `id`, `run_ref`, `redirect_neighbours`, `canonical_targets`, `page_neighbour_count_by_url`. The `derive_planner_observation_feedback(*, id, run_ref, snapshot)` helper validates `run_ref == snapshot.run_ref` at derivation time, then constructs the typed feedback. Contract module's only `graph_observation` reference is `TYPE_CHECKING`-only; the helper duck-types snapshot field access at runtime. Adapter test 21 extended to ban `Import` nodes for any `veracrawl.*` module (require `from … import name` so the per-name gate is the only path). AC8 changed: non-`s5:` commits that touch any of the s5 non-registry file set FAIL loudly. Test-27 reference in Open Questions corrected. AC1 collected count stays at **37** (one removal — old test 3 `test_feedback_rejects_run_ref_mismatch_with_snapshot` no longer fits since the contract dropped its snapshot field; one addition — new test 10 `test_feedback_has_no_snapshot_field` pins the structural decision; one rename — old test 17 → new test 17 `test_derive_rejects_run_ref_mismatch_with_snapshot` reframes the invariant to live in the helper). |
| 4    | 2026-05-14 | REJECTED | 2 majors + 1 minor: (major) AC8 registry-bypass — a non-`s5:` commit that only adds the `PlannerObservationFeedback` `FOUNDATION_CONTRACTS` entry would pass AC8 with no STATUS row. (major) adapter allowlist admits `utc_now()` / `TimestampedModel` via the whole-module `veracrawl.contracts.common` allow; replay invariant claims a pure function but doesn't gate this. (minor) "wraps a `GraphObservationSnapshot`" still appears in the Why section and topic README, inconsistent with the v4 structural decision. | Plan revised to v5: AC8 phase A2 added — commits that introduce or modify the literal string `"PlannerObservationFeedback"` in `src/veracrawl/contracts/registry.py` (detected via `git log -S`) must have subject `s5:`. Adapter import allowlist for `veracrawl.contracts.common` switched to name-allowlist `{Ref, VeraModel, stable_hash}` only — `utc_now`, `TimestampedModel`, and any future addition rejected. Why section reworded to "typed projection of a graph snapshot"; README row reworded to "typed read projection". No test-count change. |
| 5    | 2026-05-14 | PLAN_DONE_WITH_RESERVATIONS | Iter 5 returned 2 majors + 1 minor: (major) hub-page hint emission used dict insertion order, but `VeraModel.canonical_json()` sorts dict keys — after JSON round-trip, hub-hint emission order would differ from original, breaking replay-stability. (major) contract import-boundary test 20 allowed the whole `veracrawl.contracts.common` module, admitting `utc_now` / `TimestampedModel` even though the contract module is purely pure. (minor) test 21 prose introduces "four sub-checks" then lists six. **iter-5 fixes applied to plan body in v6 (this row):** hub-hint ordering changed from "dict insertion order" to "sorted by URL ascending" — replay-stable across canonical_json round-trip; new red test 27a `test_v2_hub_hint_order_is_url_sorted` added; new red test 28a `test_v2_decision_is_replay_stable_through_feedback_canonical_json_round_trip` added (derive → canonical_json → reload → re-plan → assert byte-equal). Test 20 split into per-name allowlist `{Ref, VeraModel, stable_hash}` for `contracts.common` + `TYPE_CHECKING`-gated `GraphObservationSnapshot` only. New test 17a `test_feedback_model_fields_exactly` pins `PlannerObservationFeedback.model_fields` keys to `{"id", "run_ref", "redirect_neighbours", "canonical_targets", "page_neighbour_count_by_url"}`. Test 21 prose corrected from "Four sub-checks" to "Six sub-checks". AC1 collected count 37 → 40 (three new tests). | **Reservations carried into implementation** (≤5 iter budget exhausted; codex re-review not exercised, per s1 precedent): (R1) the new iter-5 findings were addressed in the plan but not re-tested via codex; reviewer to confirm during impl task-review that the v6 changes actually close them. (R2) the hub-hint URL-sort decision is binding — if a future slice needs insertion-order semantics, it must add a contract field, not regress this rule. (R3) the `TYPE_CHECKING`-gate detection in test 20 relies on the AST parent containing an `If(test=Name("TYPE_CHECKING"))`; an alias `from typing import TYPE_CHECKING as TC` would bypass it — out of scope for s5 but flagged for s6+. |

Codex plan-review gate via `~/.claude/hooks/codex-review.sh plan
<plan-file> --project-dir $PWD`. ≤ 5 iterations.

## Why

- **AGENTS.md hard constraint — general-purpose**: capability 2 of the
  goal doc requires "URL/canonical/redirect/page-structure graph
  captured during real runs and consumed by frontier prioritization".
  s4 shipped the capture side (the `GraphObservationPort` + 4 event
  contracts + `InMemoryGraphObserver`); s5 closes the **consumption**
  side by giving a planner adapter a typed way to read those
  observations and emit refined `frontier_priority_hints`.
- **AGENTS.md hard constraint — low coupling**: the planner adapter
  must not depend on the `InMemoryGraphObserver` concrete adapter or
  on `graph_memory`. It consumes only the typed
  `PlannerObservationFeedback` — a **typed read projection** of a
  graph snapshot (the snapshot itself is consumed by the derive
  helper at construction time and is NOT carried as a public field
  on the contract). The caller — eventually s6's runner — is
  responsible for assembling the feedback (running the derive
  helper against whichever observer adapter is wired) before
  invoking the planner.
- **Goal doc capability 2 (middle slice)**: per the
  `contract+port → fixture-mode adapter → production adapter →
  runtime-spine wiring → live integration test` rule, s4 delivered
  the *capture* port + fixture adapter; s5 delivers the *consumer*
  side (a feedback-aware fixture planner adapter); s6 wires the
  runner to thread observations from the runner's existing side
  effects through the observer → snapshot → feedback → planner →
  runner-back-to-frontier loop.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`graph/`,
  `graph_memory/`, `memory/` — fixture builders; `external_crawl/
  runner.py` imports zero graph symbols"*. After s5, a real
  graph signal (observed canonical / redirect / structural
  neighbours) flows into the planner's typed output. After s6, the
  runner closes the loop.

## Scope

### In

- New contract `veracrawl.contracts.planner_observation_feedback`:
  - `PlannerObservationFeedback` — typed **read projection** of
    a graph snapshot for planner consumption. Fields *(no
    public `snapshot` field — the snapshot is consumed by the
    derive helper but not stored on the contract; this
    eliminates indirect snapshot access from any consumer)*:
    - `id: str` (non-blank).
    - `run_ref: Ref` (non-blank).
    - `redirect_neighbours: list[str]` (deduplicated canonical
      URLs that appear as the `to_canonical_url` of any redirect
      event; emission order matches snapshot order).
    - `canonical_targets: list[str]` (deduplicated `canonical_target_url`
      values from canonical events; same emission-order rule).
    - `page_neighbour_count_by_url: dict[str, int]` (page URL →
      observed `discovered_link_count`; deterministic by
      construction).

    Validators: `id` / `run_ref` non-blank; every URL in the
    three derived collections is absolute http(s);
    `redirect_neighbours` / `canonical_targets` entries unique;
    `page_neighbour_count_by_url` keys absolute http(s) and
    values ≥ 0.

  - `derive_planner_observation_feedback(*, id, run_ref,
    snapshot) -> PlannerObservationFeedback` — pure helper
    that:
    1. Asserts `snapshot.run_ref == run_ref` (raises
       `ValueError("derive_planner_observation_feedback: run_ref must match snapshot.run_ref")`
       otherwise). This is where the run-ref-equality
       invariant lives, since the contract itself no longer
       carries the snapshot.
    2. Walks the snapshot once to produce the three derived
       collections in the documented emission order.
    3. Constructs and returns the `PlannerObservationFeedback`.

    The helper uses **`TYPE_CHECKING`-only** import of
    `GraphObservationSnapshot` for annotations; at runtime
    the helper accesses snapshot fields by name (duck typing
    — `snapshot.run_ref`, `snapshot.redirect_observed_events`,
    etc.). This means the *contract module* never imports
    snapshot types at runtime, closing the indirect-access
    coupling vector identified in iter 3.

- New deterministic adapter
  `veracrawl.adapters.planning.deterministic_crawl_planner_v2.DeterministicCrawlPlannerV2`:
  - Constructor: `__init__(self, *, feedback: PlannerObservationFeedback | None = None)`.
  - `plan(request)` flow:
    0. **Provenance preconditions (when `feedback is not None`)** —
       enforced at the top of `plan()` *before* any work:
       - `feedback.run_ref == request.run_ref` else
         `raise ValueError("DeterministicCrawlPlannerV2: feedback.run_ref must match request.run_ref")`.
       - `feedback.id in request.observed_state_refs` else
         `raise ValueError("DeterministicCrawlPlannerV2: feedback.id must be threaded through request.observed_state_refs")`.
       Both invariants make the caller responsible for asserting
       that the feedback came from the same crawl run and was
       advertised to the planner via the request's existing
       `observed_state_refs` slot (no out-of-band channel).
    1. Sort `request.seed_urls` by the deterministic decay
       formula (same `1/(1+i)` as s1's `DeterministicCrawlPlanner`).
    2. Emit one `PlannedSeed` per seed URL, `AdapterType.HTTP`
       hint.
    3. Emit a single `AdapterPrior(HTTP, 1.0)`.
    4. **Frontier priority hints — feedback-driven** *(this slice's
       point)*: when `feedback` is `None`, emit `[]` (s1 behavior).
       When `feedback` is set, emit (in this fixed order):
       - One `HOST_GLOB` hint per `feedback.redirect_neighbours`
         entry — host extracted from the URL,
         `priority_delta=+0.6` (boost: a known redirect target).
       - One `URL_PREFIX` hint per `feedback.canonical_targets`
         entry — full URL as the prefix,
         `priority_delta=+0.4` (boost: a known canonical
         target).
       - One `URL_PREFIX` hint per
         `feedback.page_neighbour_count_by_url` entry whose
         value is `≥ 5` ("hub page" threshold) — full page URL
         as the prefix, `priority_delta=+0.2` (mild boost: a
         page observed to expose many neighbours is structurally
         valuable to recrawl). Entries with count `< 5` produce
         no hint. **Emission order: hub URLs sorted
         ascending (`sorted(...)`).** This is deliberately
         independent of dict insertion order so the emission
         survives a `VeraModel.canonical_json()` round-trip
         (canonical JSON sorts dict keys — insertion order
         would not be replay-stable; URL-ascending sort is).
       - Hints' `rationale_ref` records the adapter+kind+key:
         - `rationale:deterministic-crawl-planner-v2:redirect-<host>`
         - `rationale:deterministic-crawl-planner-v2:canonical-<url-hash>`
         - `rationale:deterministic-crawl-planner-v2:hub-<url-hash>`
         (URL hash is the first 8 chars of `stable_hash(url)`
         so the rationale is deterministic + short).
    5. Replay refs: `[request.id, adapter_ref,
       request.replay_config_ref, request.objective_ref]`
       plus, when `feedback is not None`, `feedback.id`
       appended last so a snapshot of `decision.replay_refs`
       reflects every input that shaped the plan.
    6. Policy decision refs: `list(request.policy_decision_refs)`
       (defensive copy).
    7. `decision.request_ref == request.id` (inherited from s1's
       `PlanDecision` shape; pinned by red test 34 against
       regression).

- One companion enum extension? No — `FrontierMatchKind` (s1)
  already has `URL_PREFIX` and `HOST_GLOB`.

- Contract registry entry in `FOUNDATION_CONTRACTS` for
  `PlannerObservationFeedback`
  (`OwnerService.AGENTS`, `replay_required=True`).

- Tests per the red list.

### Out

- Modification of `PlanRequest` to carry the feedback inline.
  s1 already has `observed_state_refs: list[Ref]` as the
  extensibility slot; the s5 caller threads the feedback's
  `id` into that list. The planner adapter consumes the
  feedback via its constructor, NOT by resolving a ref —
  resolution remains the caller's responsibility.
- Modification of `CrawlPlannerPort` Protocol. The port stays
  unchanged; only adapters opt into feedback-aware behavior.
- Modification of `external_crawl/runner.py`. Runner wiring is
  s6.
- Production / LLM feedback-aware adapter. s5 ships the
  deterministic version only.
- Any read/write of the s4 `InMemoryGraphObserver`. The s5
  adapter takes a `PlannerObservationFeedback` value, not the
  observer.

## Design

### Module map

```
src/veracrawl/contracts/planner_observation_feedback.py             # new — ≤ 110 LOC
src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py   # new — ≤ 160 LOC
tests/contract/test_planner_observation_feedback_contracts.py       # new — ≤ 280 LOC
tests/contract/test_planner_observation_feedback_contract_registry.py  # new — ≤  30 LOC
tests/contract/test_planner_observation_feedback_import_boundaries.py  # new — ≤ 110 LOC
tests/unit/adapters/planning/test_deterministic_crawl_planner_v2.py # new — ≤ 340 LOC
```

Behavior-LOC ceiling: 110 + 160 = **270 LOC**. Under the binding
≤ 300 LOC cap (headroom = 30 LOC for the extra
provenance + hub-page hint branches).

### Data flow

```
caller (s6 / test) ──► GraphObservationSnapshot (s4)
                             │
                             ▼
            derive_planner_observation_feedback(*, id, run_ref, snapshot)
                             │
                             ▼
                   PlannerObservationFeedback (typed read projection)
                             │
                             ▼
DeterministicCrawlPlannerV2(feedback=<fb>).plan(request)
                             │
                             ▼
                        PlanDecision (s1 contract)
                             │
                             ▼
        decision.frontier_priority_hints filled when fb was set;
        empty otherwise (legacy s1 behavior).
```

### Cross-module flow

- `contracts/planner_observation_feedback.py` imports at
  **runtime** only: `veracrawl.contracts.common.{Ref, VeraModel,
  stable_hash}` + stdlib. The snapshot/event types are
  imported only inside an `if TYPE_CHECKING:` block — they
  appear in helper signatures as forward references but are
  never present at module import time. The contract has
  **no** `snapshot` field, so it does not depend on the
  graph_observation runtime symbols at all. The derive
  helper accesses snapshot fields via attribute lookup at
  call time (duck-typed `snapshot.run_ref`,
  `snapshot.redirect_observed_events`, etc.).
- `adapters/planning/deterministic_crawl_planner_v2.py`
  imports ONLY (via `from … import …` — aliased
  `import veracrawl.foo as f` is rejected by test 21
  sub-check 2):
  - stdlib (`STDLIB_ALLOWLIST`),
  - `veracrawl.contracts.common`,
  - `veracrawl.contracts.crawl_planner`,
  - `veracrawl.contracts.enums`,
  - `veracrawl.contracts.planner_observation_feedback`
    (name allowlist: `{PlannerObservationFeedback}` only),
  - `veracrawl.ports.crawl_planner`.

  The adapter reaches snapshot data only through the typed
  feedback fields (`feedback.redirect_neighbours`,
  `feedback.canonical_targets`,
  `feedback.page_neighbour_count_by_url`). Since the
  contract has no `snapshot` field, no `feedback.snapshot`
  path exists; test 22 adds defense-in-depth by banning
  any `Attribute(attr="snapshot")`, `getattr(_,
  "snapshot")`, and the literal `"snapshot"` string in the
  adapter source.
- The import-boundary tests (20–22) enforce all of the
  above by AST-walking the two modules.

### Replay invariant

The feedback's derived collections are **pure functions** of
the snapshot. Given the same snapshot,
`derive_planner_observation_feedback(*, id, run_ref, snapshot)`
returns byte-equal output. The deterministic planner v2 is also
a pure function of `(request, feedback)`. Two runs with the
same inputs produce byte-equal `PlanDecision.canonical_json()`.
No new non-determinism is introduced.

### Naming

- `PlannerObservationFeedback` (vs `GraphFeedback`): "planner
  observation feedback" names the *interface* between the
  observation port (s4) and the planner port (s1). "Graph
  feedback" is broader and would imply graph-shape outputs
  (nodes / edges) that the s4 capture surface doesn't yet ship.
- `DeterministicCrawlPlannerV2` (vs renaming s1's adapter):
  s1's adapter stays as the no-feedback baseline; v2 is
  *additionally* feedback-aware, so the old adapter remains
  the right default for callers without observations.

## Dependencies

### On prior slices

- s1 (`CrawlPlannerPort` + `PlanRequest` / `PlanDecision` /
  `PlannedSeed` / `AdapterPrior` / `FrontierPriorityHint` /
  `FrontierMatchKind`).
- s4 (`GraphObservationSnapshot` + 4 event types).

### On existing repo state

- `veracrawl.contracts.common.{Ref, VeraModel, stable_hash}`.
- `veracrawl.contracts.registry.{FOUNDATION_CONTRACTS,
  _contract}`.

### Prerequisites

None new.

## Test Strategy

Red-first list.

### `tests/contract/test_planner_observation_feedback_contracts.py`

1. `test_feedback_rejects_blank_id` → `ValidationError(match="id")`.
2. `test_feedback_rejects_blank_run_ref` → `ValidationError(match="run_ref")`.
3. `test_feedback_rejects_non_http_redirect_neighbour` →
   `ValidationError(match="redirect_neighbours")`.
4. `test_feedback_rejects_duplicate_redirect_neighbour` →
   `ValidationError(match="redirect_neighbours")`.
5. `test_feedback_rejects_non_http_canonical_target` →
   `ValidationError(match="canonical_targets")`.
6. `test_feedback_rejects_duplicate_canonical_target` →
   `ValidationError(match="canonical_targets")`.
7. `test_feedback_rejects_non_http_page_neighbour_url` →
   `ValidationError(match="page_neighbour_count_by_url")`.
8. `test_feedback_rejects_negative_page_neighbour_count` →
   `ValidationError(match="page_neighbour_count_by_url")`.
9. `test_feedback_accepts_minimal_empty_collections` —
   construct with empty derived collections succeeds.
10. `test_feedback_has_no_snapshot_field` —
    `"snapshot" not in PlannerObservationFeedback.model_fields`.
    Pins the structural decision: the snapshot type is NOT
    re-exposed on the contract, eliminating any
    `feedback.snapshot` / `getattr(feedback, "snapshot")` /
    `feedback.model_dump()["snapshot"]` access path.
10a. `test_feedback_model_fields_exactly` —
    `set(PlannerObservationFeedback.model_fields.keys()) ==
    {"id", "run_ref", "redirect_neighbours",
    "canonical_targets", "page_neighbour_count_by_url"}`.
    Pins the contract surface so a stealth field addition
    (e.g., re-introducing `snapshot`, adding a `clock_ref`)
    fails CI rather than silently bypassing the structural
    guarantees.
11. `test_derive_extracts_redirect_neighbours_in_order` —
    snapshot with three redirect events targeting URLs A, B, C
    (in that order) → `feedback.redirect_neighbours == [A, B, C]`.
12. `test_derive_dedups_redirect_neighbours` —
    snapshot with two events both targeting URL A →
    `feedback.redirect_neighbours == [A]`.
13. `test_derive_extracts_canonical_targets_in_order` —
    analogous.
14. `test_derive_dedups_canonical_targets` — analogous.
15. `test_derive_extracts_page_neighbour_counts` —
    snapshot with two page-structure events for the same page
    → most-recent count wins; emission-order test.
16. `test_derive_is_deterministic_for_identical_input` —
    two calls with the same snapshot return byte-equal
    `canonical_json()` outputs.
17. `test_derive_rejects_run_ref_mismatch_with_snapshot` —
    `derive_planner_observation_feedback(id="fb:1",
    run_ref="run:a", snapshot=<run_ref="run:b">)` raises
    `ValueError(match="run_ref must match snapshot.run_ref")`.
    This is the single canonical home for the
    run-ref-equality invariant after the contract dropped
    its `snapshot` field.

### `tests/contract/test_planner_observation_feedback_contract_registry.py`

18. `test_registry_contains_planner_observation_feedback` —
    `"PlannerObservationFeedback"` registered with
    `replay_required=True` and
    `owner_service=OwnerService.AGENTS`.
19. `test_registry_validate_returns_ok` (regression).

### `tests/contract/test_planner_observation_feedback_import_boundaries.py`

Shared constant in the test module:

```python
STDLIB_ALLOWLIST = {
    "__future__", "typing", "collections.abc", "re",
    "hashlib", "urllib.parse",
    "pydantic",   # iter-1 task-review correction: contract validators
                  # need `pydantic.model_validator`. Pydantic is a pure
                  # validation library — no non-determinism, no I/O —
                  # so it is treated identically to stdlib for import-
                  # boundary purposes. Same precedent as s2 plan iter-1
                  # task-review (allowlist extended for pydantic).
}
SNAPSHOT_AND_EVENT_TYPES = {
    "GraphObservationSnapshot",
    "UrlObservedEvent", "RedirectObservedEvent",
    "CanonicalObservedEvent", "PageStructureObservedEvent",
}
```

20. `test_contracts_planner_observation_feedback_imports_allowlist`
    — AST walk of `src/veracrawl/contracts/planner_observation_feedback.py`.
    Four sub-checks:
    1. `level == 0` for all imports (no relative imports).
    2. For every `ast.Import` node: every `alias.name` ∈
       `STDLIB_ALLOWLIST` only (no `veracrawl.*` aliased
       module imports; the contract uses `from … import name`
       exclusively for veracrawl symbols).
    3. For every `ast.ImportFrom` node: `module ∈
       STDLIB_ALLOWLIST ∪ {"veracrawl.contracts.common",
       "veracrawl.contracts.graph_observation"}`. The
       `graph_observation` import is permitted ONLY inside
       an `if TYPE_CHECKING:` block; the test detects this
       by recording the parent context of each `ImportFrom`
       and asserting any `graph_observation` import has
       parent chain `Module → If` with the `If.test` node
       being a `Name("TYPE_CHECKING")`. Runtime imports of
       `graph_observation` are rejected.
    4. **Per-name allowlist for `veracrawl.contracts.common`**:
       every name imported from `contracts.common` must be in
       `{"Ref", "VeraModel", "stable_hash"}`. Any other
       symbol — including `utc_now`, `TimestampedModel`,
       `now`, or any future addition — is rejected. The
       contract module derives no time-bearing values; this
       gate pins that decision at the boundary.
21. `test_adapters_planning_deterministic_crawl_planner_v2_imports_allowlist`
    — AST walk of
    `src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py`.
    Six sub-checks:
    1. `level == 0` for all imports.
    2. **No `ast.Import` nodes for `veracrawl.*` modules.**
       Aliased module-imports
       (`import veracrawl.contracts.planner_observation_feedback as pof`)
       are rejected; any `veracrawl.*` symbol must enter via
       `from … import name` so the per-name gate (sub-check
       4) applies. `ast.Import` of stdlib modules is fine
       (verified against `STDLIB_ALLOWLIST`).
    3. **Module allowlist for `ast.ImportFrom`**: `module ∈
       STDLIB_ALLOWLIST ∪ {
         "veracrawl.contracts.common",
         "veracrawl.contracts.crawl_planner",
         "veracrawl.contracts.enums",
         "veracrawl.contracts.planner_observation_feedback",
         "veracrawl.ports.crawl_planner",
       }`. `STDLIB_ALLOWLIST` is the explicit set — `openai`,
       `httpx`, `langchain`, `anthropic` etc. are rejected.
    4. **Per-name allowlist for `veracrawl.contracts.common`**:
       every name imported from `veracrawl.contracts.common`
       must be in `{"Ref", "VeraModel", "stable_hash"}`.
       `utc_now`, `TimestampedModel`, and any other symbol
       (current or future) are rejected. Rationale: the
       v2 adapter's pure-function replay invariant requires
       that it never reads wall-clock time, so it must not
       have `utc_now` / `TimestampedModel` in scope.
    5. **Per-name allowlist for the feedback contract**: every
       `ImportFrom(module="veracrawl.contracts.planner_observation_feedback")`
       imported name must be in
       `{"PlannerObservationFeedback"}`. Imports of
       `GraphObservationSnapshot`, any event type, or
       `derive_planner_observation_feedback` are rejected.
       (Note: dropping the contract's public `snapshot`
       field means snapshot types are NOT re-exported by
       `planner_observation_feedback` either — sub-check 5
       is now belt-and-suspenders for that structural
       guarantee.)
    6. **Per-name allowlist for `veracrawl.contracts.crawl_planner`
       and `veracrawl.contracts.enums`**: the adapter may
       import only names it actually uses; we pin the v2
       set as `{"PlanRequest", "PlannedSeed", "AdapterPrior",
       "FrontierPriorityHint", "PlanDecision"}` from
       `crawl_planner` and `{"AdapterType", "FrontierMatchKind"}`
       from `enums`. Any other name from these two modules
       is rejected.
22. `test_adapters_planning_deterministic_crawl_planner_v2_never_touches_snapshot_attribute`
    — AST walk + source-bytes scan of the adapter module:
    1. No `ast.Attribute(attr == "snapshot")` anywhere in
       the module.
    2. No `ast.Call(func=ast.Name("getattr"),
       args=[..., ast.Constant("snapshot")])` —
       blocks `getattr(feedback, "snapshot")`.
    3. The literal string `"snapshot"` does not appear in
       the file's source bytes at all (this is the
       belt-and-suspenders check; covers
       `feedback.model_dump()["snapshot"]`,
       f-strings, comments, etc.). Since the adapter has no
       legitimate use of the string `"snapshot"`, the check
       is safe.

    Rationale: even though v4 removed the public `snapshot`
    field, defense-in-depth pins the *no-indirect-access*
    rule against any future regression where the field gets
    re-added.
23. `test_external_crawl_runner_does_not_import_planner_observation_feedback`
    — s5 guard: wiring is s6.

### `tests/unit/adapters/planning/test_deterministic_crawl_planner_v2.py`

24. `test_v2_without_feedback_matches_s1_decision_shape` —
    no `feedback` argument; emits exactly one `PlannedSeed`
    per seed URL, one `AdapterPrior(HTTP, 1.0)`, zero
    frontier hints.
25. `test_v2_emits_host_glob_hints_for_redirect_neighbours` —
    feedback with two redirect neighbours
    (`https://a.example/x` and `https://b.example/y`) → two
    `FrontierPriorityHint` entries with
    `match_kind=HOST_GLOB`, `match_value` equal to the host,
    `priority_delta=0.6`.
26. `test_v2_emits_url_prefix_hints_for_canonical_targets` —
    analogous with `URL_PREFIX` and `priority_delta=0.4`.
27. `test_v2_emits_url_prefix_hints_for_hub_pages` —
    feedback with `page_neighbour_count_by_url == {"https://a.example/hub":
    5, "https://a.example/leaf": 1}` → one
    `FrontierPriorityHint` for `https://a.example/hub` with
    `match_kind=URL_PREFIX`, `priority_delta=0.2`; the
    `leaf` entry (count < 5) produces no hint. Total hint
    count: 1.
27a. `test_v2_hub_hint_order_is_url_sorted` —
    feedback constructed with insertion order
    `{"https://z.example/hub": 9, "https://a.example/hub": 7,
    "https://m.example/hub": 5}` → emitted hub hints
    appear in URL-ascending order
    (`a.example/hub`, `m.example/hub`, `z.example/hub`).
    Pins the replay-stability rule against dict insertion
    order.
28. `test_v2_emits_hints_in_redirect_canonical_hub_order` —
    feedback with all three kinds → hints appear in the
    fixed order: redirect-derived first, canonical-derived
    second, hub-page-derived third.
28a. `test_v2_decision_is_replay_stable_through_feedback_canonical_json_round_trip`
    *(replay invariant)* — construct a feedback with
    redirect / canonical / hub data; emit a
    `PlanDecision_a` from
    `DeterministicCrawlPlannerV2(feedback=fb_a).plan(req)`;
    round-trip the feedback through canonical JSON
    (`fb_b = PlannerObservationFeedback.model_validate_json(
    fb_a.canonical_json())`); emit a `PlanDecision_b` from
    `DeterministicCrawlPlannerV2(feedback=fb_b).plan(req)`;
    assert `PlanDecision_a.canonical_json() ==
    PlanDecision_b.canonical_json()`. This is the test that
    iter 5 flagged as missing — it directly pins the
    canonical-JSON round-trip property against any future
    regression in either the contract's serialization or
    the adapter's emission order.
29. `test_v2_rejects_feedback_run_ref_mismatch_with_request`
    *(provenance)* — feedback has `run_ref="run:a"`, request
    has `run_ref="run:b"` → `plan()` raises `ValueError(match=
    "feedback.run_ref must match request.run_ref")`.
30. `test_v2_rejects_feedback_id_not_in_request_observed_state_refs`
    *(provenance)* — feedback `id="fb:1"`, request
    `observed_state_refs=["other"]` → `plan()` raises
    `ValueError(match="feedback.id must be threaded")`.
31. `test_v2_records_feedback_id_in_decision_replay_refs`
    *(provenance)* — when feedback is set and the
    provenance preconditions hold, `decision.replay_refs[-1]
    == feedback.id`.
32. `test_v2_without_feedback_does_not_record_feedback_id_in_replay_refs`
    *(provenance)* — when feedback is `None`,
    `decision.replay_refs` does **not** contain any string
    starting with `"fb:"`; length == 4
    (`[request.id, adapter_ref, replay_config_ref,
    objective_ref]`).
33. `test_v2_rationale_refs_are_deterministic_from_inputs` —
    rationale refs match the documented formulas
    (`redirect-<host>`, `canonical-<8-char-hash>`,
    `hub-<8-char-hash>`).
34. `test_v2_decision_request_ref_equals_request_id`
    *(provenance)* — for both `feedback=None` and
    `feedback=<fb>` paths, `decision.request_ref ==
    request.id` (pin against regression).
35. `test_v2_is_pure_function` — two `.plan(request)` calls
    on the same instance return byte-equal
    `canonical_json()`.
36. `test_v2_implements_crawl_planner_port` —
    `isinstance(DeterministicCrawlPlannerV2(), CrawlPlannerPort)`.
37. `test_v2_policy_decision_refs_forwarded_verbatim` —
    matches s1 behavior; verifies the v2 adapter doesn't
    regress this invariant.

### Green path

Each red test gets a minimal implementation. One purpose per
commit. After all 37 tests pass, refactor only obvious
duplication.

## Acceptance Criteria

Mechanically verifiable.

1. **Pytest gate** —
   `pytest tests/contract/test_planner_observation_feedback_contracts.py tests/contract/test_planner_observation_feedback_contract_registry.py tests/contract/test_planner_observation_feedback_import_boundaries.py tests/unit/adapters/planning/test_deterministic_crawl_planner_v2.py -v`
   exits 0 with **40** collected, **40** passed.
   (37 from v4 + 3 added in v6: 10a `test_feedback_model_fields_exactly`,
   27a `test_v2_hub_hint_order_is_url_sorted`,
   28a `test_v2_decision_is_replay_stable_through_feedback_canonical_json_round_trip`.)
2. **Contract registry** —
   `python -c "from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry; from veracrawl.contracts.enums import OwnerService; r = FOUNDATION_CONTRACTS['PlannerObservationFeedback']; assert r.replay_required and r.owner_service is OwnerService.AGENTS; assert validate_registry().ok"`
   exits 0.
3. **No runner wiring** —
   `python -c "import pathlib; assert 'planner_observation_feedback' not in pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text() and 'DeterministicCrawlPlannerV2' not in pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text()"`
   exits 0.
4. **Adapter import allowlist** —
   `pytest tests/contract/test_planner_observation_feedback_import_boundaries.py::test_adapters_planning_deterministic_crawl_planner_v2_imports_allowlist -v`
   exits 0.
5. **No graph_memory / graph imports anywhere in s5 code** —
   `! grep -rE '\b(veracrawl\.graph_memory|veracrawl\.graph\b)' src/veracrawl/contracts/planner_observation_feedback.py src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py`
   (grep exits 1 — no match).
6. **Behavior LOC budget** —
   `total=$(wc -l src/veracrawl/contracts/planner_observation_feedback.py src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py | tail -1 | awk '{print $1}'); test "$total" -le 300`
   exits 0.
7. **Codex plan-review gate recorded** — STATUS records at
   least one s5 plan-review row whose verdict is either
   `APPROVED` or `DONE_WITH_RESERVATIONS`:
   `grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s5-planner-observation-feedback.md`
   reports `≥ 1`. The s5 plan file is the location of the
   plan-review log (per s4 / s3 precedent). Acceptance:
   `[ $(grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s5-planner-observation-feedback.md) -ge 1 ]`
   exits 0.
8. **Codex task-review per commit recorded** — every commit
   that touches any of the s5 file set must have a matching
   `s5-impl-<sha7>` STATUS row with verdict `APPROVED` or
   `DONE_WITH_RESERVATIONS`. The s5 commit range is bounded
   below by the s5-plan commit (the commit that first added
   `s5-planner-observation-feedback.md`) — this works
   whether the branch is `master` or a feature branch.

   Mechanical check (run from repo root):
   ```bash
   set -eu
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' \
     -- docs/plans/general-purpose-crawler-agentification/s5-planner-observation-feedback.md \
     | tail -1)
   [ -n "$plan_first" ] || { echo "s5 plan commit not found"; exit 1; }

   s5_exclusive_paths=(
     src/veracrawl/contracts/planner_observation_feedback.py
     src/veracrawl/adapters/planning/deterministic_crawl_planner_v2.py
     tests/contract/test_planner_observation_feedback_contracts.py
     tests/contract/test_planner_observation_feedback_contract_registry.py
     tests/contract/test_planner_observation_feedback_import_boundaries.py
     tests/unit/adapters/planning/test_deterministic_crawl_planner_v2.py
   )
   s5_shared_paths=(
     src/veracrawl/contracts/registry.py
   )

   bad_subject=0
   missing=0

   # Phase A1: every commit touching any s5-exclusive path MUST
   # have subject prefix "s5:". Off-policy commits FAIL loudly.
   for full_sha in $(git log --pretty=format:'%H' "${plan_first}..HEAD" -- "${s5_exclusive_paths[@]}"); do
     subj=$(git log -1 --pretty=format:'%s' "$full_sha")
     case "$subj" in
       "s5:"*) ;;
       *) echo "off-policy commit touches s5-exclusive paths: $full_sha '$subj'"; bad_subject=1 ;;
     esac
   done

   # Phase A2: every commit that introduces or removes the
   # literal string "PlannerObservationFeedback" in
   # src/veracrawl/contracts/registry.py MUST also have subject
   # "s5:". This catches a registry-only commit that adds the
   # s5 contract entry under a non-s5 subject (which would
   # otherwise slip past Phase A1's exclusive-path gate).
   for full_sha in $(git log -S'"PlannerObservationFeedback"' --pretty=format:'%H' "${plan_first}..HEAD" -- src/veracrawl/contracts/registry.py); do
     subj=$(git log -1 --pretty=format:'%s' "$full_sha")
     case "$subj" in
       "s5:"*) ;;
       *) echo "off-policy commit edits PlannerObservationFeedback registry entry: $full_sha '$subj'"; bad_subject=1 ;;
     esac
   done

   # Phase B: every s5-attributed commit (subject "s5:*") in the
   # range, regardless of which s5 paths it touches, MUST have a
   # matching s5-impl-<sha7> row in STATUS with APPROVED or
   # DONE_WITH_RESERVATIONS.
   all_in_range=$(git log --pretty=format:'%H %s' "${plan_first}..HEAD" -- "${s5_exclusive_paths[@]}" "${s5_shared_paths[@]}")
   while IFS= read -r line; do
     full_sha=${line%% *}
     subj=${line#* }
     case "$subj" in
       "s5:"*) ;;
       *) continue ;;   # Phase A already covered exclusive-path off-policy; shared paths are allowed under other subjects.
     esac
     short=$(git rev-parse --short=7 "$full_sha")
     grep -qE "s5-impl-${short}\b.* (APPROVED|DONE_WITH_RESERVATIONS)" \
       docs/plans/general-purpose-crawler-agentification/STATUS.md \
       || { echo "missing s5-impl-${short} row in STATUS"; missing=1; }
   done <<<"$all_in_range"

   [ $bad_subject -eq 0 ] && [ $missing -eq 0 ]
   ```
   exits 0.

   **Commit-subject convention** (binding for s5): every
   commit that touches any of `s5_exclusive_paths` has
   subject prefix `s5:`. Phase A makes this mechanical:
   an off-policy commit that edits
   `deterministic_crawl_planner_v2.py` (or any other
   s5-exclusive file) but uses a different subject prefix
   fails AC8. Phase B then requires the STATUS row for
   every `s5:`-attributed commit. `registry.py` is in
   `s5_shared_paths` because it is co-owned with other
   slices; non-`s5:` edits to it are allowed (e.g., a later
   slice extending the registry) and do not trip Phase A,
   but `s5:`-subject edits still require a STATUS row via
   Phase B.

## Rollback

s5 only adds new files plus one `FOUNDATION_CONTRACTS` entry.
Rollback is `git revert <s5-commit-range>` — no schema
changes, no consumer breakage. s1's
`DeterministicCrawlPlanner` remains the no-feedback baseline.

## Open Questions

1. **`priority_delta` magnitudes (0.6 / 0.4 / 0.2)**:
   arbitrary in s5; later slices may tune. The s3
   priority-queue frontier (placeholder slice s3.1) will
   consume these deltas, so the magnitudes are testable
   end-to-end once that lands.
2. **Hint emission order**: redirect-derived first,
   canonical-derived second, hub-page-derived third. Open
   to revision; pinned by test 28 either way.
3. **Hub-page threshold (`discovered_link_count ≥ 5`)**:
   arbitrary in s5. The cutoff is meant to suppress noise
   from low-link pages (likely article leaves) while
   boosting hub-style pages. Future slices may swap this
   for a percentile-based threshold once we have corpus-
   scale page-structure data.
4. **`page_neighbour_count_by_url`**: "most recent count
   wins" when multiple `PageStructureObservedEvent`s name the
   same page. Alternative: max count or sum across observations.
   Default: most-recent (matches the "snapshot is a point-in-
   time projection" semantic).
5. **LLM planner v2**: a future slice will mirror this
   feedback-aware shape for the s2 `LlmCrawlPlanner`. Out of
   scope here.
