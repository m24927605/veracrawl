# s1 — `CrawlPlannerPort` + plan-decision contract + deterministic fixture adapter

## Status

Plan-review iteration table for this slice. The `STATUS.md` row holds
the canonical outcome with full finding bodies; this table is the
inline summary.

| Iter | Date (UTC) | Verdict  | Findings (one-liner) | Resolution |
|------|------------|----------|----------------------|------------|
| 1    | 2026-05-13 | REJECTED | 2 blockers (seed-input gap, inconsistent `replay_refs`) + 3 majors (second port, LOC budget, hook bypass) | Plan revised to v2: caller passes `seed_urls` directly, single new port, consistent `replay_refs`, prerequisite hook shim, LOC recomputed ≤300 |
| 2    | 2026-05-13 | REJECTED | iter-1 findings closed (per codex). 3 new majors: policy-decision-ref mislabel, observed-state-ref cardinality leak, non-existent `model_dump_json(sort_values)` API | Plan revised to v3: `PlanRequest.policy_decision_refs` added and forwarded verbatim; adapter prior fixed to `[(HTTP, 1.0)]` only (no `observed_state_refs` branching); test 28 uses `canonical_json()` byte-equality; observed-state branching test dropped |
| 3    | 2026-05-13 | REJECTED | iter-2 findings all closed (per codex). 1 major + 1 minor: (major) `decision.request_ref == request.id` invariant specified but not mechanically asserted by any red test — an adapter could emit a wrong `request_ref` while still putting `request.id` in `replay_refs` and pass; (minor) STATUS test-number drift vs inline red list | Plan revised to v4: new red test 27a `test_request_ref_equals_request_id` asserts `decision.request_ref == request.id`; acceptance criterion 1 collected-test count bumped to 31; STATUS rows aligned to the actual red list numbering |
| 4    | 2026-05-13 | REJECTED | iter-1/2/3 findings all closed (per codex). 1 major: several declared contract validator invariants (non-blank scalar refs on `PlanRequest`, non-blank `rationale_ref` on `PlannedSeed`/`AdapterPrior`/`FrontierPriorityHint`, non-blank `request_ref`/`planner_adapter_ref` on `PlanDecision`) are NOT mechanically asserted by any red test — an implementation could leave the validators out and still pass the 31-test pytest gate. | Plan revised to v5: 10 new discrete red tests added covering every previously-untested non-blank ref invariant (5 `PlanRequest` scalars × 1 each, 3 `rationale_ref` × 1 each, 2 `PlanDecision` scalars × 1 each); acceptance criterion 1 collected-test count bumped from 31 → 41. Iter 5 follows. |
| 5    | 2026-05-13 | REJECTED — DONE_WITH_RESERVATIONS via post-iter-5 follow-up | iter-1/2/3/4 findings all closed (per codex). 1 major + 1 minor: (major) adapter import boundary test 21 uses a blocklist regex — an implementation could import internal runtime modules (`veracrawl.external_crawl.runner`, `veracrawl.agents.orchestration`) and still pass; (minor) topic README line 38 still describes the obsolete `CrawlObjective → PlanDecision` shape rather than the revised `PlanRequest(seed_urls=...) → PlanDecision` shape. | Post-iter-5 follow-up landed in this same plan revision (no re-review): test 21 rewritten as a strict AST **allowlist** (stdlib + `veracrawl.contracts.*` + `veracrawl.ports.crawl_planner` only); acceptance criterion 4 rewritten to reference the allowlist test (earlier note in this row mistakenly said "dropped"); topic README updated. Per goal doc, plan lands as `DONE_WITH_RESERVATIONS` because iter-5 follow-up was not re-reviewed. |

**Codex plan-review gate**: AGENTS.md "Plan-Driven Development" and the
goal doc call
`~/.claude/hooks/codex-review.sh plan <plan-file> --project-dir $PWD`.
That hook is **not present on this machine**
(`ls ~/.claude/hooks` returned empty). The codex companion runtime IS
installed at
`/Users/michael.chen/.claude/plugins/cache/openai-codex/codex/1.0.4/scripts/codex-companion.mjs`,
exposing `task` and `adversarial-review` subcommands. Restoring the
documented hook is treated as a **prerequisite for landing s1** (see
Dependencies → Prerequisites). For *this plan-review pass* the
substitution is unavoidable; the prompt body and substitution rationale
are recorded in `STATUS.md` so a future audit can compare against the
hook-installed version. Iter outcomes here mirror what the hook would
have reported.

## Why

- **AGENTS.md hard constraint — general-purpose**: VeraCrawl must
  remain a general-purpose AI agent crawler.
  `src/veracrawl/agents/orchestration.py:60` dispatches on
  `scenario: str` and emits ref-string fixtures; there is no typed
  contract surface that says *"given an objective + candidate seeds,
  choose adapters / per-seed priority / frontier hints / extraction
  strategy"*. Without that surface, every later capability has nowhere
  to plug in. s1 introduces the surface.
- **AGENTS.md hard constraint — low coupling / high cohesion**: the
  current scaffolding bakes scenario knowledge into the orchestration
  module. The planning capability must flow through a port whose shape
  does not depend on any adapter, any model SDK, any browser engine,
  or any persistence client. s1 introduces that port and its contracts
  in `ports/` and `contracts/` only.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`target_runtime/*` —
  fixture template synthesis; no objective→plan→adaptive-frontier
  loop"* and *"`agents/orchestration.py` — scenario-string dict
  lookup"*. s1 closes the planner half of that gap, contract-first.
- **Goal doc capability 1**: *"Agent planning loop wired into
  `ExternalCrawlRunner` (objective → adapter choice → frontier priority
  → extraction strategy)"*. s1 is the first slice of that capability;
  per the goal's `contract+port → fixture-mode adapter → production
  adapter → runtime-spine wiring → live integration test` rule, s1
  delivers the first two stages — no LLM, no runner wiring — and
  nothing else.

## Scope

### In

- New port `veracrawl.ports.crawl_planner.CrawlPlannerPort`
  (Python `Protocol`, `runtime_checkable`). Single method:

  ```python
  def plan(self, request: PlanRequest) -> PlanDecision: ...
  ```

  No other ports introduced in this slice (iter-1 finding 3).

- New typed contracts in `veracrawl.contracts.crawl_planner`:

  - `PlanRequest` — the input. Fields:
    - `id: str`
    - `run_ref: Ref`
    - `objective_ref: Ref` (lineage only; the planner adapter is
      not obligated to resolve the body — that's a future slice's
      port. Carried so the decision's `replay_refs` can anchor to
      the objective.)
    - `seed_urls: list[str]` (≥ 1 required; each must be absolute
      http(s); duplicates rejected at validator time). This is the
      planner's actual input — the caller hands it a set of candidate
      URLs to triage. *(Iter-1 finding 1.)*
    - `budget_ref: Ref`
    - `policy_snapshot_ref: Ref` (the run's policy snapshot anchor;
      replay lineage only — **NOT** a substitute for individual
      policy-decision refs; see `policy_decision_refs` below). *(Iter-2
      finding 1.)*
    - `policy_decision_refs: list[Ref]` (≥ 1 required; the caller
      passes the individual `PolicyDecision` refs that authorize the
      planner invocation — these are concrete decisions, distinct
      from the snapshot ref). *(Iter-2 finding 1.)*
    - `replay_config_ref: Ref`
    - `observed_state_refs: list[Ref]` (empty for s1; populated by
      later graph-feedback slices, default `[]`). **The s1
      deterministic adapter MUST NOT branch on the contents or
      cardinality of this list** — branching belongs to s5, which
      lands the typed observed-state contract. *(Iter-2 finding 2.)*

  - `PlannedSeed` — one seed the planner decided to admit. Fields:
    - `canonical_url: str` (absolute http(s); the validator reuses
      a private `_is_http_url` helper that mirrors
      `contracts.agent._is_http_url` — see Design § "URL helper
      duplication").
    - `priority_score: float` (`0.0 ≤ x ≤ 1.0`).
    - `adapter_hint: AdapterType`.
    - `rationale_ref: Ref` (non-blank).

  - `AdapterPrior` — per-adapter weight. Fields:
    - `adapter_type: AdapterType`.
    - `weight: float` (`0.0 ≤ x ≤ 1.0`).
    - `rationale_ref: Ref` (non-blank).

  - `FrontierPriorityHint` — pattern-based priority delta. Fields:
    - `match_kind: FrontierMatchKind` (new `StrEnum`:
      `URL_PREFIX` / `HOST_GLOB` / `CONTENT_TYPE_PREFIX`).
    - `match_value: str` (non-blank; shape consistent with
      `match_kind` — `URL_PREFIX` starts with `http(s)://`,
      `HOST_GLOB` matches `[a-zA-Z0-9._*-]+`,
      `CONTENT_TYPE_PREFIX` matches `type/subtype` shape).
    - `priority_delta: float` (`-1.0 ≤ x ≤ 1.0`).
    - `rationale_ref: Ref` (non-blank).

  - `PlanDecision` — the port's output. Fields:
    - `id: str`
    - `request_ref: Ref` (must equal `PlanRequest.id`).
    - `planner_adapter_ref: Ref` (identifies the adapter that produced
      the decision, e.g.
      `"adapter:deterministic-crawl-planner:v1"`).
    - `planned_seeds: list[PlannedSeed]` (≥ 1 required).
    - `adapter_priors: list[AdapterPrior]` (≥ 1 required;
      `adapter_type` values are unique; sum of `weight` is `≤ 1.0 +
      1e-9` and `≥ 0.0`).
    - `frontier_priority_hints: list[FrontierPriorityHint]`
      (may be empty in s1).
    - `extraction_strategy_refs: list[Ref]` (may be empty in s1).
    - `replay_refs: list[Ref]` (validator requires **both**
      `request_ref` AND `planner_adapter_ref` to appear in the list;
      additional refs allowed). *(Iter-1 finding 2.)*
    - `policy_decision_refs: list[Ref]` (≥ 1 required; the planner
      adapter forwards `request.policy_decision_refs` verbatim — see
      Scope and *(Iter-2 finding 1)*).

- One companion enum: `FrontierMatchKind` in
  `veracrawl.contracts.enums` (the conventional home; 100+ enums
  already live there).

- One deterministic fixture adapter in
  `veracrawl.adapters.planning.deterministic_crawl_planner`:
  `class DeterministicCrawlPlanner(CrawlPlannerPort)`. Behavior:
  - Emits exactly one `PlannedSeed` per entry in
    `request.seed_urls`, in input order. Priority decays as
    `1.0 / (1 + index)` — documented as
    `DeterministicCrawlPlanner.SEED_PRIORITY_DECAY` so the formula
    is explicit and replayable.
  - Adapter hint defaults to `AdapterType.HTTP` for every seed.
  - Emits a single fixed `adapter_priors` of exactly one
    `AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
    rationale_ref="rationale:deterministic-crawl-planner:http-only")`
    **regardless** of `request.observed_state_refs`. The
    `rationale_ref` is a deterministic constant exposed as
    `DeterministicCrawlPlanner.HTTP_PRIOR_RATIONALE_REF` so callers
    and replay can pin it. The `observed_state_refs` slot exists
    on `PlanRequest` for s5 to populate but is unread by the s1
    adapter. *(Iter-2 finding 2; smoke-test follow-up corrects
    earlier tuple-notation shorthand.)*
  - Emits zero `frontier_priority_hints` (s5 territory; emitting
    deterministic hints here would be speculative scope creep).
  - Emits `extraction_strategy_refs = []` (s7 territory).
  - Emits `policy_decision_refs = list(request.policy_decision_refs)`
    — the adapter forwards the caller's policy decision refs
    verbatim (defensive copy). It does **NOT** synthesize a
    policy-decision ref from `request.policy_snapshot_ref`; mixing a
    snapshot ref into the decision-refs slot mislabels the
    provenance. *(Iter-2 finding 1.)*
  - Emits `replay_refs = [request.id, planner_adapter_ref,
    request.replay_config_ref, request.objective_ref]` — order is
    the deterministic emission order (test 22 asserts byte-equal).
    *(Iter-1 finding 2.)*

- Contract registry entries in
  `veracrawl.contracts.registry.FOUNDATION_CONTRACTS` for the five
  new pydantic models (`PlanRequest`, `PlannedSeed`, `AdapterPrior`,
  `FrontierPriorityHint`, `PlanDecision`). Each
  `_contract(...,replay_required=True)` and
  `owner_service=OwnerService.AGENTS` (the planner is an agents-owned
  capability; matches the existing `MultiAgentRepairReport` /
  `AgentRecommendation` precedent).

- Tests per the red list below.

### Out

- Any modification of `src/veracrawl/external_crawl/runner.py`. The
  runner does not import the new port in s1.
- Any LLM-backed adapter. The deterministic adapter is the only
  one shipped in s1.
- Any modification of `src/veracrawl/agents/orchestration.py`. The
  scenario-string scaffolding stays; later slices replace it.
- Any modification of `src/veracrawl/target_runtime/`.
- Any second new port (e.g. an objective resolver). Iter-1 finding 3
  drops `ObjectiveResolverPort`; the deterministic adapter does not
  read the objective body. Any future planner that needs the body
  introduces its own port in its own slice.
- `GraphSnapshotRef` typed input on `PlanRequest`. The analogous slot
  in s1 is the generic `observed_state_refs: list[Ref]` so s5 can
  add semantics without breaking the schema.
- Persistence of `PlanDecision`. Persistence wiring is part of s3.

## Design

### Module map (created in this slice)

```
src/veracrawl/contracts/crawl_planner.py        # new — ≤ 130 LOC
src/veracrawl/ports/crawl_planner.py            # new — ≤  50 LOC
src/veracrawl/adapters/planning/__init__.py     # new — empty marker
src/veracrawl/adapters/planning/deterministic_crawl_planner.py  # new — ≤  90 LOC
tests/contract/test_crawl_planner_contracts.py            # new — ≤ 200 LOC
tests/contract/test_crawl_planner_contract_registry.py    # new — ≤  40 LOC
tests/contract/test_crawl_planner_import_boundaries.py    # new — ≤  60 LOC
tests/unit/adapters/planning/test_deterministic_crawl_planner.py  # new — ≤ 170 LOC
```

Behavior LOC (excluding tests and the additive registry-dict edits):
`130 + 50 + 90 = 270 LOC` — **under the binding ≤ 300 LOC budget**.
The pydantic `@model_validator` bodies are counted as hand-written
behavioral logic per iter-1 finding 4 and are part of the 130 LOC
contracts module budget. The five
`_contract(...)` rows added to
`FOUNDATION_CONTRACTS` are mechanical and ≤ 25 LOC; they sit in the
`contracts/registry.py` "generated contract code" carve-out (the
helper already exists at `contracts/registry.py:140-156`).

### Data flow

```
caller assembles PlanRequest(seed_urls=[...], objective_ref, ...)
   |
   v
CrawlPlannerPort.plan(request) ──► PlanDecision
                                     • planned_seeds (one per seed_url)
                                     • adapter_priors
                                     • frontier_priority_hints (empty s1)
                                     • extraction_strategy_refs (empty s1)
                                     • replay_refs (request.id + adapter_ref + ...)
                                     • policy_decision_refs

(later slice s3 wires this into ExternalCrawlRunner; not in s1)
```

The caller — for s1 that is **the test harness**, full stop — is
responsible for assembling the candidate seed URLs (from the
objective, from a sitemap, from prior runs, from an LLM-driven
expansion). The planner is *not* responsible for URL discovery in
s1; it is responsible for **triage**: priority + adapter hint +
frontier hints + extraction strategy refs. This matches the goal
doc's capability-1 framing ("objective → adapter choice → frontier
priority → extraction strategy") — URL discovery is a separate
concern handled by later slices that add the sitemap / RSS /
LLM-expansion ports.

### Contract validator behavior (the test surface for the red list)

For each new pydantic model, `@model_validator(mode="after")`
enforces:

- `PlannedSeed`:
  - `canonical_url` is absolute http(s).
  - `0.0 ≤ priority_score ≤ 1.0`.
  - `rationale_ref` non-blank.

- `AdapterPrior`:
  - `0.0 ≤ weight ≤ 1.0`.
  - `rationale_ref` non-blank.

- `FrontierPriorityHint`:
  - `-1.0 ≤ priority_delta ≤ 1.0`.
  - `match_value` non-blank AND consistent with `match_kind`.
  - `rationale_ref` non-blank.

- `PlanRequest`:
  - All scalar refs (`id`, `run_ref`, `objective_ref`,
    `budget_ref`, `policy_snapshot_ref`, `replay_config_ref`)
    non-blank.
  - `seed_urls` non-empty; each entry is absolute http(s);
    duplicates rejected (case-sensitive — canonicalization is
    upstream).
  - `policy_decision_refs` non-empty. *(Iter-2 finding 1.)*

- `PlanDecision`:
  - `planned_seeds` non-empty.
  - `adapter_priors` non-empty.
  - `adapter_priors` `adapter_type` values are unique.
  - `sum(p.weight for p in adapter_priors) ≤ 1.0 + 1e-9` and `≥ 0`.
  - `request_ref` non-blank.
  - `planner_adapter_ref` non-blank.
  - `request_ref` appears in `replay_refs`. *(Iter-1 finding 2.)*
  - `planner_adapter_ref` appears in `replay_refs`. *(Iter-1
    finding 2.)*
  - `policy_decision_refs` non-empty.

### Cross-module flow

- `ports/crawl_planner.py` imports **only**
  `veracrawl.contracts.crawl_planner` and stdlib
  (`typing.Protocol`, `runtime_checkable`). Asserted by
  `tests/contract/test_crawl_planner_import_boundaries.py`.
- `adapters/planning/deterministic_crawl_planner.py` imports the
  port, the contracts, and stdlib. Forbidden imports
  (model SDKs, browsers, storage, queue, agent frameworks)
  enforced by the same import-boundary test.
- `contracts/registry.py` is the only module outside the new ones
  this slice modifies — five additive entries plus, if needed, one
  `OwnerService.AGENTS` reuse (no enum addition).

### URL helper duplication

`contracts/agent.py:45-56` defines `_is_http_url` (private). s1's
`contracts/crawl_planner.py` mirrors the same function as a private
`_is_http_url` rather than reaching into `contracts.agent`'s
underscore-prefixed name. Codex review iter 1 did not flag this
either way; the duplication is preserved as the default to avoid
cross-contracts module reach into a private symbol. Iter 2 may
revisit; default stands.

### Replay invariant

The planner adapter is deterministic in s1 — no clock, no RNG, no
model output. The replay invariant still applies: `replay_refs`
records both the request lineage (`request.id`) and the producer
identity (`planner_adapter_ref`). When s2 lands the LLM-backed
adapter, it appends `model_call_trace_ref` and
`prompt_template_ref` to the same list — the contract slot already
exists, so s2 is a non-breaking change.

### Naming

`CrawlPlannerPort` (chosen over the goal doc's
`ObjectiveInterpreterPort` example) because:
- The port's output is a *plan decision*, not just an interpreted
  objective — it commits to per-seed priority + adapter prior +
  frontier hints.
- The existing `contracts/objective.CrawlPlan` model uses "plan"
  vocabulary; co-locating under `crawl_planner` keeps the
  terminology coherent.
- "Interpreter" connotes natural-language parsing, which is one
  possible adapter (the s2 LLM adapter) but not the only one.

`DeterministicCrawlPlanner` (not `HeuristicCrawlPlanner`) because
"deterministic" advertises the contract this adapter honors —
the import-boundary test can mechanically verify it.

## Dependencies

### On prior slices

- None (s1 is the topic's first slice).

### On existing repo state

- `veracrawl.contracts.objective.CrawlObjective` (read-only; not
  modified).
- `veracrawl.contracts.common.Ref`,
  `veracrawl.contracts.common.TimestampedModel`,
  `veracrawl.contracts.common.VeraModel`.
- `veracrawl.contracts.enums.AdapterType`,
  `veracrawl.contracts.enums.OwnerService`.
- `veracrawl.contracts.registry.FOUNDATION_CONTRACTS`,
  `veracrawl.contracts.registry._contract` helper.

### Prerequisites (must be true before s1 lands)

1. **`~/.claude/hooks/codex-review.sh` shim installed and
   executable.** *(Iter-1 finding 5.)* The shim delegates to
   `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task
   <standardized-prompt-body> <plan-file-or-baseline>` for the
   `plan` and `task` subcommands. Standardized prompt body lives
   at `docs/plans/general-purpose-crawler-agentification/codex-review-prompts/`
   (added in the same prereq landing). Acceptance check:
   `[ -x ~/.claude/hooks/codex-review.sh ]` returns 0. This
   prereq is scoped to "install the shim"; the prompt-body design
   is reused from the version recorded in iter-1 STATUS and is
   not new authorship.

No new runtime dependency. No `pyproject.toml` change.

## Test Strategy

Red-first list. Each test is written before its implementation
counterpart and verified to fail with the expected error.

### `tests/contract/test_crawl_planner_contracts.py`

1. `test_planned_seed_rejects_non_http_url` — `canonical_url=
   "file:///tmp/x"` → `ValidationError("canonical_url must be an
   absolute http(s) URL")`.
2. `test_planned_seed_rejects_priority_out_of_range` — `priority_score=
   1.5` → `ValidationError(match="priority_score")`.
2a. `test_planned_seed_rejects_blank_rationale_ref` — *(Iter-4
   finding 1)*. `rationale_ref=""` → `ValidationError(match=
   "rationale_ref")`.
3. `test_adapter_prior_rejects_weight_out_of_range` — `weight= -0.1` →
   `ValidationError(match="weight")`.
3a. `test_adapter_prior_rejects_blank_rationale_ref` — *(Iter-4
   finding 1)*. `rationale_ref=""` → `ValidationError(match=
   "rationale_ref")`.
4. `test_frontier_priority_hint_rejects_delta_out_of_range` —
   `priority_delta= 2.0` → `ValidationError(match="priority_delta")`.
5. `test_frontier_priority_hint_rejects_blank_match_value` —
   `match_value= ""` → `ValidationError(match="match_value")`.
6. `test_frontier_priority_hint_rejects_match_value_inconsistent_with_kind` —
   `match_kind=URL_PREFIX`, `match_value="not-a-url"` →
   `ValidationError(match="match_value")`.
6a. `test_frontier_priority_hint_rejects_blank_rationale_ref` —
   *(Iter-4 finding 1)*. `rationale_ref=""` →
   `ValidationError(match="rationale_ref")`.
7. `test_plan_request_rejects_empty_seed_urls` — `seed_urls=[]` →
   `ValidationError(match="seed_urls")`.
8. `test_plan_request_rejects_non_http_seed_url` —
   `seed_urls=["file:///tmp"]` →
   `ValidationError(match="seed_urls")`.
9. `test_plan_request_rejects_duplicate_seed_urls` —
   `seed_urls=["https://a.example", "https://a.example"]` →
   `ValidationError(match="duplicate")`.
10. `test_plan_request_rejects_blank_objective_ref` →
    `ValidationError(match="objective_ref")`.
10a. `test_plan_request_rejects_empty_policy_decision_refs` →
    `ValidationError(match="policy_decision_refs")`. *(Iter-2 finding 1.)*
10a-schema. `test_plan_request_rejects_missing_policy_decision_refs`
    — *(task-review iter 2 follow-up; iter-3 plan-alignment fix)*.
    Construct `PlanRequest` with the `policy_decision_refs` key
    omitted entirely → `ValidationError(match="policy_decision_refs")`
    raised by the Pydantic field-level required-field schema. This
    pins the field-level requirement against a regression to
    `Field(default_factory=list)`, which test 10a alone would not
    catch (10a passes with the defaulted-empty implementation;
    10a-schema does not).
10b. `test_plan_request_rejects_blank_id` — *(Iter-4 finding 1)*.
    `id=""` → `ValidationError(match="id")`.
10c. `test_plan_request_rejects_blank_run_ref` — *(Iter-4 finding 1)*.
    `run_ref=""` → `ValidationError(match="run_ref")`.
10d. `test_plan_request_rejects_blank_budget_ref` — *(Iter-4 finding 1)*.
    `budget_ref=""` → `ValidationError(match="budget_ref")`.
10e. `test_plan_request_rejects_blank_policy_snapshot_ref` — *(Iter-4
    finding 1)*. `policy_snapshot_ref=""` →
    `ValidationError(match="policy_snapshot_ref")`.
10f. `test_plan_request_rejects_blank_replay_config_ref` — *(Iter-4
    finding 1)*. `replay_config_ref=""` →
    `ValidationError(match="replay_config_ref")`.
11. `test_plan_decision_rejects_empty_planned_seeds` →
    `ValidationError(match="planned_seeds")`.
12. `test_plan_decision_rejects_empty_adapter_priors` →
    `ValidationError(match="adapter_priors")`.
13. `test_plan_decision_rejects_duplicate_adapter_types` →
    `ValidationError(match="adapter_priors")`.
14. `test_plan_decision_rejects_adapter_priors_sum_above_one` →
    `ValidationError(match="sum")`.
14a. `test_plan_decision_rejects_blank_request_ref` — *(Iter-4
    finding 1)*. `request_ref=""` →
    `ValidationError(match="request_ref")`.
14b. `test_plan_decision_rejects_blank_planner_adapter_ref` — *(Iter-4
    finding 1)*. `planner_adapter_ref=""` →
    `ValidationError(match="planner_adapter_ref")`.
15. `test_plan_decision_rejects_missing_request_ref_in_replay_refs`
    *(iter-1 finding 2)* — build a decision whose `replay_refs`
    lacks `request_ref` → `ValidationError(match="request_ref")`.
16. `test_plan_decision_rejects_missing_planner_adapter_ref_in_replay_refs`
    *(iter-1 finding 2)* — likewise for `planner_adapter_ref` →
    `ValidationError(match="planner_adapter_ref")`.
17. `test_plan_decision_rejects_empty_policy_decision_refs` →
    `ValidationError(match="policy_decision_refs")`.

### `tests/contract/test_crawl_planner_contract_registry.py`

18. `test_registry_contains_all_five_planner_contracts` — assert
    every name in `("PlanRequest", "PlannedSeed", "AdapterPrior",
    "FrontierPriorityHint", "PlanDecision")` appears in
    `FOUNDATION_CONTRACTS` with `replay_required=True` and
    `owner_service == OwnerService.AGENTS`.
19. `test_registry_validate_returns_ok` — regression check:
    `validate_registry().ok is True` after the new entries land.

### `tests/contract/test_crawl_planner_import_boundaries.py`

20. `test_ports_crawl_planner_imports_only_contracts_and_stdlib` —
    walk module AST; reject any import that is not stdlib or
    `veracrawl.contracts.*`.
21. `test_adapters_planning_deterministic_crawl_planner_imports_allowlist`
    — *(Iter-5 follow-up — post-iter-5 finding 1)*. **Allowlist**
    (not blocklist) check: walk the module's AST and require every
    `import` / `from ... import` resolves to one of stdlib,
    `veracrawl.contracts.*`, or `veracrawl.ports.crawl_planner`.
    Any other module — including internal runtime modules like
    `veracrawl.external_crawl.runner`, `veracrawl.agents.orchestration`,
    other adapters, or any third-party SDK — fails the test. This
    closes the gap codex flagged: a blocklist over named SDKs would
    miss accidental coupling to internal runtime modules.
22. `test_external_crawl_runner_does_not_import_crawl_planner_port`
    — guard against accidental s3 work landing in s1.

### `tests/unit/adapters/planning/test_deterministic_crawl_planner.py`

23. `test_emits_one_planned_seed_per_seed_url_in_order` — three
    seed URLs in input → three planned seeds in the same order;
    priorities `[1.0, 0.5, 1/3]` per
    `DeterministicCrawlPlanner.SEED_PRIORITY_DECAY`.
24. `test_adapter_hint_defaults_to_http_for_every_seed` — every
    `PlannedSeed.adapter_hint == AdapterType.HTTP`.
25. `test_adapter_priors_fixed_http_only_regardless_of_observed_state` —
    *(Iter-2 finding 2; smoke-test follow-up clarified typed
    comparison.)* Run the adapter twice: once with
    `observed_state_refs=[]` and once with
    `observed_state_refs=["graph-snapshot:ignored"]`. Both
    invocations MUST emit `decision.adapter_priors == [
    AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
    rationale_ref="rationale:deterministic-crawl-planner:http-only")
    ]`, i.e. exactly one typed `AdapterPrior` instance whose three
    fields equal the documented constants (comparison via
    `model_dump()` for stable equality). The previous draft used a
    tuple shorthand; the actual contract requires the full typed
    model.
26. `test_replay_refs_match_declared_emission_order` —
    `decision.replay_refs == [request.id,
    "adapter:deterministic-crawl-planner:v1",
    request.replay_config_ref, request.objective_ref]`. Byte-equal
    list comparison. *(Iter-1 finding 2.)*
27. `test_policy_decision_refs_forwarded_verbatim` — *(Iter-2
    finding 1)*. `request.policy_decision_refs == ["policy:a",
    "policy:b"]` → `decision.policy_decision_refs == ["policy:a",
    "policy:b"]` (list-equal; verifies forwarding, not synthesis).
    A second assertion verifies the adapter copied (mutating the
    request's list afterward does not change the decision).
27a. `test_request_ref_equals_request_id` — *(Iter-3 finding 1)*.
    Build a request with a specific `id` and assert
    `decision.request_ref == request.id`. The deterministic adapter
    must wire the request's `id` into the decision's `request_ref`;
    putting `request.id` in `replay_refs` alone is insufficient
    because an adapter could emit
    `decision.request_ref="wrong"` and still pass the replay-refs
    assertion. This test pins the provenance invariant.
28. `test_planner_is_pure_function_via_canonical_json` — *(Iter-2
    finding 3)*. Two calls with the same request return byte-equal
    `decision.canonical_json()` outputs (the helper lives on
    `VeraModel` in `src/veracrawl/contracts/common.py:43-44`). The
    previous iter-2 plan called the non-existent
    `model_dump_json(sort_values=True)` API.
29. `test_planner_implements_crawl_planner_port` — runtime check:
    `isinstance(adapter, CrawlPlannerPort)` (uses
    `@runtime_checkable`).

No test mocks `DeterministicCrawlPlanner` itself; tests instantiate
it with a real request and assert real outputs. *(Adversarial rule:
"tests that mock the thing under test".)*

### Green path

Each red test gets a minimal implementation. One purpose per
commit. After all 42 tests pass, refactor only to dedupe regex
constants and simplify validator messages.

## Acceptance Criteria

Mechanically verifiable from a fresh checkout.

1. **Pytest gate** —
   `pytest tests/contract/test_crawl_planner_contracts.py tests/contract/test_crawl_planner_contract_registry.py tests/contract/test_crawl_planner_import_boundaries.py tests/unit/adapters/planning/test_deterministic_crawl_planner.py -v`
   exits 0 with **42** collected, **42** passed, **0** failed,
   **0** errored. *(Iter-3 finding 1 added unit test 27a; iter-4
   finding 1 added 10 contract tests covering every declared
   non-blank-ref validator: 2a, 3a, 6a, 10b-10f, 14a, 14b;
   s1-step-1 task-review iter 2 follow-up added contract test
   10a-schema for the schema-level required-field invariant.)*
2. **Contract registry** —
   `python -c "from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry, OwnerService; names = ('PlanRequest','PlannedSeed','AdapterPrior','FrontierPriorityHint','PlanDecision'); assert all(n in FOUNDATION_CONTRACTS for n in names); assert all(FOUNDATION_CONTRACTS[n].replay_required for n in names); assert all(FOUNDATION_CONTRACTS[n].owner_service == OwnerService.AGENTS for n in names); assert validate_registry().ok"`
   exits 0.
3. **No runner wiring** —
   `python -c "import pathlib; assert 'crawl_planner' not in pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text()"`
   exits 0.
4. **Adapter imports respect the allowlist** — *(Iter-5 follow-up
   — post-iter-5 finding 1)*. The pytest gate's test 21 enforces an
   AST allowlist (stdlib + `veracrawl.contracts.*` +
   `veracrawl.ports.crawl_planner`); the redundant blocklist grep
   from earlier drafts is dropped because the allowlist is strictly
   tighter.
5. **Port has no adapter dep** —
   `python -c "import veracrawl.ports.crawl_planner as p; import inspect; assert 'veracrawl.adapters' not in inspect.getsource(p)"`
   exits 0.
6. **Behavior LOC budget** — *(Iter-1 finding 4 — recomputed)*
   `total=$(wc -l src/veracrawl/contracts/crawl_planner.py src/veracrawl/ports/crawl_planner.py src/veracrawl/adapters/planning/deterministic_crawl_planner.py | tail -1 | awk '{print $1}'); test "$total" -le 300`
   exits 0. The actual figure lands in STATUS on the s1 commit row.
7. **Codex plan-review gate via the documented hook** —
   *(Iter-1 finding 5)* the prereq shim is installed and
   `CODEX_REVIEW_ITERATION=N ~/.claude/hooks/codex-review.sh plan
   docs/plans/general-purpose-crawler-agentification/s1-crawl-planner-port-contract.md
   --project-dir $PWD` exits 0 with `VERDICT: APPROVED`, OR five
   iterations are exhausted with iter-5 findings addressed in a
   follow-up commit and the result recorded as
   `DONE_WITH_RESERVATIONS` per the goal doc's "post-iter-5
   follow-up" provision (mirrors
   `docs/plans/p0-fix-pack/STATUS.md`).
8. **Codex task-review gate via the documented hook** — each
   commit produced by this slice passes
   `BASELINE=$(git rev-parse HEAD~1) && CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD`
   within ≤ 5 iterations, or carries a recorded reservation.

## Rollback

s1 only adds new files plus five `FOUNDATION_CONTRACTS` dict entries
plus one `FrontierMatchKind` enum addition. Rollback is a single
`git revert <s1-commit-range>` — no migrations, no on-disk schema
changes, no consumer breakage (the runner does not import the port).
The registry edits are append-only; revert removes them cleanly. No
downstream consumers exist until s2.

## Open Questions

1. **`_is_http_url` reuse**: keep the private mirror in
   `contracts/crawl_planner.py` (default) or import from
   `contracts.agent`. Default decision stands; codex iter 2 may
   re-flag.
2. **`OwnerService.AGENTS` vs `OwnerService.PORTS`**: the contracts
   describe agent decisions, not generic port shapes. Default
   stands; codex iter 2 may re-flag.
3. **`PlannedSeed.parent_canonical_url`**: omitted in s1 because the
   caller passes seed URLs directly; deeper-discovery semantics are
   added in later slices when the runner enqueues from extracted
   links. Decision recorded; codex may revisit when s3 lands.
4. **`PlanRequest.seed_urls` ordering**: the deterministic adapter
   preserves input order; whether the *contract* requires order
   preservation across all adapters is a design decision deferred to
   s2 (LLM adapter). For s1 the test asserts adapter behavior, not
   contract requirement.
5. **Hook-shim prompt-body location**: the prereq lands the shim
   plus a prompt body file. Open question is whether the prompt
   bodies belong under the topic plan directory or a global
   `docs/plans/.codex-review-prompts/`. Default: topic directory
   for s1; promote to global if a second topic copies the bodies
   verbatim.
