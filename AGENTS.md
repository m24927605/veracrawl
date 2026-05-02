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

## Spec Kit Workflow

This repository uses GitHub Spec Kit for spec-driven development.

For non-trivial product, architecture, or code changes, follow the Spec Kit workflow before implementation.

Use the command form available in the current agent environment:

- Most Spec Kit integrations: `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement`
- Codex skills mode: `$speckit-constitution`, `$speckit-specify`, `$speckit-clarify`, `$speckit-plan`, `$speckit-tasks`, `$speckit-analyze`, `$speckit-implement`

Workflow:

1. Establish or update project principles with `/speckit.constitution` when the requested change affects engineering rules, product boundaries, safety policy, or long-term architecture.
2. Create or update the feature specification with `/speckit.specify`.
   - Describe what is being built and why.
   - Do not choose the tech stack in the specification phase unless the user explicitly asks.
   - Tie requirements back to the relevant VeraCrawl docs in `docs/`.
3. Run `/speckit.clarify` when requirements, acceptance criteria, safety boundaries, user roles, data contracts, or output semantics are ambiguous.
4. Create the technical implementation plan with `/speckit.plan`.
   - Include architecture choices, package/module boundaries, data contracts, migration impact, testing strategy, and rollout sequence.
   - For VeraCrawl V1 work, respect `docs/README.md`, `docs/01-product-definition.md`, `docs/02-production-architecture.md`, `docs/07-data-contracts.md`, and `docs/08-build-roadmap.md`.
5. Generate executable tasks with `/speckit.tasks`.
6. Run `/speckit.analyze` before implementation for cross-artifact consistency and coverage checks when available.
7. Implement with `/speckit.implement`, or manually execute the generated task list if the command is unavailable.

Spec Kit is initialized in this repo under `.specify/`, with Codex skills installed under `.agents/skills/`. If those directories are missing in a future checkout, reinitialize with `specify init --here --integration codex --integration-options="--skills"` before running non-trivial workflow steps.

## When To Require A Spec

Use the Spec Kit workflow for:

- new product features
- architecture changes
- data contract changes
- agent workflow changes
- safety, policy, credential, crawling, evidence, memory, graph, export, or replay behavior
- changes that touch multiple modules or persistence boundaries

Small mechanical fixes, typo fixes, formatting-only edits, or narrowly scoped documentation wording changes may be done directly, but mention that the full Spec Kit workflow was intentionally not used because the change is trivial.

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

For all Spec Kit plans and implementation tasks:

- Use Python for V1 services, workers, contracts, policy checks, event handling, and agent runtime abstractions.
- Keep the AI agent runtime framework-neutral and owned by VeraCrawl.
- Do not make core packages depend on LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or equivalent agent frameworks.
- Any model SDK or agent framework must live behind a replaceable adapter.
- Do not persist framework-native state as canonical state; persist VeraCrawl contracts, commands, events, policy decisions, tool calls, artifact refs, and replay records.
- Treat framework independence as an architecture acceptance criterion, not an implementation preference.

## Implementation Discipline

- Keep specs, plans, tasks, and code consistent. If implementation reveals a requirement mismatch, update the spec artifacts before continuing.
- Treat specs and plans as source-of-truth intent; code should implement them, not drift away from them.
- Keep task execution traceable to task IDs from `tasks.md`.
- Do not mark tasks complete unless the implementation and verification are actually done.
- Run the relevant tests or checks before finalizing; if a check cannot be run, state why.
- Preserve existing user changes. Do not revert unrelated work.

## Spec Kit References

- GitHub Spec Kit: https://github.com/github/spec-kit
- Spec Kit documentation: https://github.github.io/spec-kit/

<!-- SPECKIT START -->
Current active Spec Kit plan: `specs/012-review-replay-ops/plan.md`.
Use it with `specs/012-review-replay-ops/spec.md`,
`specs/012-review-replay-ops/research.md`,
`specs/012-review-replay-ops/data-model.md`,
`specs/012-review-replay-ops/contracts/`, and
`specs/012-review-replay-ops/quickstart.md` for VeraCrawl Review Replay Ops Console work.
<!-- SPECKIT END -->
