# General-Purpose Crawler Agentification — Plan Topic

Closes the gap between the repository's current state and the README's
"general-purpose AI agent web crawler" claim, in the order mandated by
`docs/plans/general-purpose-crawler-agentification-goal.md` and bound by
the AGENTS.md hard constraints (general-purpose, low coupling / high
cohesion, no schedule-driven scope cuts).

## Audit-anchored starting state

The goal document records a Staff audit (do not re-discover). The
agent loop that wires *objective → adapter choice → frontier priority
→ extraction strategy* does not exist as runtime — only as
scenario-string dict-lookup fixtures inside
`src/veracrawl/agents/orchestration.py` (`run_multi_agent_repair`
dispatches on `scenario` strings; the planner role is never invoked
with a real `CrawlObjective`). `src/veracrawl/external_crawl/runner.py`
constructs the frontier directly from `CrawlJobSpec.seed_urls` and
imports zero `graph_*` symbols, so there is no closed loop between
the live runner and the agent contract spine. Slice 1 introduces the
contract surface that turns that loop into a wired-in port.

## Slice sequence

Slices are listed in dependency order. Each slice is one plan file +
one STATUS row. Scope per slice is ≤ ~300 LOC behavior excluding
tests + generated contract code. Each slice maps to one of the seven
capability priorities defined in the goal document.

The first three slices (s1–s3) deliver capability 1 end-to-end —
each strictly smaller than "wire LLM into the live runner" so the
sequence enforces the goal doc's
`contract+port → fixture-mode adapter → production adapter →
runtime-spine wiring → live integration test` decomposition.

| Slice | Title | Capability | One-line scope |
|-------|-------|------------|----------------|
| s1 | `CrawlPlannerPort` + plan-decision contract + deterministic fixture adapter | 1 | Introduce the port and the typed `PlanDecision` contract; ship one deterministic adapter that maps `PlanRequest(seed_urls=[...], objective_ref=...)` → `PlanDecision` (with replay refs). No LLM. No runner wiring. |
| s2 | Real LLM-driven `CrawlPlanner` adapter (replay-strict) | 1 | Real LLM adapter consuming s1 port; composes existing v2 `ModelProviderPortV2` + `PromptRegistryPort` + `TokenBudgetPort`; **requires** `ProviderResponse.raw_response_ref` (non-blank) and writes the full 7-entry replay-ref list (`request.id`, `adapter_ref`, `replay_config_ref`, `objective_ref`, `prompt_template_ref`, `response.id`, `raw_response_ref`) into `PlanDecision.replay_refs`. Live deployment requires the directly-dependent follow-up slice s2.1 (provider-artifact wiring) to populate `raw_response_ref` on the OpenAI/Anthropic v2 adapters — running s2 against the current production providers as-is fails fast with `ProviderTraceMissingError` (desired safety property). |
| s2.1 | Provider-artifact wiring for OpenAI/Anthropic v2 adapters | 1 | Directly-dependent follow-up to s2: persist raw provider response bytes to the artifact store via `ArtifactStorePort` and populate `ProviderResponse.raw_response_ref` on every `complete(...)` call. Unlocks live use of the s2 LLM planner; same wiring serves any future `ModelProviderPortV2` consumer (`SchemaExtractionRuntime`, etc.). |
| s3 | `ExternalCrawlRunner` wires `CrawlPlannerPort` (planned-seed scheduling) | 1 | Runner invokes the planner before seed enqueue; sorts `decision.planned_seeds` descending by `priority_score` (stable, ties → emission order) and feeds them into the existing FIFO frontier; persists six planner-derived keys into the run report — `plan_decision_ref`, `plan_decision_replay_refs`, `plan_decision_frontier_priority_hints`, `plan_decision_adapter_priors`, `plan_decision_planned_seed_order`, `plan_decision_extraction_strategy_refs` — so future slices can consume them without re-running the planner. Live integration test against `httpbin.org`. (Iter-1 narrowing: actual `frontier_priority_hints` application lands in s3.1; `adapter_priors` consumption in s3.2; extraction-strategy execution in s10.) |
| s3.1 | Priority-queue `ExternalCrawlFrontier` consumes `frontier_priority_hints` | 1 | Swap the FIFO frontier for a heap-based priority queue keyed by `(depth + hint_delta, enqueue_order)`. Consumes `plan_decision_frontier_priority_hints` recorded by s3's run report. Directly dependent on s3. |
| s3.2 | Multi-adapter dispatch consumes `adapter_priors` | 1 | Runner accepts a `dict[AdapterType, CrawlHttpFetcherPort-like]` and routes URLs based on weighted sampling over `plan_decision_adapter_priors`. Directly dependent on s3. |
| s4 | `GraphObservationPort` + URL/canonical/redirect/structure event contracts | 2 | Port whose adapters consume frontier and fetch events to write into the URL/page-structure graph. Deterministic fixture adapter records events; no `graph_memory` import yet inside the runner. |
| s5 | `PlannerObservationFeedback` contract + deterministic fixture planner adapter v2 | 2 | Introduces the typed `PlannerObservationFeedback` — a **typed read projection** of a graph snapshot, carrying derived `redirect_neighbours` / `canonical_targets` / `page_neighbour_count_by_url` only (no public snapshot field; the snapshot is consumed at derive time and not stored on the contract). New `DeterministicCrawlPlannerV2` consumes the feedback via its constructor; caller threads `feedback.id` through the existing s1 `PlanRequest.observed_state_refs` slot. Adapter emits `HOST_GLOB` / `URL_PREFIX` `frontier_priority_hints` for redirect neighbours, canonical targets, and hub pages (`discovered_link_count ≥ 5`). No runner wiring. |
| s6 | Runner persists graph events during real runs and re-invokes planner on frontier-empty | 2 | Live wiring of s4 + s5: runner constructs an observer adapter per run, records events as fetches/redirects/parses happen, builds a snapshot at planner-invocation time, derives a `PlannerObservationFeedback`, threads `feedback.id` into `PlanRequest.observed_state_refs`, and re-invokes the planner on frontier-empty. Replay re-runs deterministically given the snapshot (`feedback.id` participates in `decision.replay_refs`). |
| s7 | `ExtractionStrategyPort` (open-schema discovery) + deterministic fixture adapter | 3 | Strategy port emits a `SchemaProposal` from a normalized document; fixture adapter proposes flat-field schemas from anchor distributions. No LLM. |
| s8 | `DriftDetectionPort` + `RepairPort` contracts + deterministic fixture adapters | 3 | Two ports for catching schema drift across pages and proposing structural repairs; fixture adapters detect missing-field rates and propose anchor reselection. |
| s9 | LLM adapters for s7 + s8 via `ModelProviderPortV2` | 3 | Production adapters wired behind s7/s8; replay refs include prompt-template + model-call-trace; PRODUCTION-mode only. |
| s10 | `SchemaExtractionRuntime` consumes s7–s9 on real pages | 3 | Runner pipes per-page normalized docs through strategy → extract → drift → repair; live integration test against one new fixture site. |
| s11 | `ReplayConsumerPort` consumes `clock_ref` / `seed_ref` / `model_response_refs` | 4 | Port + deterministic fixture adapter that replays a bundle into deterministic stubs for clock + RNG + model responses. |
| s12 | `ExternalCrawlRunner` reads `replay_config_ref` and routes non-determinism through `ReplayConsumerPort` | 4 | Runner consumes the bundle when present; bypass otherwise. Unit + contract tests. |
| s13 | Live byte-identical re-execution test for one corpus | 4 | End-to-end: record run → replay → byte-equal diff for artifacts + run_report. `@pytest.mark.live`. |
| s14 | SQLite `EventStorePort` adapter wired into `control/runtime.py` by default | 5 | Replace `InMemoryEventStore` default with the SQLite adapter (already exists); migration plus regression tests. |
| s15 | Filesystem-with-content-hash `ArtifactStorePort` default at the runtime spine | 5 | Replace `ReferencePersistenceStore` default with the hashed-filesystem adapter; regression tests for outbox and replay refs. |
| s16 | `WorkerLeasePort` + queue-consumer loop (fixture mode) | 6 | Port for leased work consumption honoring AIMD + budget gates; deterministic single-process fixture adapter. |
| s17 | Multi-process worker pool consumer (production adapter) | 6 | Real worker pool consuming the queue, sharing the AIMD + budget state via outbox; live integration test. |
| s18 | Real-site acceptance corpus: three unfamiliar sites end-to-end | 7 | Fixtures + `@pytest.mark.live` corpus exercising plan → fetch → extract → publish on three sites the existing test suite never touched. |

## Smallest viable first slice

s1 is the smallest slice that begins unlocking capability 1. Capability 1
("agent planning loop wired into `ExternalCrawlRunner`") requires three
things: (a) a typed contract for the planner's output, (b) a fixture
adapter that exercises that contract end-to-end, and (c) runner wiring.
Per the goal doc's `contract+port → fixture → production → wiring →
live` rule, s1 covers only (a) + a deterministic (b); the LLM
production adapter is s2 and runner wiring is s3.

s1 is contract-first: it introduces `CrawlPlannerPort` (a port the
runner will eventually depend on) plus `PlanRequest`, `PlannedSeed`,
`AdapterPrior`, `FrontierPriorityHint`, and `PlanDecision`
contracts. The caller passes candidate seed URLs through
`PlanRequest.seed_urls`; the planner triages them into a typed
`PlanDecision`. s1 ships one deterministic adapter so the contract
surface is exercised end-to-end by tests, but it does **not** import
any model SDK, browser engine, persistence client, or internal
runtime module, and `external_crawl/runner.py` is not modified in
this slice. That keeps s1 well under the ≤ ~300 LOC behavior delta
and isolates the contract surface from later changes.

## Out of scope (topic-wide)

- Agent framework adoption (LangChain / LangGraph / CrewAI / AutoGen /
  Semantic Kernel). The topic's slices keep the agent runtime
  framework-neutral per AGENTS.md "Python And Agent Framework
  Boundary".
- New product features outside the seven capability priorities.
- V1-only narrowing of the planner contract. The contract surface
  must remain general-purpose across HTTP / sitemap / RSS / browser /
  document adapters (AGENTS.md hard constraint).

## STATUS

Slice progress lands in `STATUS.md` (created at slice 1 land), mirroring
the row format of `docs/plans/p0-fix-pack/STATUS.md`. Codex iteration
outcomes and reservations are recorded per row.
