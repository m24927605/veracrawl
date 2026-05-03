# Feature Specification: VeraCrawl Production Runtime Spec Roadmap

**Feature Branch**: `038-production-runtime-closure`
**Created**: 2026-05-03
**Status**: Roadmap Control Spec
**Input**: User direction: "Define all remaining specs first so the AI agent does not keep inventing divergent specs."

## Purpose

This spec fixes the post-037 production runtime roadmap. It does not implement a
runtime feature by itself. It defines the finite set of remaining specs required
to move VeraCrawl from executable deterministic target-architecture foundations
to a production-capable general-purpose AI agent crawler.

Future production implementation specs MUST come from this roadmap. If a missing
production capability is discovered, this spec and `docs/08-build-roadmap.md`
MUST be amended first; a new implementation spec MUST NOT be created ad hoc.

## Constitution Alignment

- **General-purpose crawler impact**: The roadmap preserves broad crawling
  capability across source types, website patterns, schemas, evidence paths,
  graph/memory intelligence, and operations. It does not narrow VeraCrawl into a
  single-site scraper or workflow demo.
- **Target/V1 boundary**: Specs 039-055 are production sequencing specs. They
  connect the already completed target architecture foundation to real source
  acquisition, processing, orchestration, AI adapters, persistence, benchmark,
  and operations paths without reducing target architecture.
- **Evidence and replay impact**: Every planned spec must preserve command,
  event, artifact, source observation, evidence, verification, publication,
  export, replay, and operator-visible refs when it touches those paths.
- **Safety and policy impact**: Live crawling specs must enforce source scope,
  robots/terms policy, private-network denial, credentials, browser cost,
  prompt-taint, privacy lifecycle, retention, and export/withdrawal boundaries.
- **Required reference docs**: `docs/01-product-definition.md`,
  `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`,
  `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`,
  and `docs/11-target-testing-and-acceptance.md`.

## Roadmap Rules

- **RR-001**: Specs 039-055 are the approved remaining production runtime specs.
- **RR-002**: A later implementation spec may be activated only after all prior
  blocking specs listed in the roadmap are complete or explicitly marked
  non-blocking by an amendment to this spec.
- **RR-003**: No spec may reduce target architecture because of schedule,
  staffing, convenience, or implementation speed.
- **RR-004**: Every activated spec must run Spec Kit clarify, plan, tasks,
  analyze where available, implementation, and real verification.
- **RR-005**: Every activated spec must state which roadmap row it implements.
- **RR-006**: No implementation spec may persist framework-native agent/model
  state, browser-native state, adapter-native state, or export-native state as
  VeraCrawl canonical state.
- **RR-007**: Live website execution may use only authorized, policy-allowed
  sources. CAPTCHA solving, paywall bypass, login-wall circumvention, WAF
  evasion, stealth automation, credential theft, and robots/terms bypass remain
  non-goals.

## Approved Remaining Specs

| Spec | Name | Purpose | Blocking Dependencies | Completion Gate |
| --- | --- | --- | --- | --- |
| 039 | Production Run Control API | Make objectives, projects/sites, plans, approvals, runs, budgets, and policy snapshots executable beyond fixtures. | 038 | A real run can be created, approved, blocked, resumed, cancelled, and replayed through canonical commands/events. |
| 040 | Production Persistence Runtime Wiring | Wire target runtime through production Postgres/object/queue ports without coupling core to clients. | 039 | Canonical run state, artifacts, events, outbox, idempotency, and queue leases survive process restart and replay. |
| 041 | Live HTTP Acquisition Runtime | Implement policy-gated live HTTP acquisition with redirects, canonical URLs, headers, content hashes, snapshots, and replay refs. | 039, 040 | Authorized HTTP crawl writes source observations and artifacts from real local/network fixtures without direct-source bypass. |
| 042 | Structured Source Adapters Runtime | Add sitemap, RSS/feed, API-like, document, and file-import source adapters behind source ports. | 041 | Each structured adapter produces adapter result refs, artifacts, policy refs, evidence seeds, and negative fixtures. |
| 043 | Browser Snapshot Runtime | Add policy-gated browser snapshot adapter with rendering budget, sandboxing, network trace, DOM/screenshot artifacts, and replay. | 041, 042 | Browser-required fixtures pass only with browser artifacts and fail on unsafe/cost/prompt-taint cases. |
| 044 | Credentialed Session Runtime | Add authorized session and credential-use runtime without leaking secrets or bypassing scope. | 039, 041, 043 | Credentialed fixtures prove vault boundary, credential audit, redacted replay, and denial for out-of-scope access. |
| 045 | Live Normalization And Site Understanding | Convert acquired artifacts into normalized documents, anchor maps, page classifications, site models, and link provenance. | 041, 042, 043 | Real artifacts produce replayable normalization manifests and site models across target website patterns. |
| 046 | Schema Extraction Candidate Runtime | Generate schema-bound extraction strategies and candidates while keeping candidates separate from published outputs. | 045 | Candidates carry strategy, schema validation, model/tool trace, source anchors, rejection, and replay refs. |
| 047 | Live Evidence And Verification Runtime | Build evidence packets, evidence anchors, verification decisions, conflict records, and review refs from live candidates. | 046 | Outputs cannot publish without source-backed evidence, verification, policy, replay, and negative conflict coverage. |
| 048 | Result Publication And Export Runtime | Materialize results, Result API, export receipts, output manifests, withdrawal/correction refs, and local production exports. | 047 | Published outputs and exports are replayable, withdrawable, evidence-backed, and blocked when publication gates fail. |
| 049 | Real Agent And Model Adapter Runtime | Connect OpenAI/model providers and agent frameworks through adapters while preserving framework-neutral core state. | 039, 045, 046 | Planning/extraction/repair can use real adapters, but core imports and canonical state remain framework-neutral. |
| 050 | Multi-Agent Orchestration And Repair Runtime | Add planner/frontier/extractor/verifier/drift/memory/ops agent coordination through controlled tools and commands. | 049, 047 | Multi-agent workflows repair crawl/extraction failures without bypassing policy, evidence, owner, or replay gates. |
| 051 | Graph And Memory Production Runtime | Wire advanced graph projections and memory retrieval/write paths into live crawl decisions without treating them as source evidence. | 045, 047, 050 | Graph/memory improve planning and repair while source-backed evidence remains mandatory for publication. |
| 052 | Worker Orchestration And Scale Runtime | Run production worker pools, queues, leases, retries, dead-letter, sharding, backpressure, and autoscaling. | 040, 041, 045, 047 | Long-running crawls tolerate worker failure, retries, and load without state corruption or silent item loss. |
| 053 | Ops Console, Replay, And Observability Runtime | Expose operator workflows for run review, evidence review, replay, graph/debug views, alerts, cost, and recovery. | 048, 052 | Operators can inspect, pause/resume, replay, recover, and explain outputs through canonical refs. |
| 054 | Production Benchmark And Release Gate | Define and run the final authorized benchmark suite proving target production readiness. | 039-053 | Live benchmark passes with all source, processing, evidence, publication, replay, ops, scale, and safety gates. |
| 055 | Real-World Benchmark Corpus Gate | Add authorized public website corpus validation that supplements deterministic release gates with real external acquisition, policy, observation, artifact, and replay proof. | 054 | A declared public corpus runs through live HTTP acquisition with origin/robots/private-network safety, observation oracles, artifact/content hash refs, command/event/outbox refs, and replay refs. |

## Activation Policy

When a roadmap spec is activated:

1. Keep its reserved spec number and directory.
2. Replace the planned `spec.md` with the full Spec Kit specify output if needed,
   while preserving the roadmap ID, dependencies, and completion gate.
3. Run clarify unless every ambiguity is already resolved in that spec.
4. Create plan, research, data model, contracts, quickstart, and tasks.
5. Implement only that activated spec's bounded scope.
6. Record real validation in its `tasks.md`.
7. Merge before moving to the next blocking spec.

## Non-Goals

- This spec does not implement runtime code.
- This spec does not claim production readiness.
- This spec does not authorize creating additional production implementation
  specs outside 039-055 without first amending this roadmap.

## Success Criteria

- **SC-001**: Specs 039-055 exist as planned spec files with fixed purpose,
  dependency, and completion gate.
- **SC-002**: `docs/08-build-roadmap.md` contains the same post-037 roadmap.
- **SC-003**: `AGENTS.md` points future production work to this roadmap before
  opening or activating additional specs.
- **SC-004**: The repository has no unbounded instruction to invent additional
  production specs after 037.
