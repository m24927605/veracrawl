# Production Architecture

## System Shape

```text
Control Plane
  -> Project / Site / Objective / Job Spec
  -> Scope / Rate / Budget / Credential Vault
  -> Schema Registry
  -> Agent Policy / Tool Registry
  -> Policy Guard

Agent Plane
  -> Objective Interpreter
  -> Crawl Planner
  -> Site Understanding Agent
  -> Frontier / Extraction / Verification Agents
  -> Drift Repair Agent
  -> Agent Tool Gateway
  -> Policy Decision Logger
  -> Prompt Injection / Taint Guard
  -> Agent Action Event Log

Crawl Plane
  -> Frontier Scheduler
  -> HTTP Fetch Workers
  -> Browser Render Workers
  -> Sitemap / RSS / API / File Adapters
  -> Retry / Backoff / Dedup / Canonicalization

Intelligence Plane
  -> DOM / Text Normalizer
  -> Page Type Classifier
  -> Entity / Output Extractor
  -> Evidence Packet Builder
  -> Verifier
  -> Drift Detector

Memory Plane
  -> Raw Snapshot Store
  -> Drawer / Closet Memory
  -> Temporal Knowledge Graph Retrieval
  -> Site / Task / Agent Diaries
  -> Cross-site Tunnels

Data Plane
  -> Object Store
  -> Postgres Metadata
  -> Search Index
  -> Vector Index
  -> Graph Store
  -> Temporal Knowledge Graph Projection
  -> Result API
  -> Export Workers

Ops Plane
  -> Metrics / Logs / Traces
  -> Replay Console
  -> Quality Dashboard
  -> Alerting
  -> Cost Controls
```

The system shape is the full target architecture. V1 uses a narrower slice: Objective Interpreter, constrained Planner, Site Understanding/Extraction loop, policy gateway, HTTP fetch workers, normalization, evidence, verification service, publication service, minimal review/replay surface, and file/API export.

## V1 Module Boundaries

V1 implementation should be packaged by dependency direction:

```text
contracts
  <- policy
  <- runtime-events
  <- control-api
  <- scheduler
  <- fetch
  <- normalize
  <- extract
  <- evidence
  <- verify
  <- publish
  <- review-replay
  <- local-export
```

Rules:

- `contracts` has no dependency on services.
- workers depend on contracts and policy, not on each other.
- agents call tools exposed by services; agents do not import worker internals.
- V1 packages must not import target-only graph, memory, warehouse export, or cross-site tunnel modules.
- target-only contracts can exist as docs, but V1 code paths must reject non-V1 profile values.

## Implementation Technology Baseline

VeraCrawl's implementation language is Python.

Core implementation rules:

- V1 services, workers, contracts, policy checks, event handling, and agent runtime abstractions should be implemented in Python.
- Contracts should be expressed as framework-neutral Python types and schemas before they are bound to any storage, API, queue, or model provider.
- Python package boundaries should follow the V1 module dependency direction instead of convenience imports.
- Framework-specific objects must not cross service, event, persistence, or contract boundaries.

The AI agent layer must remain independent of any agent framework.

Agent framework rules:

- Core services must not depend on LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or any equivalent agent framework.
- Any model provider, agent SDK, tool-calling runtime, or orchestration framework must be wrapped behind a VeraCrawl-owned adapter interface.
- Durable state stores only VeraCrawl contracts, commands, events, tool calls, policy decisions, and artifact refs; it must not store framework-native traces or opaque framework state as source of truth.
- The V1 agent loop should be small and explicit: prepare context refs, call model or adapter, validate tool request, execute approved tool through the gateway, persist typed result, and emit replay events.
- A framework can be added later only as a replaceable adapter when it passes replay, policy, observability, and contract-boundary tests.

## Control Plane

The control plane owns configuration, user intent, and governance.

Responsibilities:

- create projects, sites, objectives, jobs, and runs
- store job specs and schema specs
- store user crawl objectives and approved crawl plans
- define allowed source adapters
- manage credentials and secrets through a vault
- enforce scope, budgets, and rate constraints
- enforce robots, terms, authorization, privacy, and retention policy
- version extraction schemas
- define agent tool permissions and approval rules
- approve or pause jobs

Key design choice: crawl workers and agents should not invent policy. They receive an already-resolved run configuration and operate through approved tools.

## Agent Plane

The agent plane turns high-level crawl objectives into executable, inspectable crawl behavior.

Responsibilities:

- interpret natural-language crawl objectives
- propose crawl plans and source adapter choices
- infer likely site structure and page types
- guide frontier prioritization
- propose extraction strategies and schema mappings
- request additional evidence when extraction is uncertain
- diagnose fetch, extraction, and drift failures
- write replayable agent action events
- label untrusted web content before prompt construction
- log policy decisions for plan, tool, fetch, credential, prompt, and publication gates

Agents may propose plans, create candidates, request frontier updates, and submit verification recommendations through controlled tools. They must not directly mutate durable core stores or publish outputs without the verification and publication boundary.

Untrusted web content may inform agent reasoning, but it must not issue instructions to tools or expose secrets. The agent tool gateway should enforce trust labels, sanitized context refs, credential isolation, and policy decisions before any mutating action.

## Crawl Plane

The crawl plane executes discovery and fetching.

Components:

- Frontier Scheduler
- URL canonicalizer
- dedup service
- HTTP fetch workers
- browser render workers
- source adapters
- retry manager
- content hash service
- snapshot writer

The frontier is not a simple queue. It should be a prioritized crawl and fetch task graph with state:

- discovered
- eligible
- scheduled
- fetching
- fetched
- failed
- retired

Normalization, extraction, evidence building, verification, and publication should have their own processing tasks or artifact states. A single fetched URL can produce multiple documents, candidates, and published outputs with independent success and failure states.

Priority inputs:

- user objective relevance
- AI crawl plan
- job objective relevance
- graph distance from high-value pages
- freshness debt
- uncertainty
- historical failure rate
- page type value
- project priority
- cost budget

Graph signals should not directly increase extraction or verification confidence in V1. They can guide what to fetch, what to review first, and where to look for drift or duplicates.

## Intelligence Plane

The intelligence plane turns observations into extraction candidates and publishable outputs. Verified facts are a specialized output type for factual claims.

Pipeline:

```text
CrawlObjective
  -> CrawlPlan
  -> FrontierItem
  -> FetchResult
  -> PageSnapshot
  -> NormalizedDocument
  -> PageTypeClassification
  -> ExtractionCandidate
  -> EvidencePacket
  -> VerificationDecision
  -> PublishedOutput
  -> VerifiedFact when the output is a factual claim
```

Rules:

- LLM output can produce candidates, not direct facts.
- Each candidate must include evidence anchors.
- Agent plans and extraction strategies must be stored as replayable events.
- Agent verification output is a recommendation unless a policy or human gate accepts it.
- Verification must be deterministic where possible.
- Schema drift should create review events, not silent data changes.
- Low-confidence extraction should remain queryable but not published as verified output.

## Memory Plane

The memory plane helps agents and schedulers avoid rediscovering the same context and improves future crawl planning, extraction, and repair.

It stores:

- site structure memories
- task memories
- page type memories
- extraction memories
- known failure patterns
- cross-site pattern tunnels
- agent diaries

Memory should be scoped by project, site, page type, entity, objective, and crawl run. Global search is useful, but scoped search must be the default.

Memory may reference temporal facts and graph projections, but it should not be the writer of authoritative facts. Temporal KG updates should be derived from verified outputs and append-only events.

## Data Plane

Recommended storage split:

- Object store: raw snapshots, screenshots, text snapshots, large artifacts.
- Postgres: jobs, runs, frontier items, metadata, facts, evidence packet indexes.
- Search index: BM25 and exact text search.
- Vector index: semantic recall.
- Graph store: URL graph, entity graph, page type graph.

The same data should not be copied blindly across all stores. Each store should have a clear access pattern.

Artifact lifecycle must be runtime-owned:

- every raw, normalized, screenshot, and export artifact carries privacy classification
- PII scan results and redaction refs are recorded before broad indexing
- retention, legal hold, tombstone, deletion, and projection cleanup are tracked
- secondary indexes must receive delete or redaction propagation events

## Ops Plane

Production crawling fails constantly. The ops plane must make failure visible.

Minimum metrics:

- pages fetched per minute
- error rate by site and adapter
- retry rate
- browser minute usage
- queue lag
- extraction success rate
- verification rejection rate
- drift rate
- freshness lag
- cost per published output
- storage growth
- token usage

Minimum traces:

- objective interpretation trace
- crawl planning trace
- job run trace
- agent tool call trace
- frontier decision trace
- fetch trace
- extraction trace
- verification trace
- memory retrieval trace

## Deployment Shape

Baseline production deployment:

- API service
- scheduler service
- fetch worker pool
- browser worker pool
- extraction worker pool
- verification worker pool
- memory worker
- graph worker
- metrics and tracing stack
- object storage
- Postgres
- queue
- search/vector backend

Workers should be stateless except for temporary execution cache. Durable state belongs to the queue, database, and object store.

## V1 Minimal Deployment

V1 should be runnable before the full production deployment:

- single API/control process
- embedded scheduler loop
- HTTP fetch worker in-process or one worker process
- normalization/extraction/evidence/verification workers in-process
- local filesystem or S3-compatible object store
- Postgres as the default metadata store
- queue can be Postgres-backed for V1
- browser worker disabled by default
- graph worker limited to URL/page-structure graph
- memory worker disabled; run diary events only
- search/vector backend disabled by default
- local result materialization and Result API before production export connectors

Full deployment splits these into separate services when scale, isolation, or customer requirements justify it.

## Ownership And Consistency

Each aggregate should have a single writer service:

- Control plane owns projects, sites, objectives, policies, schemas, and approved crawl plans.
- Scheduler owns frontier transitions.
- Fetch workers own fetch attempts and snapshot write requests.
- Normalization and extraction workers own normalized documents, classifications, candidates, and evidence build tasks.
- Verification service owns verification decisions.
- Publication service owns published outputs. Export service owns export jobs, delivery receipts, withdrawals, and export reconciliation.
- Memory worker owns memory events and retrieval indexes.
- Graph worker owns graph projections and graph signals.

Cross-service changes should flow through commands and append-only events. Search, vector, graph, and temporal KG stores are projections with replay watermarks, lag SLOs, rebuild rules, and stale invalidation rules. Postgres metadata, object artifacts, and the event log remain the source of truth for replay.

Command flow:

```text
CommandEnvelope
  -> policy and approval checks
  -> aggregate owner applies transition with expected version
  -> CommandResult
  -> append-only events
  -> projections and outbound dispatch
```

Publication and export side effects should use an outbound outbox. Export workers may dispatch only committed, current, policy-allowed immutable output manifests. Delivery receipts, withdrawals, and delete propagation must reconcile back to events.

Failures should produce `FailureRecord` and optional `RecoveryAction` objects. Recovery must handle retryable commands, orphan artifacts, partial publication, partial export, projection rebuilds, and compensating withdrawals.

## Runtime Security

Fetch and browser execution must be sandboxed:

- enforce egress allowlists and private-network denylists
- block file URLs unless explicitly authorized
- defend against DNS rebinding and internal network probing
- cap response, download, DOM, screenshot, and artifact sizes
- isolate browser contexts and credential injection
- broker credentials through scoped vault access
- record policy decisions for fetches, prompt context, and credential use

## Runtime Guardrails

Backpressure and cost controls are baseline runtime features, not late hardening:

- per-project and per-site concurrency limits
- browser minute, token, queue, storage, and runtime budgets
- queue visibility timeout and dead-letter handling
- per-site failure circuit breakers
- budget-triggered pause and review
