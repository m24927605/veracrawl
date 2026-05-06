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
| 038 | Production Runtime Spec Roadmap | Control the remaining production spec set and prevent ad hoc spec expansion. | 037 | Specs 039-075 are defined with purpose, dependency, and completion gate. |
| 039 | Production Run Control API | Make objectives, projects/sites, plans, approvals, run lifecycle, budgets, and policy snapshots executable beyond fixtures. | 038 | Implemented by `veracrawl-run-control`: a run can be created, approved, blocked, resumed, cancelled, and replayed through canonical commands/events. |
| 040 | Production Persistence Runtime Wiring | Wire target runtime through production Postgres/object/queue ports without coupling core to clients. | 039 | Implemented by `veracrawl-production-persistence`: row 039 canonical state, artifacts, events, outbox, idempotency, and queue leases survive adapter reopen and replay through port-shaped persistence wiring. |
| 041 | Live HTTP Acquisition Runtime | Implement policy-gated live HTTP acquisition with redirects, canonical URLs, headers, content hashes, snapshots, and replay refs. | 039, 040 | Implemented by `veracrawl-live-http`: authorized local HTTP acquisition composes row 039/040 refs, adapter-owned HTTP, network/source acquisition refs, target source observations, artifacts, canonical URL refs, and typed unsafe/fake-acquisition failures without direct-source bypass. |
| 042 | Structured Source Adapters Runtime | Add sitemap, RSS/feed, API-like, document, and file-import source adapters behind source ports. | 041 | Implemented by `veracrawl-structured-source`: sitemap/RSS/API/document/file-import adapters produce source adapter result refs, parsed natural output refs, artifacts, evidence seed refs, policy refs, command/event/outbox refs, and replay refs, with malformed/policy/unsupported/replay negative fixtures. |
| 043 | Browser Snapshot Runtime | Add policy-gated browser snapshot adapter with rendering budget, sandboxing, network trace, DOM/screenshot artifacts, and replay. | 041, 042 | Implemented by `veracrawl-browser-snapshot`: browser-required fixtures preserve live HTTP and structured source prerequisite refs, sandbox policy refs, browser step refs, DOM/screenshot/network trace/console/timing artifacts, budget refs, prompt-taint boundary refs, command/event/outbox refs, and replay refs; egress denial, unsafe interaction, budget exhaustion, prompt-tainted content, missing artifact, and replay mismatch fail with typed diagnostics. |
| 044 | Credentialed Session Runtime | Add authorized session and credential-use runtime without leaking secrets or bypassing scope. | 039, 041, 043 | Implemented by `veracrawl-credentialed-session`: credentialed fixtures preserve live HTTP and browser snapshot prerequisite refs, credential scope/origin/approval refs, credential use audit refs, session adapter result refs, redacted artifacts, redaction map refs, redacted replay refs, command/event/outbox refs, and replay refs; missing authorization, out-of-scope use, raw secret leakage, unsafe credential use, missing audit, missing redacted replay, and replay mismatch fail with typed diagnostics. |
| 045 | Live Normalization And Site Understanding | Convert acquired artifacts into normalized documents, anchor maps, page classifications, site models, and honest link provenance/no-link analysis. | 041, 042, 043 | Implemented by `veracrawl-live-normalization`: listing, detail, and browser-shaped local live artifacts produce normalized documents, normalization manifests, source anchors, link provenance or deterministic no-link analysis, page type refs, site model refs, derived-context refs, command/event/outbox refs, and replay refs; missing upstream, empty content, missing anchor map, missing site model, and replay mismatch fail with typed diagnostics. |
| 046 | Schema Extraction Candidate Runtime | Generate schema-bound extraction strategies and candidates while keeping candidates separate from published outputs. | 045 | Implemented by `veracrawl-schema-extraction`: declared schemas, approved exploratory schemas, and browser-shaped normalized content produce strategy refs, candidate refs, candidate field anchors, schema validation refs, framework-neutral model/tool trace refs, confidence refs, command/event/outbox refs, and replay refs; missing normalization, schema validation failure, missing field anchors, missing model/tool traces, direct candidate publication, drift repair, and replay mismatch produce typed failure or needs-review reports with no published output. |
| 047 | Live Evidence And Verification Runtime | Build evidence packets, evidence anchors, verification decisions, conflict records, and review refs from live candidates. | 046 | Implemented by `veracrawl-live-evidence`: schema extraction candidates produce evidence coverage refs, evidence packet refs, evidence anchor refs, evidence manifest refs, verification refs, review refs, freshness refs, policy/privacy refs, command/event/outbox refs, and replay refs before pass; missing schema extraction, missing source anchors, stale evidence, contradictory evidence, graph-only evidence, memory-only evidence, verification conflict, publication bypass, and replay mismatch produce typed failure or needs-review reports with no published output. |
| 048 | Result Publication And Export Runtime | Materialize results, Result API, export receipts, output manifests, withdrawal/correction refs, and local production exports. | 047 | Implemented by `veracrawl-result-publication`: row 047 live evidence produces publication reports, published outputs, output manifests, Result API snapshots, export target/job/attempt refs, delivery receipts, withdrawal/correction refs, destination mappings, policy/privacy refs, command/event/outbox refs, and replay refs; missing live evidence, publication policy denial, verification not accepted, missing output manifests, missing export receipts, missing withdrawal propagation, correction without withdrawal, missing privacy, direct export bypass, and replay mismatch produce typed non-pass reports. |
| 049 | Real Agent And Model Adapter Runtime | Connect model providers and agent frameworks through adapters while preserving framework-neutral core state. | 039, 045, 046 | Implemented by `veracrawl-agent-model-runtime`: row 039/045/046 refs plus local model/native agent runtime adapters execute planner, extractor, and repair turns through ports with canonical request/response/trace, adapter runtime, policy/security, command/event/outbox, and replay refs; external SDK/runtime absence returns `needs_review`, while unsupported adapters, raw prompt/response/credential leakage, provider/framework-native canonical state, missing traces, core import boundary violations, and replay gaps fail with typed diagnostics. |
| 050 | Multi-Agent Orchestration And Repair Runtime | Add planner/frontier/extractor/verifier/drift/memory/ops agent coordination through controlled tools and commands. | 049, 047 | Implemented by `veracrawl-agent-workflow`: row 049 agent/model runtime refs and row 047 live evidence refs gate planner/frontier/fetch-analysis/extractor/verifier/drift/memory/ops workflows; crawl, extraction, and drift repairs require handoffs, coordination decisions, controlled tool refs, owner-service command refs, before/after evidence, rollback, review escalation, policy, command/event/outbox, and replay refs, while missing dependencies, owner bypass, agent reasoning as evidence, unresolved conflicts, missing tool/owner gates, and replay gaps fail with typed diagnostics. |
| 051 | Graph And Memory Production Runtime | Wire advanced graph projections and memory retrieval/write paths into live crawl decisions without treating them as source evidence. | 045, 047, 050 | Implemented by `veracrawl-graph-memory-runtime`: row 045 live normalization, row 047 live evidence, row 050 multi-agent repair, advanced graph, graph frontier/review, temporal KG, and memory kernel refs gate graph/memory-influenced frontier and repair decisions; URL, redirect, canonical, page-structure, entity, task, temporal graph refs plus site/task/repair/run-diary memory refs, freshness, invalidation, explanations, policy, command/event/outbox, and replay refs are required before pass, while missing dependencies, graph-as-evidence, memory-as-evidence, stale memory, missing invalidation, missing explanations, and replay mismatch fail with typed diagnostics. |
| 052 | Worker Orchestration And Scale Runtime | Run production worker pools, queues, leases, retries, dead-letter, sharding, backpressure, and autoscaling. | 040, 041, 045, 047 | Implemented by `veracrawl-worker-orchestration`: production persistence, queue broker conformance, live HTTP, live normalization, live evidence, and scale recovery refs gate the worker runtime; frontier/fetch/browser/processing/verification/review/export/projection/recovery pools require heartbeat, capacity, queue item, shard lease, lease heartbeat, fencing, visibility timeout, fairness, retry, dead-letter, failure, recovery, duplicate suppression, backpressure, autoscaling, pending outbox, event gap, policy, command/event/outbox, and replay refs before pass, while missing persistence, missing queue broker, stale lease unrecovered, missing heartbeat, hidden dead letter, duplicate pollution, backpressure without policy, and replay mismatch fail with typed diagnostics. |
| 053 | Ops Console, Replay, And Observability Runtime | Expose operator workflows for run review, evidence review, replay, graph/debug views, alerts, cost, and recovery. | 048, 052 | Implemented by `veracrawl-ops-runtime`: result publication/export, worker orchestration, ops console, and observability reports compose into one operator-visible replay aggregate; run-control, review/evidence review, replay audit, graph/debug, export/withdrawal, failure/recovery, DR, quality, dashboard, alert, runbook, cost, signal, metric, trace, policy, command/event/outbox, redaction, and replay refs gate pass, while missing publication, missing worker orchestration, missing ops console, missing observability, stale dashboard, unresolved recovery, unsafe operator action, and replay mismatch fail with typed diagnostics. |
| 054 | Production Benchmark And Release Gate | Define and run the final authorized benchmark suite proving target production readiness. | 039-053 | Implemented by `veracrawl-release-gate`: target runtime, source coverage, product acceptance, security/privacy, result publication/export, worker orchestration, and ops runtime refs compose into one release report; source, processing, evidence, verification, publication, export, replay, ops, scale, safety, policy, command/event/outbox, artifact, redaction, SLO, release decision, and audit refs gate pass, while missing lower runtime gates, SLO violations, release blockers, false-ready status, and replay mismatch fail with typed diagnostics. |
| 055 | Real-World Benchmark Corpus Gate | Supplement deterministic release gates with authorized public website corpus validation. | 054 | Implemented by `veracrawl-real-benchmark`: a manifest-declared public corpus runs through live HTTP acquisition with origin allowlists, robots preflight, private-network denial, coarse observation oracles, artifact/content hash refs, source observation refs, command/event/outbox refs, and replay refs; robots denial, scope denial, observation mismatch, missing evidence refs, replay mismatch, and network unavailability fail with typed diagnostics. |
| 056 | Real-World AI Agent Crawl Planning And Extraction Benchmark | Prove the public corpus crawl actually invokes framework-neutral AI planning, site understanding, extraction candidate generation, and verification/repair decisions. | 055, 049, 047 | Implemented by `veracrawl-real-ai-benchmark`: a manifest-declared public corpus runs through row 055 live acquisition and VeraCrawl model/agent ports with model call traces, agent action traces, tool call traces, context bundle traces, source anchors, extraction candidates, evidence/verification/publication gate refs, command/event/outbox refs, and replay refs; missing AI traces, LLM output as evidence, missing candidate anchors, publication bypass, framework-native canonical state, core import coupling, and replay gaps fail with typed diagnostics. |
| 057 | Production Crawl Quality Benchmark Roadmap | Fix the finite post-056 quality benchmark spec set so production-grade crawl quality is not asserted from the small AI smoke corpus alone. | 056 | Specs 058-064 are defined with purpose, dependency, measurable thresholds, non-goals, and completion gates; no additional production quality spec may be invented without amending this row and `specs/057-production-quality-benchmark-roadmap/spec.md`. |
| 058 | Expanded Real-World Public Corpus Benchmark | Expand real public validation from a four-target smoke corpus into a diverse quality-tier public corpus. | 055, 056, 057 | Implemented by `veracrawl-real-quality-corpus`: a manifest-declared quality-tier corpus composes row 055 live acquisition with quality contracts, pattern coverage, threshold gates, policy/drift/network accounting, artifact/hash/canonical refs, command/event/outbox refs, and replay refs; insufficient target/origin/pattern coverage, target drift, missing replay, and missing evidence refs fail with typed diagnostics. |
| 059 | JavaScript Browser Crawl Quality Benchmark | Prove browser rendering improves crawl evidence when HTTP-only acquisition is insufficient. | 043, 055, 056, 058 | Implemented by `veracrawl-browser-quality-benchmark`: manifest-declared JS-required targets run HTTP-only observation before browser rendering and pass only with browser-only recovered oracle fragments, DOM/screenshot/network/console/timing artifacts, rendered content hashes, source anchors, sandbox/policy/budget/prompt-taint refs, command/event/outbox refs, and replay refs; unsafe action, prompt-taint bypass, missing artifacts/anchors, budget exhaustion, replay mismatch, adapter unavailability, and insufficient browser-required target coverage fail with typed diagnostics. |
| 060 | Multi-Page Deep Crawl Frontier Benchmark | Prove bounded multi-page crawling with frontier planning, pagination, detail coverage, canonicalization, duplicate suppression, and replayable stop reasons. | 045, 050, 051, 052, 058, 059 | Implemented by `veracrawl-deep-crawl-benchmark`: manifest-declared bounded fixture/public-style sites pass only when at least 5 sites and 50 required pages are covered with frontier decisions, page observations, stop reasons, source anchors, artifact/hash refs, link provenance, canonical refs, duplicate suppression, graph refs, AI/model/agent/tool/context refs where frontier priority is AI-influenced, policy refs, command/event/outbox refs, and replay refs; duplicate-loop, off-origin pollution, robots bypass, budget exhaustion, infinite pagination, replay mismatch, missing frontier, missing graph, missing replay, and insufficient coverage fail with typed diagnostics. |
| 061 | Field-Level Oracle Extraction Benchmark | Evaluate extraction quality at field level with schema-specific expected values, anchors, normalization rules, and verification gates. | 046, 047, 048, 058, 060 | Implemented by `veracrawl-field-oracle-benchmark`: schema-driven generated/explicit oracles evaluate at least 8 schemas and 200 expected fields, with every accepted field carrying source anchors, artifacts, content hashes, normalized value refs, evidence packet refs, verification decision refs, policy refs, command/event/outbox refs, and replay refs; wrong value, missing anchor, schema violation, stale evidence, publication bypass, LLM-as-evidence, missing evidence/verification/replay, and insufficient schema/field coverage fail with typed diagnostics. |
| 062 | Precision Recall Quality Benchmark | Compute precision, recall, F1, false-positive, false-negative, unsupported-field, and abstention metrics from field-level oracle reports. | 061 | Implemented by `veracrawl-quality-metrics`: field confusion records produce corpus and slice precision/recall/F1, false-positive, false-negative, abstention, unsupported, and needs-review rates with fixed thresholds of precision >= 0.98, recall >= 0.90, F1 >= 0.94, and critical-field precision >= 0.99; hidden false positives, LLM-as-true-positive, publication bypass, missing evidence, missing replay, and low-threshold cases fail with typed diagnostics. |
| 063 | Repair Success Rate Benchmark | Measure crawl, extraction, verification, drift, and replay repair success under seeded failures without owner-service bypass or policy weakening. | 050, 061, 062 | Implemented by `veracrawl-repair-quality-benchmark`: seeded crawl planning, fetch/browser, normalization, extraction, verification, publication, drift, and replay repair cases pass only with repair success rate >= 0.80 for repairable cases, unsafe bypass rate = 0, unresolved critical repair rate = 0, framework-neutral model/agent/tool/context traces, owner-service command refs, before/after evidence, rollback/escalation refs, policy refs, command/event/outbox refs, and replay refs; low success rate, unsafe bypass, owner-service bypass, model-only evidence, missing trace, missing rollback, unresolved critical repair, and missing replay fail with typed diagnostics. |
| 064 | Cost Latency Stability Release Gate | Aggregate quality, cost, latency, throughput, token/call usage, retry behavior, and multi-run stability into the production crawl quality release decision. | 058-063 | Implemented by `veracrawl-quality-release-gate`: quality report refs from 058-063, at least three stability runs, cost budget, p95 latency, throughput, retry rate, token/call usage, stability variance, policy refs, command/event/outbox refs, SLO metric refs, audit refs, release decision refs, and replay refs gate the final quality release decision; missing prior gates, cost budget violations, latency SLO violations, retry violations, stability regressions, insufficient runs, replay gaps, false-ready status, and missing command/event refs fail with typed diagnostics. |
| 065 | Top Ecommerce Live AI Benchmark | Run a targeted market validation corpus against selected Taiwan and United States major ecommerce public entry points with hosted LLM/agent traces. | 055, 056, 064 | Implemented by `veracrawl-real-benchmark` and `veracrawl-real-ai-benchmark`: `top-ecommerce-public-corpus` and `top-ecommerce-ai-agent-corpus` cover Shopee Taiwan, momo Shopping, PChome 24h, Amazon US, Walmart US, and eBay US homepages with robots preflight, origin allowlists, live HTTP evidence, OpenAI model traces through `ModelProviderPort`, native agent traces through `AgentRuntimePort`, source anchors, extraction candidates, evidence/verification gate refs, command/event/outbox refs, and replay refs; robots denial, source drift, hosted-model failure, missing traces, LLM-as-evidence, or replay gaps fail visibly. |
| 066 | US Top Ecommerce Product Price Availability Benchmark | Test whether a specified product's price and availability can be extracted from Amazon, Walmart, and eBay with source evidence and AI traces. | 055, 056, 065 | Implemented by `veracrawl-product-availability-benchmark`: a manifest-declared product-page corpus for SanDisk 256GB Extreme microSDXC runs robots-gated live HTTP plus optional read-only browser DOM source evidence and framework-neutral model/agent decisions for product identity, price candidate, availability candidate, and verification; passing fields require source anchors, artifacts, content hashes, evidence/verification refs, command/event/outbox refs, and replay refs, while source access denial, missing price, missing availability, LLM-as-evidence, missing traces, missing browser DOM evidence, and missing replay fail or produce honest needs-review without fabricated inventory. |
| 067 | Taiwan Top Ecommerce Product Price Availability Benchmark | Test whether the same specified product's price and availability can be extracted from Shopee Taiwan, momo, and PChome 24h with source evidence and AI traces. | 055, 056, 065, 066 | Implemented by `veracrawl-product-availability-benchmark`: the Taiwan product-page corpus reuses the row 066 runtime and adds generic product meta price/availability and Chinese availability signal support; momo and PChome 24h fields must pass only when source-backed, while Shopee Taiwan JavaScript shell or API access limits are recorded as needs-review/source-limited without bypass or fabricated price/inventory. |
| 068 | Production Grade Crawler Closure Roadmap | Fix the finite post-067 closure spec set required before VeraCrawl may claim full production-grade web crawler capability. | 067 | Specs 069-075 are defined with purpose, dependency, non-goals, and completion gates; no additional production-grade closure spec may be invented without amending this row and `specs/068-production-grade-crawler-closure-roadmap/spec.md`. |
| 069 | Objective Discovery And Crawl Planning Runtime | Turn high-level objectives into approved discovery plans, candidate sites, entry points, query strategies, crawl bounds, and evidence requirements. | 049, 050, 055, 056, 067, 068 | Implemented by `veracrawl-discovery-planner`: `DiscoveryEntryPoint`, `CandidateSourceTarget`, `DiscoveryApprovalDecision`, and `CrawlDiscoveryPlan` carry model/agent/tool/context trace refs, policy refs, command/event/outbox refs, and replay refs; ref-only or framework-native state cannot satisfy the gate. |
| 070 | Unified HTTP Browser Acquisition Escalation Runtime | Escalate from HTTP/structured acquisition to browser rendering when evidence is missing, while preserving sandbox, budget, DOM/network artifacts, and no-bypass policy. | 043, 041, 045, 059, 067, 069 | Implemented by `veracrawl-acquisition-escalation`: `AcquisitionAttemptRecord` requires source artifacts, content hashes, and source anchors for pass, or source limitation refs for needs-review; source-limited cases cannot publish fabricated evidence. |
| 071 | Authorized Source Access And Official API Runtime | Support official APIs and authorized credentialed sessions as first-class source adapters without leaking secrets or bypassing site controls. | 044, 049, 070 | Implemented by `veracrawl-authorized-source`: `AuthorizedSourceAccessRecord` requires credential grant refs, credential audit refs, redacted artifacts, source anchors, content hashes, policy refs, command/event/outbox refs, and replay refs. |
| 072 | Adaptive Frontier Deep Crawl Production Runtime | Execute bounded multi-page crawls with AI-assisted frontier prioritization, pagination/detail traversal, canonicalization, dedupe, rate limits, and replayable stop reasons. | 050, 051, 052, 060, 070 | Implemented by `veracrawl-deep-crawl-production`: the production gate records deep crawl capability refs, bounded coverage metrics, source-backed artifact/hash/anchor refs, policy refs, command/event/outbox refs, and replay refs. |
| 073 | Production Extraction Quality And Oracle Runtime | Convert field-level oracle, precision/recall, confidence calibration, abstention, and publication gating into release-blocking production quality checks. | 061, 062, 072 | Implemented by `veracrawl-production-quality-gate`: the production gate records field-oracle, precision/recall, publication-readiness capability refs, evidence packet refs, verification refs, publication gate refs, source-backed refs, policy refs, command/event/outbox refs, and replay refs. |
| 074 | Production Reliability Operations And Cost Runtime | Prove long-running worker, queue, persistence, object store, retry, recovery, observability, cost, latency, and SLO behavior under production-like runs. | 052, 053, 064, 072, 073 | Implemented by `veracrawl-production-ops-gate`: the production gate records durable-worker, recovery/observability, cost/latency SLO capability refs, metrics, policy refs, command/event/outbox refs, and replay refs. |
| 075 | Production Grade Web Crawler Release Gate | Aggregate 069-074 into one release gate that decides whether VeraCrawl may claim production-grade crawler capability. | 069-074 | Implemented by `veracrawl-production-grade-release-gate`: parsed `ProductionGateReport` artifacts from all six lower gates are required; ref-only lower gate strings, missing lower gates, non-passing lower gates, false-ready guards, blockers, and replay gaps fail the aggregate release. |
| 076 | Amazon Official Product API Adapter | Add a credential-gated Amazon official product API path for source-backed product identity, price, and availability when public/browser product pages are source-limited. | 066, 071 | Implemented by `veracrawl-ecommerce-official-api`: `AmazonCreatorsApiAdapter` lives outside core behind `EcommerceOfficialApiAdapterPort`, requires an operator-provided Creators API endpoint and bearer token or API key, validates endpoint origin, emits credential grant/audit refs, redacted artifacts, source anchors, content hashes, policy refs, command/event/outbox refs, and replay refs, and returns typed `needs_review` when credentials or fields are unavailable. No Amazon SDK/native state is stored in core, and no deprecated PA-API production pass is claimed without credentialed evidence. |
| 077 | eBay Browse API Adapter | Add an official eBay Browse API path for source-backed product search, price, and availability when public item pages are access denied. | 066, 071, 076 | Implemented by `veracrawl-ecommerce-official-api`: `EbayBrowseApiAdapter` lives outside core behind `EcommerceOfficialApiAdapterPort`, supports `EBAY_ACCESS_TOKEN` or OAuth client credentials, calls the official Browse API item summary search endpoint, emits authorized-source/field evidence refs, and reports typed `needs_review` without fabricated price/inventory when credentials, OAuth, source, or field evidence is unavailable. |
| 078 | Delivery ETA Offer Sorting Projection | Extend product crawl output so downstream comparison sites can sort source-backed offers by price, total price, delivery ETA, and availability without fabricating missing fields. | 066, 067, 076, 077 | Implemented by `veracrawl-product-availability-benchmark`: accepted product fields may now include optional `delivery_eta` and `shipping_fee` evidence rows, `ProductAvailabilitySiteResult` carries optional ETA/shipping/total-price values, and `ProductOfferProjectionReport` materializes deterministic sorted offer refs. Delivery ETA remains optional and source-backed; blocked sites, ambiguous ETA copy, and currency-mismatched shipping totals remain absent or typed non-pass. |
| 079 | Query Product Discovery And Offer Ranking | Start from a natural-language product query and allowed ecommerce search/listing entry pages, discover product candidate URLs from source-backed artifacts, then compose product availability extraction and offer ranking without manually supplied product URLs. | 066, 067, 078 | Implemented by `veracrawl-product-discovery`: product discovery source specs, source-backed candidate URL records, a derived product availability manifest, product field evidence, offer projection, ranked offers, model/agent/tool/context traces, policy refs, command/event/outbox refs, and replay refs are materialized. Candidate URLs remain advisory until product availability and evidence gates pass; the Taiwan live fixture currently records PChome sortable offers and Yahoo product-page source access denial as needs-review. |
| 080 | Crawler Intelligence Optimization Roadmap | Fix the finite post-079 optimization spec set for focused frontier scoring, DOM understanding, extraction fallback/confidence, canonical dedupe/identity, ranking, cost/recovery/evaluation gates, runtime wiring, owner-service integration, and end-to-end objective gating. | 075, 079 | Specs 081-097 are defined with purpose, dependency, non-goals, and completion gates; they are post-closure optimization follow-ups and do not replace or weaken the 069-075 production-grade closure gate. |
| 081 | Focused Frontier Scoring Runtime | Replace raw priority integers with replayable score breakdowns and priority/retire/stop decisions based on objective relevance, page type value, URL/anchor/semantic/graph/freshness/history signals, duplicate risk, policy risk, and expected cost. | 072, 028, 051, 060, 080 | Implemented by a scheduler-owned scoring runtime that lowers duplicate fetch/cost rates while preserving required-page recall, policy gates, command/event/outbox refs, and replayable stop reasons. |
| 082 | DOM Page Understanding And Element Ranking Runtime | Produce pruned DOM artifacts, page zone classifications, repeated-block clusters, and interactive element rankings for search, filters, pagination, sort controls, product cards, price blocks, tables, and document metadata. | 045, 070, 081 | Implemented by a normalize/browser-owned DOM intelligence runtime that reduces model context size, preserves anchors, labels prompt-tainted content, and blocks unsafe interactions. |
| 083 | Extractor Fallback And Confidence Runtime | Add a deterministic-first extractor fallback chain, field validators, confidence calibration, abstention, and drift signals before LLM structured extraction fallback. | 046, 047, 073, 082 | Implemented by an extract/evidence/verify runtime where accepted fields pass source-backed oracle thresholds, low-confidence fields abstain, and LLM-only values cannot publish. |
| 084 | Canonical Dedupe And Identity Runtime | Add URL canonicalization policy, query parameter normalization, exact/near duplicate detection, SimHash/MinHash clusters, embedding-advisory clusters, identity resolution, and variant preservation. | 072, 073, 081, 083 | Implemented by normalize/graph/scheduler-owned dedupe decisions that reduce duplicate pollution while preserving true product/article/document/page variants with replay refs. |
| 085 | Recommendation Ranking Runtime | Add generic ranking score records for outputs/offers/documents/facts using intent, evidence quality, source reliability, freshness, availability, price, delivery, confidence, duplicate, and source-limited penalties, with heuristic ranking before learning-to-rank. | 078, 079, 083, 084 | Implemented by a publish/ranking runtime that emits deterministic ranked refs and score explanations without fabricating unsupported fields. |
| 086 | Cost Recovery Evaluation Gates | Aggregate optimization quality, cost, latency, cache, retry, repair, drift, duplicate, ranking, and replay metrics across specs 081-085 into a release-blocking optimization gate. | 074, 081-085 | Implemented by an ops/quality gate that blocks optimization release on missing lower reports, quality regression, unsafe recovery, stale cache reuse, cost/SLO violations, or replay gaps. |
| 087 | Crawler Optimization Runtime Wiring | Wire the spec 080-086 optimization contracts into runtime-safe services for scheduler/frontier, DOM/extraction context, canonical dedupe, ranking, and ops aggregation without adapter or benchmark coupling. | 080-086 | Implemented by adapter-free runtime services, replay helpers, registry entries, and contract/unit/import-boundary tests that allow owner services to consume optimization outputs through typed refs. |
| 088 | Optimization Runtime Activation Roadmap | Fix the finite post-087 owner-service integration spec set for scheduler, DOM normalize, extraction verification, dedupe identity, ranking publication, cost/cache/budget, drift recovery feedback, and regression release gates. | 080-087 | Specs 089-096 are defined and implemented as adapter-free owner-service integration follow-ups without changing the 069-075 production-grade closure gate. |
| 089 | Priority Frontier Scheduler Integration | Wire optimization frontier decisions into scheduler-owned enqueue, block, retire, and stop outcomes. | 081, 087, 088 | Scheduler integration records replayable score-backed frontier adoption refs without agent, benchmark, or adapter coupling. |
| 090 | DOM Intelligence Normalize Integration | Wire DOM context, page zones, retained nodes, and interactive rankings into normalize/browser-owned integration refs. | 082, 087, 088 | Normalize integration preserves anchors, artifact refs, prompt-taint refs, and context reduction metrics. |
| 091 | Extraction Fallback Verification Integration | Wire extractor fallback, field confidence, abstention, and LLM-only rejection into extract/verify boundaries. | 083, 090 | Extract/verify integration accepts source-backed fields and rejects unsupported evidence before publication eligibility. |
| 092 | Canonical Dedupe Identity Integration | Wire canonicalization, fingerprints, identity decisions, duplicate suppression, and variant retention into scheduler/normalize/graph boundaries. | 084, 089, 091 | Dedupe integration suppresses tracking duplicates while preserving variants and replaying identity decisions. |
| 093 | Recommendation Ranking Publication Integration | Wire ranking scores and ranked output sets into publish/projection boundaries without changing verification status. | 085, 091, 092 | Ranking integration emits ranked refs for retained verified outputs without fabricating optional fields. |
| 094 | Optimization Cost Cache Budget Runtime | Wire optimization cost, cache freshness, fetch/browser/token budgets, and metrics into ops-owned integration refs. | 086, 089-093 | Cost/cache integration fails stale cache reuse, budget overrun, missing metrics, and missing replay refs. |
| 095 | Drift Recovery Feedback Runtime | Wire selector drift, retry classification, repair outcomes, and memory advisory refs into recovery feedback. | 083, 086, 091, 094 | Drift feedback remains advisory, replayable, and blocked on unsafe recovery or owner bypass. |
| 096 | Optimization Regression Release Gate | Aggregate 089-095 integration refs and metrics into a release-blocking optimization regression gate. | 089-095 | Regression gate passes only with complete lower integration refs, metric refs, replay refs, and no quality/duplicate/ranking/cost/recovery regression. |
| 097 | Optimization Objective Gate | Aggregate lower 096 regression gates, deterministic weighted OptimizationScore reports, and observe/think/act/verify agent decision-loop evidence into the final optimization claim. | 080-096 | Objective gate passes only when supplied lower gates, objective score reports, agent loop evidence, policy refs, command/event/outbox refs, artifact refs, and replay refs prove the recorded corpus is faster, more accurate, and cheaper. |

Activation rule: when a planned spec is activated, preserve its number and
directory, run the Spec Kit clarify/plan/tasks/analyze/implement workflow, record
real validation in `tasks.md`, and merge it before moving to the next blocking
spec.

Specs 065, 066, and 067 are explicitly amended market validation benchmarks.
They do not claim deep category/product search traversal production readiness
beyond the recorded public homepage and declared product-page experiments.
Specs 068-075 are the finite production-grade closure specs required before
VeraCrawl may claim full production-grade web crawler capability.
Specs 076-079 are ecommerce market follow-ups layered on top of that closure:
official API paths for source-limited platforms, sortable offer projection for
price/arrival/inventory comparison output, and query-driven product discovery so
ecommerce comparison tests do not depend on manually supplied product URLs.
Specs 080-097 are post-079 crawler intelligence optimization follow-ups:
focused frontier scoring, DOM understanding, extractor fallback/confidence,
canonical dedupe/identity, generic recommendation ranking, and aggregate
cost/recovery/evaluation gates, runtime wiring, owner-service integration, and
the final objective/agent decision release gate that exposes those contracts
through adapter-free owner boundaries. They improve
validated quality and efficiency without replacing or weakening the 069-075
production-grade closure gate.

Current production-grade claim status: specs 068-075 are implemented and the
2026-05-04 follow-up live production evidence run passed the aggregate 075 gate
with parsed reports for 069, 070 live acquisition, 071 live official API,
072 deep crawl, 073 live extraction quality, and 074 operations reliability.
This supports claiming production-grade capability for the recorded validation
corpus. It does not mean every target website is crawlable: the row 066 Amazon
follow-up now has source-backed HTTP and browser DOM price/availability evidence
for the recorded product run, while eBay item access, Shopee Taiwan access, and
some forced browser-source ecommerce pages such as Walmart can still be
source-limited by human-check pages. Those outcomes must remain
operator-visible needs-review/blocked results unless solved through official
APIs or explicitly authorized sources.

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
