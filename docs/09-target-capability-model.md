# Target Capability Model

This document defines the target capability of VeraCrawl. It is not a V1 scope document.

VeraCrawl must become a powerful general-purpose AI agent web crawler. V1/V2/V3 boundaries are dependency and validation boundaries only. They must not be used to shrink the product ambition, weaken architecture, or claim target capability before it exists.

## Governing Rules

Target capability planning follows these rules:

- Plan the full desired capability first.
- Do not reduce capability because of schedule, staffing, sprint pressure, or delivery speed.
- Sequence work only by technical dependency, correctness, validation, risk isolation, and integration order.
- Do not mark a capability complete because a prototype, mock, demo, prompt, or static report exists.
- A capability is complete only when implementation, tests, replay evidence, operational observability, and acceptance gates pass.
- If a target capability is not implemented yet, documents and UI must say so directly.

## Target Capability Statement

At target architecture, VeraCrawl must accept high-level crawl and extraction objectives, understand unfamiliar websites, plan crawl strategies, operate within explicit customer authorization and policy, adapt to site structure and drift, extract structured outputs, verify evidence, preserve replay, learn from prior runs, and scale across many websites and data domains.

The target product must support:

- objective-driven crawling across many site types
- AI site understanding and crawl planning
- adaptive frontier scheduling
- HTTP, sitemap, RSS, API, browser, document, and authorized session adapters
- JavaScript-rendered page observation through controlled browser execution
- listing/detail, pagination, search, form, canonical, redirect, feed, document, and API-like patterns
- schema-guided and approved exploratory extraction
- records, tables, document metadata, files, datasets, and factual outputs
- evidence packets for every published output
- verification decisions and conflict handling
- URL, page-structure, entity, source/evidence, task, and temporal graph projections
- scoped long-term site, task, extraction, failure, repair, and agent memory
- multi-agent planning, extraction, verification, drift repair, memory, and operations workflows
- replayable commands, events, tool calls, model calls, policy decisions, and publication decisions
- review, correction, withdrawal, result delivery, and export reconciliation
- production observability, cost controls, queueing, backpressure, security, privacy, retention, and disaster recovery

## Target Buyer, User, And Value Model

Target buyers:

- head of data platform
- head of AI platform
- head of data operations
- VP or director of engineering for data-intensive products
- platform owner responsible for governed external data acquisition

Target users:

- data engineers building and operating repeatable web data pipelines
- AI platform engineers supplying evidence-backed web context to downstream AI systems
- data operations analysts reviewing extraction quality, evidence, and conflicts
- crawl operators managing freshness, failures, cost, and site health
- compliance, security, or governance reviewers auditing source access and evidence lineage

Core jobs-to-be-done:

- turn a high-level data objective into an approved, policy-compliant crawl plan
- onboard unfamiliar websites without writing bespoke scraper code for each one
- handle static, dynamic, authenticated, feed, API-like, document, and drifted source patterns through governed adapters
- publish structured outputs only when evidence and verification gates pass
- explain every output, failure, policy decision, agent action, and export delivery
- reuse graph and memory intelligence without letting either replace source evidence
- repair crawl and extraction failures without silently corrupting data
- operate many sites with cost, freshness, privacy, and reliability controls

Buying triggers:

- scraper maintenance cost grows faster than the data team can staff
- LLM extraction is fast but not auditable, replayable, or safe enough for production
- current crawlers fail on site drift, JavaScript rendering, evidence requirements, or review workflows
- downstream AI systems need trustworthy web data with provenance and update/correction behavior
- regulated or customer-facing workflows require source, policy, credential, and export audit trails

Target workflow:

```text
Create project and governed source scope
  -> define objective, schema, evidence requirements, and freshness policy
  -> AI proposes crawl plan, adapters, graph/memory use, risks, and alternatives
  -> operator approves plan and policy decisions
  -> crawler executes HTTP/browser/session/feed/API/document adapters
  -> agents classify site structure, manage frontier, extract candidates, build evidence, recommend verification, detect drift, and propose repair
  -> reviewers accept/reject/conflict/adjudicate outputs through evidence views
  -> publication service emits immutable outputs and manifests
  -> exports deliver outputs and record receipts
  -> corrections, withdrawals, retention changes, and projection rebuilds remain auditable
  -> future runs reuse scoped graph and memory while re-anchoring publication to evidence
```

Value mapping:

| Capability profile | User value | Buyer value |
| --- | --- | --- |
| Core Production | repeatable objective-to-output workflow with evidence and replay | lower maintenance risk and auditable web data pipelines |
| Dynamic Web | controlled support for JavaScript-heavy sites | broader source coverage without unsafe browser shortcuts |
| Authorized Session | governed use of customer-provided credentials | access to authorized sources with audit and secret isolation |
| Source/Pattern/Output Coverage | explicit support for every target adapter, website pattern, and output type | confidence that VeraCrawl is general-purpose rather than a narrow crawler |
| Graph Intelligence | better discovery, dedup, freshness, drift, and relationship visibility | higher coverage and fewer silent data quality failures |
| Memory Intelligence | less relearning across runs and faster repairs | compounding operational leverage without sacrificing evidence |
| Multi-agent Operations | specialized AI help for planning, extraction, verification, repair, and ops | scalable expert workflows without unbounded autonomous risk |
| Security, Privacy, And Lifecycle | safe source access, credential isolation, artifact lifecycle, and audit paths | governance readiness for regulated or customer-facing use |
| Scale And Reliability | fair, resilient execution across many sites | production readiness for platform-wide adoption |
| Export And Correction | delivery receipts, correction, withdrawal, and downstream reconciliation | governed integration with business systems and AI pipelines |

Technical target readiness is not enough for product readiness. Target product readiness also requires these user and buyer workflows to pass the product acceptance gates in [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md).

## Safety Boundary

Target capability does not mean unrestricted crawling.

VeraCrawl must support authorized and controlled acquisition. It must not include mechanisms for CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

Target support for authenticated sources means customer-authorized, scoped credential use through policy, vaulting, auditing, and replay. It does not mean circumventing access controls.

## Capability Areas

| Area | Target capability | Required proof |
| --- | --- | --- |
| Objective understanding | Convert high-level user goals into explicit crawl objectives, schema needs, policy constraints, and success criteria | objective trace, approved plan, ambiguity log, replay event |
| Crawl planning | Generate crawl plans with adapters, seeds, expected page types, frontier strategy, evidence requirements, budget, and risk notes | plan approval, policy checks, run plan snapshot |
| Source adapters | Support HTTP, sitemap, RSS, API, file/document, browser snapshot, manual seed, prior snapshot, and authorized session adapters | adapter contract tests, `SourceAdapterResult` records, policy decisions, `source_adapter_result_recorded` events, adapter-native output refs |
| Browser observation | Observe JavaScript-rendered pages, DOM state, screenshots, network metadata, and controlled interactions within policy | browser sandbox tests, budget tests, screenshot/DOM artifact refs |
| Authorized sessions | Use scoped customer credentials for approved sites and actions | vault access log, credential policy decision, redacted prompt/context tests |
| Site understanding | Infer navigation, page types, templates, duplicate zones, low-value zones, API-like endpoints, forms, and search paths | site model, graph projection, classifier metrics, review report |
| Adaptive frontier | Prioritize, retire, retry, and expand frontier items from objective relevance, graph signals, freshness, uncertainty, failures, and budgets | frontier state tests, priority explanation, replayable transitions |
| Extraction | Produce schema-bound candidates from normalized documents, DOM anchors, tables, structured data, scripts, PDFs, and approved document text | extraction strategy, candidate refs, validator result, anchor maps |
| Evidence | Build source-backed evidence packets for records, tables, document metadata, files, datasets, and facts | evidence coverage map, raw-to-normalized replay, source anchors |
| Verification | Accept, reject, review, conflict, supersede, or expire outputs by policy, evidence, schema constraints, freshness, and contradiction checks | verification decision, conflict record, output verification aggregate |
| Publication | Publish only verified outputs with immutable manifests and evidence refs | output manifest, publication event, review decision, result receipt |
| Graph intelligence | Maintain URL, hyperlink, canonical, redirect, page-structure, entity, citation/source, evidence, task, and temporal graph projections | graph build manifest, projection watermark, graph quality report |
| Memory intelligence | Store scoped memories for site behavior, page types, extraction repairs, failures, task context, and agent diaries with freshness and evidence refs | memory event, retrieval trace, invalidation test, evidence backrefs |
| Multi-agent orchestration | Coordinate Planner, Site Understanding, Frontier, Fetch Analysis, Extractor, Verifier, Drift, Memory, and Ops agents through tools and policy gates | tool call trace, permission tests, command/result events |
| Drift and repair | Detect template, selector, schema, content, graph, and source behavior drift; propose repairs without silent data corruption | drift event, repair proposal, before/after verification |
| Review and operations | Provide evidence viewer, replay console, review queue, graph explorer, run dashboard, quality reports, and operator controls | console/API acceptance tests, operator task completion tests |
| Export and correction | Deliver outputs to files, APIs, databases, warehouses, object stores, and queues; reconcile delivery and withdrawals | export receipt, outbox tests, withdrawal propagation tests |
| Scale and resilience | Run site-sharded queues, autoscaling workers, backpressure, retries, dead letters, projection rebuilds, and disaster recovery | load tests, chaos tests, recovery tests, replay completeness report |
| Security and privacy | Enforce egress controls, prompt-injection boundaries, credential isolation, artifact privacy classification, retention, deletion, and redaction propagation | security tests, privacy lifecycle tests, audit logs |

## Website Pattern Coverage

Target VeraCrawl must handle these authorized website patterns:

| Pattern | Target behavior | Completion gate |
| --- | --- | --- |
| Static content | Crawl linked pages and extract schema-bound outputs | fixture and external-style benchmark pass |
| Sitemap/RSS/feed | Discover pages from structured feeds and reconcile freshness | feed delta and freshness tests pass |
| Listing/detail | Identify listings, details, pagination, duplicates, and canonical URLs | site model and extraction tests pass |
| Search pages | Execute bounded, policy-approved search queries and process result pages | policy, budget, and replay tests pass |
| Forms | Interact with approved non-destructive forms for discovery or retrieval | form policy and sandbox tests pass |
| JavaScript pages | Render required DOM states with browser workers and capture artifacts | browser artifact and cost tests pass |
| Authenticated sources | Use scoped customer-provided credentials without exposing raw secrets to agents, prompts, logs, replay bundles, or untrusted page text | vault, prompt redaction, origin allowlist, and audit tests pass |
| API-like endpoints | Detect and use approved structured endpoints when policy permits | adapter tests and provenance tests pass |
| Documents | Fetch and normalize supported document formats with anchor maps | document normalization and evidence tests pass |
| Multi-language pages | Preserve language metadata and support language-aware extraction | language fixture tests pass |
| Drifted sites | Detect changes and route repair/review instead of silently corrupting data | drift and repair tests pass |
| High-volume sites | Maintain queue fairness, budgets, and backpressure | load and starvation tests pass |

## Target Profiles

Target completion is evaluated by capability profiles. A profile may be validated independently, but the product must not claim full target capability until all required target profiles pass.

### Core Production Profile

Required capabilities:

- objective, plan, job, run, frontier, fetch, normalize, extract, evidence, verify, publish, review, export, replay
- durable metadata, object artifacts, event log, command/result handling, policy decisions
- local/API results plus delivery receipts

Required acceptance:

- every published output has evidence
- every mutating or publication-relevant action is replayable
- interrupted runs resume without corrupting state
- policy-blocked sources are reported, not bypassed

### Dynamic Web Profile

Required capabilities:

- browser render workers
- DOM/screenshot/network artifacts
- browser budget gates
- JavaScript page type classification
- controlled interaction steps for approved discovery patterns

Required acceptance:

- browser execution is sandboxed
- raw secrets are not exposed to agents, model prompts, logs, replay bundles, or untrusted page text
- any customer-approved credential presentation to an authorized origin uses scoped headers, scoped cookies, request signing, or vault-brokered form fill with `CredentialUseAudit`
- browser minutes and artifacts are traceable to outputs

### Authorized Session Profile

Required capabilities:

- credential vault integration
- session adapter contracts
- scoped credential policies
- secret redaction
- customer authorization records

Required acceptance:

- credentials are never available to agents as raw prompt text
- raw secrets are never serialized into model requests, logs, replay bundles, or untrusted page text
- origin-visible credential presentation is allowed only for customer-authorized origins through audited scoped delivery modes
- every credential use has policy, approval, and audit records
- failed or blocked access is reported instead of bypassed

### Source Adapter, Website Pattern, And Output Coverage Profile

Required capabilities:

- all target adapters: HTTP, sitemap, RSS, browser snapshot, authorized session, API source, document source, file import, manual seed, and prior snapshot
- all target website patterns: static, sitemap/RSS/feed, listing/detail, search, non-destructive forms, JavaScript pages, authenticated sources, API-like endpoints, documents, multi-language pages, drifted sites, and high-volume sites
- all target output types: record, table, document metadata, document, file, dataset, and fact
- fixture manifests, expected output oracles, graph oracles, event oracles, evidence coverage, policy decisions, and replay bundles for each supported surface

Required acceptance:

- every target adapter has contract, policy, replay, and fixture coverage
- every website pattern has a deterministic benchmark fixture and pass/fail oracle
- every output type has evidence coverage and publication acceptance checks
- no adapter, pattern, or output type can be labeled target-complete while scaffolded, untested, or manually simulated

### Graph Intelligence Profile

Required capabilities:

- URL, hyperlink, redirect, canonical, page-structure, entity, source/evidence, task, and temporal graph projections
- graph build manifests and rebuild watermarks
- graph quality metrics
- graph-influenced frontier explanations

Required acceptance:

- graph projections can be rebuilt from canonical events and artifacts
- graph signals never replace source evidence
- graph-influenced decisions are explainable and replayable

### Memory Intelligence Profile

Required capabilities:

- site, task, page type, extraction, failure, repair, and agent memory
- scoped retrieval
- freshness scoring
- invalidation
- evidence backrefs

Required acceptance:

- memory is never source of truth for publication
- memory-derived extraction strategies re-anchor to current or selected historical evidence
- stale memory can be invalidated and excluded from planning

### Multi-agent Operations Profile

Required capabilities:

- Planner, Site Understanding, Frontier, Fetch Analysis, Extractor, Verifier, Drift, Memory, and Ops agents
- framework-neutral agent runtime
- tool gateway permissions
- agent action trace
- repair loops

Required acceptance:

- agents cannot directly mutate durable stores
- each tool call is validated by typed contracts and policy
- framework-native state is not canonical state

### Export And Correction Profile

Required capabilities:

- file, API, database, warehouse, object store, and queue export targets
- outbound outbox and idempotent dispatch
- delivery receipts and destination object mappings
- correction, supersession, withdrawal, delete propagation, and export reconciliation
- export status, receipt, and withdrawal viewer

Required acceptance:

- every delivered output has a receipt or explicit destination failure
- duplicate dispatch does not create duplicate accepted downstream records
- output correction or withdrawal propagates to every capable destination
- unsupported destination withdrawal behavior is reported and reviewed
- export and withdrawal behavior is replayable from events and receipts

### Security, Privacy, And Lifecycle Profile

Required capabilities:

- egress allowlists and private-network deny rules
- browser and fetch sandboxing
- prompt-injection and content taint boundaries
- credential isolation and audit
- artifact privacy classification, PII scan refs, redaction, tombstone, deletion, legal hold, retention, and projection cleanup
- policy decisions for browser interactions, memory retrieval, graph signal use, export, recovery, and artifact lifecycle actions

Required acceptance:

- unsafe network, prompt, credential, browser, or memory actions are blocked and logged
- raw secrets never enter agents, model prompts, logs, replay bundles, captured artifacts, or untrusted page text
- customer-authorized origin credential presentation is allowed only through audited scoped delivery modes with origin allowlist and `CredentialUseAudit`
- redaction, tombstone, delete, retention, and legal hold actions propagate to projections
- replay remains structurally complete under redaction
- security/privacy gates pass before target capability can be claimed

### Scale And Reliability Profile

Required capabilities:

- site-sharded queues
- autoscaling workers
- backpressure
- fairness controls
- dead-letter handling
- projection rebuilds
- disaster recovery
- load testing

Required acceptance:

- one bad site cannot starve unrelated jobs
- crash/restart scenarios preserve replay and state correctness
- projections can rebuild from canonical source of truth

## Completion States

Every capability must use one of these states:

| State | Meaning |
| --- | --- |
| planned | documented target capability with owner, contracts, and acceptance gates |
| designed | implementation design exists with ports, data contracts, storage, events, and tests |
| implemented | production code exists behind stable contracts |
| verified | automated tests, replay checks, and acceptance scenarios pass |
| operational | metrics, traces, alerts, runbooks, failure handling, and recovery paths exist |

Do not use `complete` unless the capability is both `verified` and `operational`.

## Non-deceptive Claims

VeraCrawl must never claim:

- arbitrary web mastery without benchmark evidence
- full target architecture if any target profile is only planned or designed
- verified output if evidence coverage is missing
- memory-backed output as source-backed proof
- graph-inferred relationship as source evidence
- browser or authenticated capability without sandbox, policy, and audit tests
- production export completion without delivery receipts and withdrawal behavior

If a capability is scaffolded but not validated, documents, specs, release notes, and UI must call it scaffolded or experimental.
