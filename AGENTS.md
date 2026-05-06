# Agent Instructions

## Hard Constraints

VeraCrawl must remain a general-purpose AI agent web crawler.

- Do not narrow VeraCrawl into a single-site scraper, browser automation demo, vertical intelligence product, or one-off extraction pipeline.
- Product specs, architecture plans, and code must preserve general-purpose crawling capability across many websites, source patterns, schemas, and data domains.
- Any V1/V2/V3 scoping must be treated as dependency and validation sequencing only; implementation must not bake in assumptions that prevent VeraCrawl from becoming a powerful general-purpose AI agent crawler.
- AI must be used to maximize website understanding, crawl planning, frontier prioritization, extraction, verification, repair, and learning while remaining bounded by policy and replay.

Code implementation must preserve low coupling and high cohesion.

- Keep domain contracts, policy, runtime events, service logic, adapters, and agent orchestration separated by explicit interfaces.
- Core packages must depend on stable contracts and ports, not on concrete worker internals, model SDKs, storage clients, queue clients, or agent frameworks.
- Each module should own one coherent responsibility and expose a small, typed API.
- Cross-module behavior must flow through commands, events, ports, and typed results rather than shared mutable state or hidden side effects.
- Do not introduce convenience imports, framework shortcuts, or global state that blur ownership boundaries.
- Treat low coupling and high cohesion as architecture acceptance criteria, not style preferences.

Do not let schedule concerns reduce the target product or architecture.

- VeraCrawl is implemented by Codex, so planning must not use human staffing limits, sprint pressure, deadlines, or delivery speed as reasons to shrink the product ambition.
- Do not choose a weaker architecture, narrower product model, lower-quality implementation, or less general crawler capability because it would be faster.
- Target architecture should be planned to the full desired capability of a powerful general-purpose AI agent web crawler.
- Sequencing is allowed only for technical dependency management, correctness, verification, risk isolation, and incremental integration.
- V1/V2/V3 boundaries must not be justified by time pressure; they must be justified by dependency order, system coherence, and validation strategy.

## Plan-Driven Development

Spec Kit has been removed from this repository. For non-trivial product, architecture, or code changes, follow the lightweight plan-driven workflow under `docs/plans/`.

Workflow:

1. Create a plan directory under `docs/plans/<topic>/` (e.g. `docs/plans/p0-fix-pack/`).
2. Write a self-contained plan document for each discrete change. Each plan must include: `Status`, `Why`, `Scope` (in/out), `Design`, `Dependencies`, `Test Strategy`, `Acceptance Criteria` (mechanically verifiable), `Rollback`, `Open Questions`.
3. Tie requirements back to the VeraCrawl docs in `docs/` — do not duplicate doc content; reference it.
4. Run the codex plan review gate before implementation:
   ```
   CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh plan <plan-file> --project-dir $PWD
   ```
5. Iterate the plan until codex approves (max 5 iterations); record iteration outcomes in the plan's status table.
6. Implement TDD: red → green → refactor → single-purpose commit.
7. Run the codex task review gate per commit:
   ```
   BASELINE=$(git rev-parse HEAD~1) && CODEX_REVIEW_ITERATION=1 \
     ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
   ```
8. Update the plan's STATUS.md (or equivalent) with commit SHA + outcome.

## When To Require A Plan

Use the plan-driven workflow for:

- new product features
- architecture changes
- data contract changes
- agent workflow changes
- safety, policy, credential, crawling, evidence, memory, graph, export, or replay behavior
- changes that touch multiple modules or persistence boundaries

Small mechanical fixes, typo fixes, formatting-only edits, or narrowly scoped documentation wording changes may be done directly, but mention that the full plan workflow was intentionally not used because the change is trivial.

## VeraCrawl V1 Constraints

Before planning or implementation, read the V1 entry points:

- `docs/README.md`
- `docs/01-product-definition.md`
- `docs/02-production-architecture.md`
- `docs/06-agent-system-design.md`
- `docs/07-data-contracts.md`
- `docs/08-build-roadmap.md`

V1 must stay inside the documented V1 profiles:

- static or mostly static HTML, sitemap, RSS, document metadata, listing/detail, pagination, canonical, and redirect patterns
- HTTP first; browser snapshots only after explicit approval
- records, tables, document metadata, and factual fields only
- local result materialization or Result API before production export connectors
- run diary only; no long-term memory planning prior until the Memory Kernel phase
- URL/page-structure graph only; no entity/task/temporal graph dependency in V1 acceptance paths

Do not confuse V1 acceptance with target architecture acceptance. V1-specific constraints apply only to the V1 production spine; target architecture planning and later implementation must still include the full graph, memory, browser, multi-agent, export, scale, and operations capabilities defined in `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.

## Python And Agent Framework Boundary

VeraCrawl is a Python product unless the user explicitly changes this decision.

For all plans and implementation tasks:

- Use Python for V1 services, workers, contracts, policy checks, event handling, and agent runtime abstractions.
- Keep the AI agent runtime framework-neutral and owned by VeraCrawl.
- Do not make core packages depend on LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or equivalent agent frameworks.
- Provide framework-neutral agent abstractions that can be implemented by adapters for OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or future frameworks without changing core contracts.
- Any model SDK or agent framework must live behind a replaceable adapter.
- Do not persist framework-native state as canonical state; persist VeraCrawl contracts, commands, events, policy decisions, tool calls, artifact refs, and replay records.
- Treat framework independence as an architecture acceptance criterion, not an implementation preference.

## Implementation Discipline

- Keep plans and code consistent. If implementation reveals a requirement mismatch, update the plan before continuing.
- Treat plans as source-of-truth intent; code should implement them, not drift away from them.
- Keep work traceable to plan acceptance criteria — each commit should map to one or more checked items.
- Do not mark items complete in STATUS.md unless implementation and verification are actually done.
- Run the relevant tests or checks before finalizing; if a check cannot be run, state why.
- Preserve existing user changes. Do not revert unrelated work.
