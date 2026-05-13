# General-Purpose Crawler Agentification — Status

Mirror of the row format in `docs/plans/p0-fix-pack/STATUS.md`.
One row per slice. Codex plan-review and per-commit task-review
iteration outcomes are recorded inline. `Reservations` links back to a
named subsection at the bottom of this file when iter-5 lands a
follow-up.

## Slice progress

| Slice | Title | Status | Plan commit | Implementation commits | Codex plan iter | Codex task iter | Reservations |
|-------|-------|--------|-------------|------------------------|-----------------|-----------------|--------------|
| s1 | `CrawlPlannerPort` + plan-decision contract + deterministic fixture adapter | IMPL_IN_PROGRESS | aca4f82 | step 1: c49f68a, 22e1966, d7b836d, 0f8472e (contracts + 29 tests, APPROVED iter 4) | iter 1 REJECTED, iter 2 REJECTED, iter 3 REJECTED, iter 4 REJECTED, iter 5 REJECTED (5/5 used; post-iter-5 follow-up landed without re-review) — see below | step 1: iter 1→2→3 REJECTED → iter 4 APPROVED — see below | 1 — see "s1 plan iter-5 reservations" below |

## s1 codex plan-review log

The goal doc references
`~/.claude/hooks/codex-review.sh plan <plan-file> --project-dir $PWD`.
That hook is not installed on this machine
(`ls ~/.claude/hooks` is empty). The codex CLI itself is present
(`codex-cli 0.130.0`, authenticated via ChatGPT login). The
plan-review gate is exercised via the codex companion runtime
`node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task <prompt>`
with an adversarial reviewer prompt recorded at
`/tmp/codex-plan-review-prompt.txt`. The substitution is recorded
here so a future audit can compare the prompt body against the
hook-installed version once landed.

| Iter | Date (UTC)        | Verdict  | Findings (severity — summary) | Resolution |
|------|-------------------|----------|-------------------------------|------------|
| 1    | 2026-05-13        | REJECTED | (1) blocker — `PlanRequest` carries only `objective_ref`; adapter cannot produce seeds because `CrawlObjective` has no `plan_ref` and `site_scope_refs` are refs, not URLs. (2) blocker — `PlanDecision` validator requires `request_ref` in `replay_refs` but adapter / test omit it. (3) major — second port `ObjectiveResolverPort` violates "one coherent capability behind one port". (4) major — 330 LOC behavior delta exceeds binding ≤300 cap; pydantic validators are not generated code. (5) major — Acceptance Criteria 7-8 bypass the binding `codex-review.sh` hook. | s1 plan revised to v2: `PlanRequest.seed_urls: list[str]` (planner triages caller-provided URLs); `ObjectiveResolverPort` dropped; `replay_refs` validator + adapter + test made consistent (`request_ref` + `planner_adapter_ref` required); LOC budget recomputed ≤300; prereq added to install `~/.claude/hooks/codex-review.sh` shim before s1 lands. Iter 2 follows. |
| 2    | 2026-05-13        | REJECTED | iter-1 findings all closed (per codex). 3 new majors: (1) `policy_decision_refs` populated with `request.policy_snapshot_ref` (a `RunPolicySnapshot` ref) — mislabel; real `PolicyDecision` refs needed. (2) Adapter-prior cardinality branch on `observed_state_refs` is ref-shape behavior leaking future graph-feedback semantics into s1. (3) Test 29 calls non-existent `model_dump_json(sort_values=True)` API; the repo's stable serialization is `VeraModel.canonical_json()`. | s1 plan revised to v3: `PlanRequest.policy_decision_refs: list[Ref]` (≥1) added; adapter forwards request refs verbatim. Deterministic adapter emits a single fixed `adapter_priors=[(HTTP, 1.0)]` regardless of `observed_state_refs` (slot preserved for s5). Test 28 rewritten to assert `adapter.plan(request).canonical_json()` byte-equality (test numbering aligned). Observed-state branching test dropped. Iter 3 follows. |
| 3    | 2026-05-13        | REJECTED | iter-2 findings all closed (per codex). 1 major + 1 minor: (major) `PlanDecision.request_ref` is specified to equal `PlanRequest.id` but no red test mechanically asserts it — an adapter could emit a wrong `request_ref` while still putting `request.id` in `replay_refs` and pass. (minor) Status table referred to "test 29" for the `canonical_json` fix but revised red list names it test 28; trail should match. | s1 plan revised to v4: new red unit test 27a `test_request_ref_equals_request_id` asserts `decision.request_ref == request.id` for the deterministic adapter; pytest count bumped from 30 to 31; STATUS rows aligned to actual red list numbering. Iter 4 follows. |
| 4    | 2026-05-13        | REJECTED | iter-1/2/3 findings all closed (per codex). 1 major: several declared contract validator invariants (non-blank scalar refs on `PlanRequest`, non-blank `rationale_ref` on `PlannedSeed`/`AdapterPrior`/`FrontierPriorityHint`, non-blank `request_ref`/`planner_adapter_ref` on `PlanDecision`) are NOT mechanically asserted by any red test — an implementation could leave the validators out and still pass the 31-test pytest gate. | s1 plan revised to v5: 10 discrete red tests added (2a, 3a, 6a, 10b–10f, 14a, 14b) covering every previously-untested non-blank-ref invariant; pytest count bumped from 31 → 41. Iter 5 follows. |
| 5    | 2026-05-13        | REJECTED (5/5 used; post-iter-5 follow-up landed without re-review) | iter-1/2/3/4 findings all closed (per codex). 1 major + 1 minor: (major) adapter import-boundary test 21 uses a blocklist regex over named SDKs — an implementation could import internal runtime modules (`veracrawl.external_crawl.runner`, `veracrawl.agents.orchestration`) or other adapters and still pass. (minor) topic README line 38 still described the obsolete `CrawlObjective → PlanDecision` shape rather than the revised `PlanRequest(seed_urls=...) → PlanDecision` shape. | Post-iter-5 follow-up landed in the same plan revision (not re-reviewed per goal-doc workflow): test 21 rewritten as a strict AST **allowlist** (`stdlib` + `veracrawl.contracts.*` + `veracrawl.ports.crawl_planner` only); acceptance criterion 4 **rewritten** to reference the allowlist test (rather than dropped — earlier note corrected); README line 38 + smallest-viable-first-slice paragraph updated. A second post-iter-5 follow-up (after the hook-shim smoke test surfaced new findings) corrected `adapter_priors` Scope + test 25 from tuple-shorthand `[(HTTP, 1.0)]` to the typed `[AdapterPrior(adapter_type=HTTP, weight=1.0, rationale_ref=...)]` the contract actually requires. Plan recorded as `PLAN_DONE_WITH_RESERVATIONS` per goal doc's "iter-5 rejects but issues are addressable" provision. See "s1 plan iter-5 reservations" below. |

## s1 step-1 (contracts) task-review log

| Iter | Date (UTC) | Commit  | Verdict  | Findings (severity — summary) | Resolution |
|------|------------|---------|----------|-------------------------------|------------|
| 1    | 2026-05-14 | c49f68a | REJECTED | (major) `contracts/crawl_planner.py` 251 LOC vs ≤130 per-file budget. (major) `PlanRequest.policy_decision_refs` declared `Field(default_factory=list)` despite being a required invariant. | Follow-up commit 22e1966 compacted to 129 LOC via `_require` helper + tighter messages; removed the default factory from `policy_decision_refs`. |
| 2    | 2026-05-14 | 22e1966 | REJECTED | (major) Removing the default factory was not mechanically covered by a red test (test 10a passes with the defaulted-empty implementation). (minor) 13 lines exceed ruff's 100-char cap. | Follow-up commit d7b836d added `test_plan_request_rejects_missing_policy_decision_refs`; shortened validator error messages so every line ≤100 chars; ruff `All checks passed!`. |
| 3    | 2026-05-14 | d7b836d | REJECTED | (major) The new test isn't in the s1 plan's Test Strategy red list; AC1 still requires 41 collected (now 42). (minor) Commit message doesn't reference the s1 slice ID + AC. | s1 plan revised: test 10a-schema added to red list; AC1 bumped 41 → 42; green-path total updated. Next commit message will explicitly reference s1 + AC1. Follow-up commit lands the plan update. |
| 4    | 2026-05-14 | 0f8472e | APPROVED | (minor) Inline s1 status iter-5 row still said "AC4 dropped" while STATUS correctly said "AC4 rewritten". | Step 1 (contracts) closed. The minor is addressed in this same doc-cleanup commit (the iter-5 row note now says "rewritten"). |

## s1 plan iter-5 reservations

Mirrors the `docs/plans/p0-fix-pack/STATUS.md` reservations pattern.

**Reservation 1 — iter-5 post-iter-5 follow-up not re-reviewed.**
Iteration 5 returned `REJECTED` with one major (test 21
blocklist→allowlist) and one minor (README line 38 shape mismatch).
Both findings were addressed in a post-iter-5 follow-up in the same
plan revision (test 21 rewritten as an AST allowlist; README updated).
Per the goal doc's `~/.claude/hooks/codex-review.sh` workflow, the
allowed iteration count is exhausted at five — the follow-up was
**not** sent through codex for a sixth review. The s1
**implementation** is consequently expected to either:

- exercise the follow-up via the per-commit task-review gate (which
  runs `codex-review.sh task <baseline>` against the diff) — codex
  will independently flag the allowlist regression risk if any
  emerges, since the implementation commits are themselves reviewed;
  OR
- if codex-task-review escalates the same finding back, treat that
  feedback as a normal task-review iteration on the implementation
  commits, not as a reopened plan iteration.

This reservation will be discharged when the s1 implementation
commits land green through the task-review gate. The discharge entry
will reference the relevant commit SHAs from a future
"Implementation commits" column update on the s1 row.

**Reservation 2 — `codex-review.sh` hook substitution.** *(DISCHARGED 2026-05-14.)*
The goal doc and AGENTS.md mandate the documented hook
`~/.claude/hooks/codex-review.sh`; at the time of iter 1–5 the hook
was not installed on this machine. The plan-review gate for iter
1–5 was exercised via `node
"${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task <prompt>`
with the adversarial prompt bodies preserved at
`/tmp/codex-plan-review-iter{1..5}-prompt.txt`. **Discharged**:
`~/.claude/hooks/codex-review.sh` is now installed (executable,
5293 bytes) and delegates to the codex-companion runtime via the
standardized prompt bodies versioned in
`docs/plans/general-purpose-crawler-agentification/codex-review-prompts/{plan,task}.md`.
A smoke-test invocation (`CODEX_REVIEW_ITERATION=6 codex-review.sh
plan <s1-plan>`) confirmed the hook returns the same adversarial
verdict shape as the manual codex-companion invocations did during
iter 1–5, and surfaced two follow-up findings (tuple-shorthand in
`adapter_priors`, AC4 stale-drop note) which were landed in the
plan as additional post-iter-5 corrections. All future s2/s3
plan-reviews and s1 per-commit task-reviews use the documented
hook path.
