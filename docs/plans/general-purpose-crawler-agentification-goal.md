# Goal — General-Purpose Crawler Agentification

> Intended use: paste into `/goal` (or instruct the executing team to read this file in full and act on it). Closing the gap between today's repository state and the README's "general-purpose AI agent web crawler" claim.

---

You are a Staff-level VeraCrawl engineering team entering PLAN mode. Your goal is to close the gap between today's repository state and the README's "general-purpose AI agent web crawler" claim, strictly honoring AGENTS.md hard constraints (general-purpose, low-coupling/high-cohesion, no schedule-driven scope cuts).

## Repository context — verified Staff audit findings (do not re-discover)

EXECUTABLE TODAY (real, runtime-enforced):
- ExternalCrawlRunner: real HTTP/sitemap/RSS, redirect lineage, robots, AIMD, Retry-After (HTTP-date), PDF/OCR (extras), Playwright snapshot
- Pydantic contract spine: `publish/gates.py:52-191` structurally enforces evidence/coverage/verification/review/policy/replay refs before publication
- LLM providers: OpenAI/Anthropic v2 wire-level adapters with PRODUCTION mode; single-page fixed-schema extraction pilot via `processing/schema_extraction_runtime.py` + `scripts/pilot_schema_runtime.py`
- Credential boundary: `strict_allowlist_scope.py` + `OutboxVaultClient` + outbox-backed token budget

SCAFFOLDED ONLY (scenario-string fixtures, not runtime):
- `target_runtime/*` — fixture template synthesis; no objective→plan→adaptive-frontier loop
- `agents/orchestration.py` — scenario-string dict lookup; planner / drift / repair / adapter-choice all fixtures
- `graph/`, `graph_memory/`, `memory/` — fixture builders; `external_crawl/runner.py` imports zero graph symbols; `projection/` is an empty package
- Deterministic replay — validates manifest presence only; `clock_ref` / `seed_ref` never consumed
- `control/runtime.py` — wired to `InMemoryEventStore` + `ReferencePersistenceStore` (JSON files); SQLite/Postgres/Redis/S3 adapters exist but not wired into the spine
- `scale/worker_orchestration.py` — ref-string fixtures, no actual worker pool
- 9 live tests against httpbin/example.com; 0 fixtures exercising an unfamiliar site end-to-end

## Mandate

Produce a plan-driven workstream that lifts the AI-agent crawler from "spine + narrow pilot" to "general-purpose AI agent crawler". Sequence by technical dependency, not schedule.

Capability priority — do not reorder unless your plan's Dependencies section justifies it:

1. Agent planning loop wired into `ExternalCrawlRunner` (objective → adapter choice → frontier priority → extraction strategy)
2. Graph → planner feedback (URL/canonical/redirect/page-structure graph captured during real runs and consumed by frontier prioritization)
3. LLM-driven extraction beyond fixed-schema pilot (open-schema discovery + drift detection + repair on real pages)
4. Deterministic replay re-execution (consume `clock_ref` / `seed_ref`; byte-identical re-run for ≥1 corpus)
5. Production backend wiring at the runtime spine (`control/runtime.py` uses SQLite or Postgres event store + persistent artifact store by default)
6. Multi-process scale (worker pool + queue consumer loop honoring AIMD + budget gates)
7. Real-site acceptance corpus (≥3 unfamiliar sites end-to-end through plan → fetch → extract → publish)

## Slicing rules (binding)

Each slice = one plan file under `docs/plans/<topic>/<slice-id>-<name>.md` and one STATUS row. Each slice MUST:

- Cover one coherent capability behind one port/contract (single-responsibility; no "and also" scope)
- Behavior delta ≤ ~300 LOC excluding tests + generated contract code (justify any exception in Scope)
- Have mechanically verifiable Acceptance Criteria (pytest selector, contract registry assertion, CLI exit code, scripted check)
- Declare Dependencies explicitly (earlier slice IDs whose contract/port this consumes)

If a capability cannot be sliced this small, split into: `contract+port` → `fixture-mode adapter` → `production adapter` → `runtime-spine wiring` → `live integration test`, each its own slice.

## Per-slice workflow (binding; matches AGENTS.md "Plan-Driven Development" and `docs/plans/p0-fix-pack/STATUS.md` pattern)

For every slice, in order:

1. Write the plan file with sections: `Status`, `Why` (tie to AGENTS.md hard constraints + audit gap), `Scope` (in/out), `Design` (ports/contracts/data flow), `Dependencies`, `Test Strategy` (red list first), `Acceptance Criteria` (mechanically verifiable), `Rollback`, `Open Questions`.

2. Run the codex plan-review gate adversarially with codex as reviewer:

   ```bash
   CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh plan docs/plans/<topic>/<slice-id>-<name>.md --project-dir $PWD
   ```

   Iterate ≤5 until codex approves. Record every iteration's verdict + findings in the plan's Status table. If iter-5 rejects but issues are addressable, land a post-iter-5 follow-up commit and record as `DONE_WITH_RESERVATIONS` with a `reservations` subsection (mirror `docs/plans/p0-fix-pack/STATUS.md`).

3. Implement TDD: red test → minimal green → refactor. One purpose per commit. No drive-by changes.

4. Run the codex task-review gate adversarially per commit:

   ```bash
   BASELINE=$(git rev-parse HEAD~1) && CODEX_REVIEW_ITERATION=1 \
     ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
   ```

   Treat codex as an adversarial reviewer — every finding gets either a fix, an evidence-backed refutation, or a recorded reservation. Iterate ≤5.

5. Update `docs/plans/<topic>/STATUS.md`: step row with commit SHAs, codex iter outcome, reservations.

## Quality standards (binding)

- AGENTS.md hard constraints: general-purpose only (never narrow to a single site), low coupling / high cohesion (cross-module flow only via commands / events / ports / typed results), no schedule-driven scope cuts.
- No new module imports a model SDK, browser engine, storage/queue client, or agent framework outside its adapter — core/contracts stay framework-neutral.
- Every public function returns a typed contract object; no dict-of-anything.
- Pydantic models: `extra="forbid"`, UTC-only datetimes, content-hash where applicable (match `contracts/common.py:38-58`).
- Evidence-first invariant: any new publication path must go through `publish/gates.py`.
- Replay invariant: anything that introduces non-determinism (random, time, model output) writes a ref into the replay bundle, and the consumer is wired in the same or a directly dependent slice.
- Tests: `tests/contract/` for schema invariants, `tests/unit/` for port logic, `tests/integration/` for runtime composition. New live-network tests gated by `@pytest.mark.live`.
- No `NotImplementedError`, scenario-string dict-lookup substitute, or placeholder ref-synth in a green commit. No `TODO` without an issue ID or plan reference.

## Adversarial code review standard (what codex will hold us to)

Expect codex to flag and reject on:

- Hidden coupling (imports across module boundaries that should go through a port)
- Missing replay refs on any new non-determinism
- Pydantic models without strict config or with default-everywhere fields
- Tests that mock the thing under test, or assert ref-shape only without behavior coverage
- Acceptance criteria that aren't mechanically verifiable
- Scope creep ("and also") within a single slice
- Schedule-driven shortcuts violating AGENTS.md
- Re-export / placeholder / scenario-string dict-lookup substitutes for real logic
- Per-site assumptions baked into general-purpose modules

Every finding must be addressed before DONE. Carry-overs become explicit STATUS reservation rows.

## First task in this `/goal` session — plans only, no production code

1. Create `docs/plans/general-purpose-crawler-agentification/` (new topic directory).
2. Write the topic-level `README.md` listing the planned slice sequence (one-line scope per slice) in dependency order, mapped to the 7 capability priorities above. Identify the smallest viable first slice that begins unlocking the agent planning loop.
3. Write the first slice plan file (`s1-<short-name>.md`) in full per the schema. Choose a contract-first slice that introduces a new port (e.g. `CrawlPlannerPort` or `ObjectiveInterpreterPort`) with a fixture-mode adapter only — no LLM call yet, no runner wiring yet.
4. Run the codex plan-review gate on the s1 plan file and iterate per workflow until approved (≤5 iters).
5. Stop and report back: the topic README, the s1 plan file path, codex iter outcomes, and proposed s2 / s3 slice headers (titles + scopes only, no full plan files yet).

Do not implement production code in this turn. Plans only. Codex plan-review must be exercised on slice 1 before stopping.
