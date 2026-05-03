# Production-first Build Roadmap

The user intent is to skip a toy scraper and build a production-grade, general-purpose AI agent web crawler. That is reasonable if "production-grade" means building the foundation for AI-guided crawling first, not shipping every advanced feature at once.

This roadmap avoids a toy implementation while still sequencing risk. The first build must prove that a high-level user objective can become an AI-proposed crawl plan, durable crawl execution, evidence-backed extraction, and replayable results.

This roadmap must not be used to reduce target architecture. V1/V2/V3 are dependency and validation boundaries only. Target completion requires the full capability, implementation, testing, and operational acceptance gates defined in [09-target-capability-model.md](09-target-capability-model.md), [10-target-implementation-design.md](10-target-implementation-design.md), and [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).

## V1 Product Slice

V1 is not the full multi-agent platform. It is the smallest coherent production spine for a general-purpose AI crawler:

```text
User objective
  -> core objective interpreter
  -> approved crawl plan
  -> policy-checked fetch and processing tasks
  -> normalized snapshots
  -> extraction candidates for declared schemas
  -> evidence packets
  -> verification decisions
  -> published outputs
  -> replay report and minimal review surface
```

V1 scope:

- static or mostly static HTML, sitemap, RSS, document, listing/detail, pagination, canonical, and redirect patterns
- HTTP adapter first, browser snapshot adapter only when policy permits and cost is tracked
- declared schemas first; exploratory schema proposals can exist but must be approved before publication
- V1 outputs focus on records, tables, document metadata, and factual fields; file and dataset workflows are later expansions
- one core planning agent and one site understanding/extraction loop before full multi-agent orchestration
- minimal evidence/replay/review surface before the full console; a static report alone is not sufficient for plan approval and output review

V1 benchmark:

- every crawl has an objective, approved plan, policy decisions, and replay report
- every published output has an evidence map
- every mutating or publication-relevant agent action has 100% replay lineage
- failed or blocked sources are reported rather than bypassed
- time to first approved plan, review time per output, accepted output precision, usable schema coverage, and successful export delivery are measured

## V1 Build Packs

Build V1 in packs so Phase 0 does not become an unbounded platform design phase:

1. Foundation pack: V1 contract profile, Project/Site, policy, command/event, approvals, state/reference/field-presence validation.
2. Runtime pack: objective, plan, job, run, scheduler, frontier, HTTP fetch, snapshot, retry, budget gates.
3. Normalize/extract pack: normalized document, normalization manifest, link provenance, site model, page type classification, extraction strategy, candidate.
4. Evidence/publication pack: evidence packet, verification decision, published output, output manifest, evidence coverage map, review decision, run diary.
5. Quickstart result pack: local JSON materialization, Result API, lightweight delivery receipt.
6. Later packs: advanced graph, memory kernel, browser scale-out, warehouse/database exports, export withdrawal, cross-site tunnels, vector search.

Each pack states owner service, storage target, API exposure, event dependencies, and exit tests before implementation starts.

| Pack | Owner service | Storage target | API exposure | Event dependencies | Entry criteria | Exit criteria |
| --- | --- | --- | --- | --- | --- | --- |
| Foundation | control-api | Postgres | internal + CLI init | command, approval, policy events | docs accepted | V1 profile validation rejects forbidden values |
| Runtime | scheduler + fetch worker | Postgres + object store | objective/plan/run APIs | frontier, fetch, snapshot events | foundation pack complete | one HTTP run writes snapshot and replayable events |
| Normalize/extract | normalize/extract worker | object store + Postgres | internal processing APIs | processing, candidate events | runtime pack complete | normalized document, anchor maps, candidate created |
| Evidence/publication | evidence + verification + publication services | Postgres + object store | review APIs | evidence, verification, output, review events | normalize/extract pack complete | evidence-backed output passes coverage and review |
| Quickstart result | publication service | local file + Result API | result API + CLI materialize | result_materialized event | evidence/publication pack complete | local JSON result, receipt, replay report created |
| Later graph/memory/export | graph/memory/export workers | graph/search/vector/export stores | later APIs | later event subsets | V1 spine verified | required for target architecture, not required for V1 acceptance |

## Post-037 Spec Roadmap

Specs 001-037 establish the executable target-architecture foundation and target
runtime gates. Production work after 037 must follow this fixed roadmap. Do not
create additional production implementation specs unless this section and
`specs/038-production-runtime-closure/spec.md` are amended first.

| Spec | Name | Purpose | Blocking dependencies | Completion gate |
| --- | --- | --- | --- | --- |
| 038 | Production Runtime Spec Roadmap | Control the remaining production spec set and prevent ad hoc spec expansion. | 037 | Specs 039-054 are defined with purpose, dependency, and completion gate. |
| 039 | Production Run Control API | Make objectives, projects/sites, plans, approvals, run lifecycle, budgets, and policy snapshots executable beyond fixtures. | 038 | Implemented by `veracrawl-run-control`: a run can be created, approved, blocked, resumed, cancelled, and replayed through canonical commands/events. |
| 040 | Production Persistence Runtime Wiring | Wire target runtime through production Postgres/object/queue ports without coupling core to clients. | 039 | Implemented by `veracrawl-production-persistence`: row 039 canonical state, artifacts, events, outbox, idempotency, and queue leases survive adapter reopen and replay through port-shaped persistence wiring. |
| 041 | Live HTTP Acquisition Runtime | Implement policy-gated live HTTP acquisition with redirects, canonical URLs, headers, content hashes, snapshots, and replay refs. | 039, 040 | Implemented by `veracrawl-live-http`: authorized local HTTP acquisition composes row 039/040 refs, adapter-owned HTTP, network/source acquisition refs, target source observations, artifacts, canonical URL refs, and typed unsafe/fake-acquisition failures without direct-source bypass. |
| 042 | Structured Source Adapters Runtime | Add sitemap, RSS/feed, API-like, document, and file-import source adapters behind source ports. | 041 | Implemented by `veracrawl-structured-source`: sitemap/RSS/API/document/file-import adapters produce source adapter result refs, parsed natural output refs, artifacts, evidence seed refs, policy refs, command/event/outbox refs, and replay refs, with malformed/policy/unsupported/replay negative fixtures. |
| 043 | Browser Snapshot Runtime | Add policy-gated browser snapshot adapter with rendering budget, sandboxing, network trace, DOM/screenshot artifacts, and replay. | 041, 042 | Browser-required fixtures pass only with browser artifacts and fail on unsafe/cost/prompt-taint cases. |
| 044 | Credentialed Session Runtime | Add authorized session and credential-use runtime without leaking secrets or bypassing scope. | 039, 041, 043 | Credentialed fixtures prove vault boundary, credential audit, redacted replay, and out-of-scope denial. |
| 045 | Live Normalization And Site Understanding | Convert acquired artifacts into normalized documents, anchor maps, page classifications, site models, and link provenance. | 041, 042, 043 | Real artifacts produce replayable normalization manifests and site models across target website patterns. |
| 046 | Schema Extraction Candidate Runtime | Generate schema-bound extraction strategies and candidates while keeping candidates separate from published outputs. | 045 | Candidates carry strategy, schema validation, model/tool trace, source anchor, rejection, and replay refs. |
| 047 | Live Evidence And Verification Runtime | Build evidence packets, evidence anchors, verification decisions, conflict records, and review refs from live candidates. | 046 | Outputs cannot publish without source-backed evidence, verification, policy, replay, and negative conflict coverage. |
| 048 | Result Publication And Export Runtime | Materialize results, Result API, export receipts, output manifests, withdrawal/correction refs, and local production exports. | 047 | Published outputs and exports are replayable, withdrawable, evidence-backed, and blocked when publication gates fail. |
| 049 | Real Agent And Model Adapter Runtime | Connect model providers and agent frameworks through adapters while preserving framework-neutral core state. | 039, 045, 046 | Planning/extraction/repair can use real adapters while core remains framework-neutral. |
| 050 | Multi-Agent Orchestration And Repair Runtime | Add planner/frontier/extractor/verifier/drift/memory/ops agent coordination through controlled tools and commands. | 049, 047 | Multi-agent workflows repair crawl/extraction failures without bypassing policy, evidence, owner, or replay gates. |
| 051 | Graph And Memory Production Runtime | Wire advanced graph projections and memory retrieval/write paths into live crawl decisions without treating them as source evidence. | 045, 047, 050 | Graph/memory improve planning and repair while source-backed evidence remains mandatory for publication. |
| 052 | Worker Orchestration And Scale Runtime | Run production worker pools, queues, leases, retries, dead-letter, sharding, backpressure, and autoscaling. | 040, 041, 045, 047 | Long-running crawls tolerate worker failure, retries, and load without state corruption or silent item loss. |
| 053 | Ops Console, Replay, And Observability Runtime | Expose operator workflows for run review, evidence review, replay, graph/debug views, alerts, cost, and recovery. | 048, 052 | Operators can inspect, pause/resume, replay, recover, and explain outputs through canonical refs. |
| 054 | Production Benchmark And Release Gate | Define and run the final authorized benchmark suite proving target production readiness. | 039-053 | Live benchmark passes with all source, processing, evidence, publication, replay, ops, scale, and safety gates. |

Activation rule: when a planned spec is activated, preserve its number and
directory, run the Spec Kit clarify/plan/tasks/analyze/implement workflow, record
real validation in `tasks.md`, and merge it before moving to the next blocking
spec.

## Phase 0: Contracts And Boundaries

Deliverables:

- product definition
- Python implementation baseline and package boundary rules
- crawl objective contract
- crawl plan contract
- data contracts
- job spec contract
- framework-neutral agent runtime contract
- agent tool contract
- agent action event contract
- typed event taxonomy
- command envelope/result contract
- approval and review decision contracts
- policy decision contract
- source adapter contract
- state machine contract
- graph contract
- normalization manifest contract
- schema snapshot and migration contract
- output manifest and evidence coverage map contract
- output verification aggregate contract
- artifact lifecycle contract
- export contract
- export withdrawal contract
- failure and recovery contract
- evidence packet contract
- verified fact contract
- run diary event contract
- run event contract
- safety and policy boundaries

Exit criteria:

- implementation plans specify Python package boundaries and dependency direction
- every crawl starts from an objective and approved plan
- every major entity has an ID strategy
- agent runtime contracts do not depend on any external agent framework
- every published output has a required evidence path
- every agent action and run event is replayable
- no worker needs undocumented shared state

## Phase 1: Durable Runtime Baseline

Deliverables:

- project/job/run API
- objective-to-plan API
- core objective interpreter
- single-agent crawl planner
- framework-neutral Python agent runtime port
- model provider adapter behind the agent runtime port
- durable queue
- frontier state machine
- idempotency keys
- retry and backoff
- minimum per-project/site concurrency limits
- browser, token, queue, and storage budget gates
- egress allowlist and private-network deny rules
- snapshot object storage
- Postgres metadata model
- typed crawl run event log
- command envelope/result handling
- approval decision recording
- minimal agent tool gateway
- structured logs
- basic metrics

Exit criteria:

- objective, plan, and run lineage can be traced
- the first crawl plan can be generated, approved, and replayed
- the V1 agent loop runs without requiring LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or equivalent frameworks
- interrupted runs can resume
- duplicate fetches do not corrupt state
- failed workers do not lose frontier items
- raw snapshots can be retrieved by ID
- agent tool calls are recorded with input and output refs
- runaway objectives cannot exceed configured crawl, browser, token, queue, or storage budgets
- rejected, duplicate, failed, and committed commands are distinguishable in replay

## Phase 2: Fetch And Normalize Plane

Deliverables:

- source adapter framework
- HTTP adapter
- sitemap adapter
- RSS adapter
- browser snapshot adapter
- AI site understanding pass
- single-agent site understanding workflow
- page type classification
- URL canonicalization
- content hashing
- HTML-to-text normalization
- normalization manifest and anchor maps
- link extraction
- link provenance records
- transformation registry

Exit criteria:

- every snapshot records transformations
- every normalized document points back to a snapshot
- evidence anchors can be replayed through raw-to-normalized maps
- every discovered link has provenance
- adapters declare metadata schemas
- first-pass site models can identify listing, detail, pagination, search, and document pages

## Phase 3: Evidence Spine And Basic Site Graph

Deliverables:

- URL graph
- redirect/canonical graph
- page structure graph
- extraction candidate store
- AI extraction strategy records
- evidence packet builder
- source anchors
- schema validators
- verification decisions
- rejection reasons
- contradiction and conflict records
- published output store
- output manifest and evidence coverage map
- output verification aggregate
- schema validator results
- minimal evidence viewer and replay report

Exit criteria:

- candidates cannot become published outputs without evidence
- factual outputs can be traced to exact source anchors
- rejected candidates are retained for debugging
- conflicts are surfaced instead of silently overwritten
- model-generated candidates remain separated from published outputs
- URL/link/redirect/canonical/page-structure graph is replayable from snapshots
- evidence coverage can be machine-validated for V1 output types
- every required evidence coverage entry has accepted verification support or allowed prior-output support

## Phase 4: Advanced Graph Intelligence

Deliverables:

- entity mention graph
- task graph
- graph clustering
- frontier priority signals
- graph delta reports
- graph signal quality metrics
- temporal KG projection from verified outputs

Exit criteria:

- frontier can prioritize from graph signals
- agents can explain graph-influenced priority changes
- duplicate clusters can be detected
- orphan and hub pages can be reported
- graph signals remain separate from source evidence
- graph build is replayable from snapshots

## Phase 5: Memory Kernel

Deliverables:

- memory event contract
- drawer store
- closet index
- site memory
- task memory
- temporal KG retrieval refs
- agent diaries
- site behavior memory
- extraction repair memory
- scoped retrieval
- cross-site tunnels
- memory freshness scoring

Exit criteria:

- agents can retrieve prior site context without loading all history
- old factual outputs can be invalidated with valid_to through verified output projection
- memories point back to evidence where relevant
- task replay can include memory inputs
- memory-derived extraction strategies must re-anchor to current or selected snapshots

## Phase 6: Advanced Agent Orchestration

Deliverables:

- controlled agent tool surface
- multi-agent planner coordination
- multi-agent site understanding coordination
- Frontier Agent
- Extractor Agent
- Verifier Agent
- Drift Agent
- Memory Agent
- Ops Agent
- agent action trace
- repair loop for failed crawl and extraction paths

Exit criteria:

- every agent action is auditable
- agents cannot directly mutate core stores
- verification remains separate from extraction
- memory writes are evented and replayable
- agents can propose crawl and repair actions without bypassing policy gates

## Phase 7: Console And Operations

Deliverables:

- run dashboard
- frontier dashboard
- evidence viewer
- snapshot viewer
- graph explorer
- quality dashboard
- replay console
- review queue
- export target setup
- export job and delivery receipt viewer
- export withdrawal and correction status
- alerting
- cost dashboard

Exit criteria:

- operators can explain a bad output
- operators can replay a failed run
- operators can see site-level failure patterns
- operators can pause, resume, and review jobs
- operators can verify delivered exports and withdrawal propagation

## Phase 8: Scale And Hardening

Deliverables:

- site-sharded queues
- worker autoscaling
- backpressure
- cost budgets
- storage lifecycle policies
- schema migration strategy
- load testing
- disaster recovery
- security review

Exit criteria:

- high-volume runs do not starve small jobs
- one bad site cannot degrade the full platform
- storage growth is controlled
- production incidents are diagnosable

## Production SLO Targets

Initial targets:

- 99.9% job state durability
- 100% published outputs have source evidence
- 0 silent factual output overwrite on conflict
- 100% replay completeness for mutating, evidence-impacting, verification, and publication actions
- 95% replay completeness for non-critical enriched context
- less than 1% duplicate snapshot pollution per run
- median fetch-to-snapshot write under configured site budget
- extraction quality measured per schema, not globally averaged
- objective-to-plan trace exists for 100% of AI-guided runs

## Major Risks

### Risk: Memory Becomes Source Of Truth

Mitigation:

- memory can suggest, but evidence verifies
- every memory-derived extraction must re-anchor to current or selected historical snapshot

### Risk: Vector Search Hides Exact Identifiers

Mitigation:

- always combine BM25, exact filters, metadata filters, and vector recall

### Risk: Agent Decisions Become Untraceable

Mitigation:

- all tool calls and decisions emit `CrawlRunEvent`
- agent diaries are structured and linked to evidence
- model, prompt, tool, memory, graph, and evidence inputs are recorded by reference

### Risk: AI Autonomy Exceeds Policy

Mitigation:

- agents operate only through approved tools
- mutating tools require policy checks and optional human approval
- crawl plans must obey scope, rate, budget, credential, and safety constraints
- blocked or unavailable sources are reported instead of bypassed

### Risk: Page Drift Corrupts Extraction

Mitigation:

- template drift detection
- selector validity windows
- schema validation
- contradiction queue

### Risk: Browser Rendering Cost Explodes

Mitigation:

- default to HTTP and structured adapters
- browser adapter only when required by job policy
- track browser minutes per published output

## Recommended First Build Target

Build the production spine first:

```text
CrawlObjective
  -> AI crawl plan
  -> JobSpec
  -> durable frontier
  -> fetch snapshot
  -> normalize
  -> page type classification
  -> candidate
  -> evidence packet
  -> verification decision
  -> published output
  -> run diary event
  -> replay report
```

This is not an MVP in the throwaway sense. It is the minimum production spine that proves VeraCrawl can turn a high-level objective into AI-guided, durable, evidence-preserving crawl execution.
