# Feature Specification: VeraCrawl Production Runtime Spec Roadmap

**Feature Branch**: `038-production-runtime-closure`
**Created**: 2026-05-03
**Status**: Roadmap Control Spec
**Input**: User direction: "Define all remaining specs first so the AI agent does not keep inventing divergent specs."

## Purpose

This spec fixes the post-037 production runtime roadmap. It does not implement a
runtime feature by itself. It defines the finite set of remaining specs required
to move VeraCrawl from executable deterministic target-architecture foundations
to a production-capable general-purpose AI agent crawler. Specs 068-096 extend
this control spec with the production-grade closure roadmap, ecommerce market
follow-ups, and post-079 crawler intelligence optimization roadmap discovered
after the first real ecommerce product benchmarks.

Future production implementation specs MUST come from this roadmap. If a missing
production capability is discovered, this spec and `docs/08-build-roadmap.md`
MUST be amended first; a new implementation spec MUST NOT be created ad hoc.

## Constitution Alignment

- **General-purpose crawler impact**: The roadmap preserves broad crawling
  capability across source types, website patterns, schemas, evidence paths,
  graph/memory intelligence, and operations. It does not narrow VeraCrawl into a
  single-site scraper or workflow demo.
- **Target/V1 boundary**: Specs 039-096 are production sequencing,
  production-grade closure, market follow-up, and optimization specs. They
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

- **RR-001**: Specs 039-096 are the approved production runtime,
  production-grade closure, market follow-up, and optimization specs.
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
| 056 | Real-World AI Agent Crawl Planning And Extraction Benchmark | Prove the public corpus crawl actually invokes framework-neutral AI planning, site understanding, extraction candidate generation, and verification/repair decisions without making model output evidence or coupling core to agent frameworks. | 055, 049, 047 | A declared public corpus runs through live HTTP acquisition and framework-neutral model/agent ports with model call, agent action, tool call, context bundle, source anchor, candidate, evidence/verification gate, command/event/outbox, and replay refs; LLM-as-evidence, publication bypass, framework-native state, missing traces, and replay gaps fail. |
| 057 | Production Crawl Quality Benchmark Roadmap | Fix the finite post-056 quality benchmark spec set so production-grade crawl quality is not asserted from the small AI smoke corpus alone. | 056 | Specs 058-064 are defined with purpose, dependency, measurable thresholds, non-goals, and completion gates; no additional production quality spec may be invented without amending this spec and `docs/08-build-roadmap.md`. |
| 058 | Expanded Real-World Public Corpus Benchmark | Expand real public validation from a four-target smoke corpus into a diverse quality-tier public corpus. | 055, 056, 057 | Implemented by `veracrawl-real-quality-corpus`: an authorized quality-tier corpus composes row 055 acquisition with quality thresholds, pattern coverage, drift/policy/network accounting, artifact/hash/canonical refs, command/event/outbox refs, and replay refs. |
| 059 | JavaScript Browser Crawl Quality Benchmark | Prove browser rendering improves crawl evidence when HTTP-only acquisition is insufficient. | 043, 055, 056, 058 | Implemented by `veracrawl-browser-quality-benchmark`: JS-required targets run HTTP-only comparison before adapter-owned browser rendering and produce browser-only recovered oracle fragments, DOM/screenshot/network/console/timing artifacts, rendered content hashes, source anchors, policy/budget/prompt-taint refs, command/event/outbox refs, and replay refs. |
| 060 | Multi-Page Deep Crawl Frontier Benchmark | Prove bounded multi-page crawling with frontier planning, pagination, detail coverage, canonicalization, duplicate suppression, and replayable stop reasons. | 045, 050, 051, 052, 058, 059 | Depth-limited public/fixture crawls produce frontier decisions, graph refs, page coverage oracles, duplicate/canonical controls, rate budgets, and replayable stop reasons. |
| 061 | Field-Level Oracle Extraction Benchmark | Evaluate extraction quality at field level with schema-specific expected values, anchors, normalization rules, and verification gates. | 046, 047, 048, 058, 060 | At least 8 schemas and 200 expected fields are evaluated; every accepted field has source anchors, content hashes, evidence packet refs, normalized value refs, and typed mismatch diagnostics. |
| 062 | Precision Recall Quality Benchmark | Compute precision, recall, F1, false-positive, false-negative, unsupported-field, and abstention metrics from field-level oracle reports. | 061 | Corpus-level and per-pattern precision/recall/F1, confidence calibration, no direct LLM evidence, and release-blocking thresholds are reported. |
| 063 | Repair Success Rate Benchmark | Measure crawl, extraction, verification, drift, and replay repair success under seeded failures without owner-service bypass or policy weakening. | 050, 061, 062 | Seeded repair cases report repair success rate, attempts, model/tool traces, before/after evidence, rollback refs, unresolved escalation, and no unsafe repair bypass. |
| 064 | Cost Latency Stability Release Gate | Aggregate quality, cost, latency, throughput, token/call usage, retry behavior, and multi-run stability into the production crawl quality release decision. | 058-063 | Quality release passes only when all prior quality benchmark reports exist, SLO/cost budgets are met, three-run stability is acceptable, replay is complete, and no false-ready status is emitted. |
| 065 | Top Ecommerce Live AI Benchmark | Run a targeted market validation corpus against selected Taiwan and United States major ecommerce public entry points with hosted LLM/agent traces. | 055, 056, 064 | Public ecommerce homepage entry points pass or fail visibly with live HTTP, source anchors, AI traces, evidence/verification refs, command/event/outbox refs, and replay refs. |
| 066 | US Top Ecommerce Product Price Availability Benchmark | Test whether a specified product's price and availability can be extracted from Amazon, Walmart, and eBay with source evidence and AI traces. | 055, 056, 065 | Product-page extraction passes where source evidence exists and records blocked sources without fabricated inventory. |
| 067 | Taiwan Top Ecommerce Product Price Availability Benchmark | Test whether the same specified product's price and availability can be extracted from Shopee Taiwan, momo, and PChome 24h with source evidence and AI traces. | 055, 056, 065, 066 | momo and PChome 24h pass with source-backed evidence; Shopee Taiwan source limitations are recorded as needs-review without bypass. |
| 068 | Production Grade Crawler Closure Roadmap | Fix the finite post-067 closure spec set required before VeraCrawl may claim full production-grade web crawler capability. | 067 | Specs 069-075 are defined with purpose, dependency, non-goals, and completion gates. |
| 069 | Objective Discovery And Crawl Planning Runtime | Turn high-level objectives into approved discovery plans, candidate sites, entry points, query strategies, crawl bounds, and evidence requirements. | 049, 050, 055, 056, 067, 068 | A high-level objective produces an approved, replayable discovery plan without declared product URLs. |
| 070 | Unified HTTP Browser Acquisition Escalation Runtime | Escalate from HTTP/structured acquisition to browser rendering when evidence is missing, while preserving sandbox, budget, DOM/network artifacts, and no-bypass policy. | 043, 041, 045, 059, 067, 069 | Browser rendering recovers source-backed DOM evidence when policy allows and records source-limited cases when it does not. |
| 071 | Authorized Source Access And Official API Runtime | Support official APIs and authorized credentialed sessions as first-class source adapters without leaking secrets or bypassing site controls. | 044, 049, 070 | Authorized APIs/sessions provide source-backed evidence with redaction, audit, replay, and policy refs. |
| 072 | Adaptive Frontier Deep Crawl Production Runtime | Execute bounded multi-page crawls with AI-assisted frontier prioritization, pagination/detail traversal, canonicalization, dedupe, rate limits, and replayable stop reasons. | 050, 051, 052, 060, 070 | Approved objectives execute as bounded, replayable multi-page crawls with coverage and extraction results. |
| 073 | Production Extraction Quality And Oracle Runtime | Convert field-level oracle, precision/recall, confidence calibration, abstention, and publication gating into release-blocking production quality checks. | 061, 062, 072 | Publication and release are blocked when source-backed quality gates fail. |
| 074 | Production Reliability Operations And Cost Runtime | Prove long-running worker, queue, persistence, object store, retry, recovery, observability, cost, latency, and SLO behavior under production-like runs. | 052, 053, 064, 072, 073 | Production-like workloads pass reliability, cost, latency, recovery, observability, and replay gates. |
| 075 | Production Grade Web Crawler Release Gate | Aggregate 069-074 into one release gate that decides whether VeraCrawl may claim production-grade crawler capability. | 069-074 | Production-grade status passes only when discovery, browser/API acquisition, deep crawl, extraction quality, operations, and safety gates all pass. |
| 076 | Amazon Official Product API Adapter | Add a credential-gated Amazon official product API path for source-backed product identity, price, and availability when public/browser product pages are source-limited. | 066, 071 | Official Amazon API evidence can satisfy product fields when credentials and source anchors are available; missing credentials remain needs-review. |
| 077 | eBay Browse API Adapter | Add an official eBay Browse API path for source-backed product search, price, and availability when public item pages are access denied. | 066, 071, 076 | Official eBay API evidence can satisfy product fields when credentials and source anchors are available; missing credentials remain needs-review. |
| 078 | Delivery ETA Offer Sorting Projection | Extend product crawl output so downstream comparison sites can sort source-backed offers by price, total price, delivery ETA, and availability without fabricating missing fields. | 066, 067, 076, 077 | Source-backed offer projection materializes sortable refs for price, total price, delivery, and availability while missing fields remain absent. |
| 079 | Query Product Discovery And Offer Ranking | Start from a natural-language product query and allowed ecommerce search/listing entry pages, discover product candidate URLs from source-backed artifacts, then compose product availability extraction and offer ranking without manually supplied product URLs. | 066, 067, 078 | Query-driven product discovery emits source-backed candidates and ranked offers without manually supplied product URLs. |
| 080 | Crawler Intelligence Optimization Roadmap | Fix the finite post-079 optimization spec set for frontier scoring, DOM understanding, extraction fallback/confidence, dedupe/identity, ranking, cost/recovery/evaluation gates, runtime wiring, and owner-service integration. | 075, 079 | Specs 081-096 are defined as post-closure optimization follow-ups without changing the 069-075 production-grade closure gate. |
| 081 | Focused Frontier Scoring Runtime | Replace raw priority integers with replayable score breakdowns and best-first frontier decisions. | 072, 028, 051, 060, 080 | Score-backed frontier scheduling improves required-page coverage per unit cost with replayable priority, retire, retry, expand, and stop decisions. |
| 082 | DOM Page Understanding And Element Ranking Runtime | Materialize pruned DOM, page zones, repeated blocks, element rankings, and LLM-ready context bundles. | 045, 070, 081 | DOM intelligence reduces model context size, preserves anchors, improves page/element classification, and blocks unsafe browser interactions. |
| 083 | Extractor Fallback And Confidence Runtime | Add deterministic-first extractor fallback, field validators, confidence calibration, abstention, and drift signals. | 046, 047, 073, 082 | Source-backed field extraction passes oracle thresholds and abstains or routes to review when evidence is weak or contradictory. |
| 084 | Canonical Dedupe And Identity Runtime | Add URL canonicalization, parameter normalization, exact/near duplicate clusters, identity resolution, and variant preservation. | 072, 073, 081, 083 | Duplicate pollution decreases while true variants remain source-backed and replayably distinct. |
| 085 | Recommendation Ranking Runtime | Add generic explainable ranking records for outputs/offers/documents/facts using heuristic profiles first and learning-to-rank only after labels are ready. | 078, 079, 083, 084 | Ranked outputs are deterministic, evidence-backed, and free of fabricated missing fields. |
| 086 | Cost Recovery Evaluation Gates | Aggregate optimization quality, duplicate, cost, latency, cache, retry, repair, drift, ranking, and replay metrics across specs 081-085. | 074, 081-085 | Optimization release is blocked unless lower reports and metrics prove net quality, cost, recovery, and replay improvements. |
| 087 | Crawler Optimization Runtime Wiring | Wire spec 080-086 optimization contracts into runtime-safe frontier, DOM/extraction, dedupe/ranking, and ops services without adapter, benchmark, or framework coupling. | 080-086 | Owner services can consume optimization decisions through typed runtime contracts, registry entries, replay helpers, and deterministic tests. |
| 088 | Optimization Runtime Activation Roadmap | Fix the finite post-087 owner-service integration spec set for scheduler, DOM, extraction, dedupe, ranking, cost/cache, drift/recovery, and regression release gates. | 080-087 | Specs 089-096 are defined and implemented through typed owner-service integration contracts. |
| 089 | Priority Frontier Scheduler Integration | Wire optimization frontier decisions into scheduler-owned enqueue, block, retire, and stop outcomes. | 081, 087, 088 | Scheduler emits replayable score-backed frontier adoption refs. |
| 090 | DOM Intelligence Normalize Integration | Wire DOM context, page zones, retained nodes, and interactive rankings into normalize/browser integration refs. | 082, 087, 088 | Normalize integration preserves anchors, artifacts, prompt-taint refs, and context reduction metrics. |
| 091 | Extraction Fallback Verification Integration | Wire fallback attempts, confidence, abstention, and LLM-only rejection into extract/verify boundaries. | 083, 090 | Extract/verify integration accepts source-backed fields and rejects unsupported evidence. |
| 092 | Canonical Dedupe Identity Integration | Wire canonicalization, fingerprints, identity decisions, duplicate suppression, and variants into graph/scheduler/normalize boundaries. | 084, 089, 091 | Dedupe integration suppresses duplicates while preserving variants. |
| 093 | Recommendation Ranking Publication Integration | Wire ranked outputs and score breakdowns into publish/projection boundaries. | 085, 091, 092 | Ranking integration preserves evidence and verification status. |
| 094 | Optimization Cost Cache Budget Runtime | Wire cost, cache freshness, fetch/browser/token budget, and metrics into ops refs. | 086, 089-093 | Cost/cache integration fails stale cache, budget overrun, missing metrics, and replay gaps. |
| 095 | Drift Recovery Feedback Runtime | Wire drift, retry, repair, and memory advisory refs into recovery feedback. | 083, 086, 091, 094 | Feedback is advisory, replayable, and blocked on unsafe recovery. |
| 096 | Optimization Regression Release Gate | Aggregate 089-095 integration evidence into a release-blocking gate. | 089-095 | Gate passes only with complete lower integration refs, metrics, replay, and no regressions. |

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
  specs outside 039-096 without first amending this roadmap.

## Success Criteria

- **SC-001**: Specs 039-096 exist as planned spec files with fixed purpose,
  dependency, and completion gate.
- **SC-002**: `docs/08-build-roadmap.md` contains the same post-037 roadmap.
- **SC-003**: `AGENTS.md` points future production work to this roadmap before
  opening or activating additional specs.
- **SC-004**: The repository has no unbounded instruction to invent additional
  production specs after 037.
