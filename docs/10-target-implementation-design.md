# Target Implementation Design

This document defines how VeraCrawl must be implemented to reach target architecture capability. It is intentionally broader than the V1 production spine.

The design assumes:

- implementation language: Python
- architecture style: low coupling, high cohesion, explicit ports and adapters
- agent runtime: VeraCrawl-owned and framework-neutral
- product target: general-purpose AI agent web crawler with graph, evidence, memory, multi-agent, browser, export, scale, and operations capability

## Implementation Principles

1. Build the target architecture, not a disguised scraper.
2. Keep canonical domain state in VeraCrawl contracts, events, commands, policies, artifact refs, and manifests.
3. Keep external frameworks, model SDKs, browser engines, databases, queues, and object stores behind adapters.
4. Make each package cohesive around one responsibility.
5. Use command/event boundaries for cross-module behavior.
6. Make replay, evidence, policy, and observability first-class implementation surfaces.
7. Never mark a capability complete until implementation and acceptance tests prove it.

## Target Package Map

Target Python packages must follow this dependency direction:

```text
veracrawl.contracts
  <- veracrawl.policy
  <- veracrawl.runtime_events
  <- veracrawl.ports
  <- veracrawl.control
  <- veracrawl.scheduler
  <- veracrawl.fetch
  <- veracrawl.browser
  <- veracrawl.normalize
  <- veracrawl.extract
  <- veracrawl.evidence
  <- veracrawl.verify
  <- veracrawl.publish
  <- veracrawl.artifact_lifecycle
  <- veracrawl.projection
  <- veracrawl.graph
  <- veracrawl.memory
  <- veracrawl.agents
  <- veracrawl.review_replay
  <- veracrawl.export
  <- veracrawl.ops
  <- veracrawl.adapters
```

Rules:

- `contracts` contains stable domain models, schema definitions, enums, IDs, validation helpers, and serialization rules.
- `ports` contains Python protocols for storage, queue, object store, model provider, browser, graph, memory, export, metrics, tracing, and clock/randomness.
- domain packages depend on `contracts`, `policy`, `runtime_events`, and `ports`; they do not depend on concrete adapters.
- `adapters` contains concrete integrations for Postgres, object storage, queues, browser engines, model providers, graph stores, search/vector stores, and export targets.
- adapters depend inward; core packages must not import adapters.
- agent orchestration depends on tool contracts and ports, not worker internals.

## Target Architecture Foundation Slice

The first implemented foundation package map must materialize the architectural
surface that later crawler runtime specs build on:

- `veracrawl.contracts`: Pydantic contracts for commands, events, policy decisions,
  source adapter specs/results, framework-neutral agent runtime specs/traces, replay
  manifests, fixture manifests, and fixture oracles.
- `veracrawl.ports`: protocol-only boundaries for storage, source adapters, agent
  runtime/model/tool/context access, deterministic clock, and deterministic randomness.
- `veracrawl.runtime_events`: append-only in-memory event store and replay completeness
  checks for foundation tests.
- `veracrawl.policy`: policy gate primitives that emit explicit allow, deny, or
  require-review decisions.
- `veracrawl.agents`: framework-neutral runtime helpers, tool gateway validation,
  and adapter conformance assertions that depend only on VeraCrawl contracts/ports.
- `veracrawl.adapters`: conformance stub adapters for source families and agent
  framework families. Real OpenAI Agent SDK, LangGraph, LangChain, CrewAI, AutoGen,
  Semantic Kernel, browser, storage, and queue dependencies remain adapter-owned.
- owner packages for `control`, `scheduler`, `fetch`, `browser`, `normalize`,
  `extract`, `evidence`, `verify`, `publish`, `artifact_lifecycle`, `projection`,
  `graph`, `memory`, `review_replay`, `export`, and `ops` exist as package boundaries
  before their production internals are implemented.

This slice is complete only when registry validation, import-boundary tests, adapter
conformance tests, replay tests, policy tests, and deterministic fixture/oracle
negative cases all pass. It must not be described as a completed production crawler
runtime; it is the foundation that prevents later runtime work from becoming a
single-site scraper or framework-coupled agent script.

## Target Runtime Spine Slice

The next implemented slice materializes the first executable target runtime spine.
It keeps the same target architecture constraints while adding deterministic runtime
behavior across owner packages:

- `veracrawl.contracts`: objective, plan, run, run-plan snapshot, runtime completion
  gate, runtime artifact ref, normalized document, extraction candidate, evidence
  coverage, evidence packet, verification decision, published output, output
  manifest, and agent recommendation contracts.
- `veracrawl.ports`: runtime repository and artifact store protocols for replacing
  deterministic fixture storage with production adapters later.
- `veracrawl.runtime_support`: in-memory repository profile used only behind ports.
- `veracrawl.artifact_lifecycle`: deterministic artifact store with content digest,
  lifecycle ref, privacy classification, and retention ref.
- `veracrawl.control`: objective-to-run bootstrap, owner command validation,
  command result creation, completion gate evaluation, and deterministic fixture
  orchestration.
- `veracrawl.fetch`, `normalize`, `extract`, `evidence`, `verify`, `publish`, and
  `review_replay`: cohesive owner-service runtime functions for source results,
  processing, source-backed evidence, verification, publication preconditions, and
  replay bundle validation.
- `veracrawl.agents`: framework-neutral recommendation intake. Accepted
  recommendations become owner-service commands; rejected recommendations preserve
  typed rejection reasons. Core state never depends on OpenAI Agent SDK, LangGraph,
  LangChain, CrewAI, AutoGen, Semantic Kernel, or framework-native state.
- `veracrawl.cli.runtime`: `veracrawl-runtime run` fixture runner that writes
  deterministic JSON reports under `.veracrawl-test-runs/`.

This slice proves the target architecture spine can move from approved objective to
published output with evidence and replay, and can block source policy denial,
missing evidence, verification conflict, adapter natural-result mismatch, replay
gap, and wrong-owner mutation. It does not implement full browser capability, graph
intelligence, memory intelligence, export connectors, distributed storage, queue
workers, or production scale crawling.

## Durable Runtime And Scheduler Foundation Slice

The durable foundation slice moves the target runtime spine beyond process-local
state while still avoiding concrete infrastructure coupling:

- `veracrawl.contracts.durable`: `UnitOfWorkRecord`, `DurableCommandRecord`,
  `OutboxRecord`, `EventCursorRecord`, and `DurableFixtureManifest`.
- `veracrawl.contracts.scheduler`: `FrontierItem`, `QueueLease`, and
  `SchedulerRecoveryReport`.
- `veracrawl.contracts.recovery`: `DurableReplayRecoveryReport`.
- `veracrawl.ports.durable` and `veracrawl.ports.scheduler`: protocol boundaries
  for durable unit-of-work, command idempotency, event cursors, outbox, artifact
  index, frontier items, and queue leases.
- `veracrawl.runtime_support.durable_store`: deterministic durable fixture profile
  behind ports. This profile is intentionally not a production database or queue.
- `veracrawl.scheduler.runtime`: owner-service lease transitions for enqueue,
  lease, heartbeat, complete, release, expire, retry, and dead-letter behavior.
- `veracrawl.runtime_events.durable` and `veracrawl.review_replay.durable`:
  event cursor validation and durable replay recovery reports.
- `veracrawl.cli.durable`: deterministic fixture runner for durable success,
  duplicate command, event gap, pending outbox, stale lease, invalid lease, and
  missing artifact scenarios.

This slice proves durable semantics, scheduler ownership, idempotency, and recovery
without importing Postgres, Redis, Kafka, object storage, browser libraries, model
SDKs, or agent frameworks into core. Production adapters and migrations remain
future specs.

## Source Adapter And Fetch Runtime Slice

The source adapter slice adds deterministic source acquisition on top of the
durable scheduler foundation:

- `veracrawl.contracts.fetch`: `FetchAttempt`, `FetchResult`, `PageSnapshot`, and
  `DocumentArtifact` contracts for source acquisition outputs.
- `veracrawl.contracts.source_runtime`: `RateLimitDecision`,
  `SourceFailureReport`, `SourceAcquisitionReport`, and `SourceFixtureManifest`.
- `veracrawl.fetch.acquisition`: owner-service source acquisition flow from
  frontier lease to source adapter command, raw artifact ref, scheduler completion,
  and replay-visible acquisition report.
- `veracrawl.adapters.sources.deterministic`: deterministic fixture adapters for
  HTTP, sitemap, RSS, API-like, and document-source families. These adapters prove
  source-family semantics; they are not production network clients.
- `veracrawl.review_replay.source`: source acquisition replay ref validation for
  artifacts, policy, command records, event cursors, outbox, scheduler refs, and
  durable recovery refs.
- `veracrawl.cli.source`: `veracrawl-source run` fixture runner for source success
  and negative acquisition scenarios.

The core runtime depends on `SourceAdapterPort`, contracts, policy, scheduler,
durable support, and replay validation. It must not import concrete browser,
storage, queue, model SDK, or agent framework implementations. Concrete HTTP
clients, browser engines, storage engines, queue systems, model providers, and
agent frameworks must enter through adapters in future specs.

This slice proves generic source acquisition semantics for deterministic fixtures:
HTTP, sitemap, RSS, API-like, document-source, blocked source, rate-limited source,
adapter mismatch, malformed response, retry exhaustion, and missing raw artifact.
It does not prove production HTTP crawling, JavaScript browser rendering,
distributed persistence, graph/memory intelligence, export delivery, or production
scale readiness.

## Browser And Network Acquisition Runtime Slice

The browser/network acquisition slice moves acquisition from deterministic
payload fixtures to real local network observation while preserving adapter
boundaries:

- `veracrawl.contracts.network`: `NetworkRequest`, `NetworkResponse`,
  `RedirectHop`, `NetworkAcquisitionReport`, and `NetworkFixtureManifest`.
- `veracrawl.contracts.browser`: `BrowserSandboxPolicy` and
  `BrowserInteractionStep`.
- `veracrawl.ports.network` and `veracrawl.ports.browser`: protocol boundaries
  for concrete HTTP clients and browser observation engines.
- `veracrawl.fetch.network_acquisition`: owner-service policy and replay flow for
  HTTP request, response, redirect, size, timeout, egress, private-network,
  robots, rate, and acquisition reporting.
- `veracrawl.browser.observation`: browser sandbox policy gate and read-only
  observation reporting.
- `veracrawl.adapters.network.stdlib_http`: concrete standard-library HTTP
  adapter for deterministic local benchmark servers.
- `veracrawl.adapters.network.local_benchmark`: deterministic local benchmark
  server used by fixtures.
- `veracrawl.adapters.browser.deterministic`: deterministic browser observation
  adapter for DOM, screenshot, and network metadata refs.
- `veracrawl.review_replay.network_browser`: replay completeness validation for
  network and browser acquisition reports.
- `veracrawl.cli.network`: `veracrawl-network run` fixture runner.

This slice proves actual local HTTP acquisition, redirect metadata, egress and
private-network gates, robots/rate/size/timeout failure typing, browser sandbox
contracts, unsafe side-effect blocking, and replay-visible artifact refs. It does
not prove full JavaScript rendering, production browser fleet execution,
authenticated crawling, distributed persistence, graph/memory intelligence,
export delivery, or production scale readiness.

## Normalize And Extract Plane Slice

The normalize/extract slice turns raw acquisition output into replayable
processing artifacts without allowing extracted candidates to bypass evidence or
publication gates:

- `veracrawl.contracts.processing`: `NormalizationManifest`, `TextAnchor`,
  `AnchorMap`, `LinkProvenance`, `PageTypeClassification`, `SiteModel`,
  `ExtractionStrategy`, `ExtractionCandidate`, `NormalizedDocument`, and
  `NormalizeExtractReport`.
- `veracrawl.normalize.pipeline`: deterministic HTML-to-text normalization,
  manifest digest tracking, anchor generation, anchor map construction, link
  extraction with source anchors, page type classification, and site model
  recording.
- `veracrawl.extract.candidates`: deterministic extraction strategy and candidate
  creation that requires every candidate field to point to an anchor.
- `veracrawl.review_replay.processing`: replay completeness checks for raw
  artifact, source adapter result, normalized document, manifest, anchor map,
  site model, page type, link provenance, extraction strategy, candidate, command,
  event cursor, outbox, and policy refs.
- `veracrawl.cli.process`: `veracrawl-process run` fixture runner for process
  success and typed negative cases.

This slice proves replay-visible lineage from raw snapshot to normalized text,
anchors, discovered links, page classification, site model, strategy, and
candidate. It preserves the architectural rule that model-generated or
deterministically generated candidates are not published outputs. It does not
prove evidence packet construction, publication completion, graph or memory
intelligence, export delivery, distributed persistence, production browser
rendering, or production scale readiness.

## Evidence And Publication Spine Slice

The evidence/publication slice turns extraction candidates into evidence-backed
outputs only after explicit gates pass:

- `veracrawl.contracts.evidence`: `EvidenceCoverageResult`, `EvidencePacket`,
  `EvidenceAnchor`, `EvidencePacketManifest`, and
  `EvidencePublicationFixtureManifest`.
- `veracrawl.contracts.verification`: `VerificationDecision` and
  `ReviewDecision`.
- `veracrawl.contracts.publication`: `PublishedOutput`, `OutputManifest`, and
  `PublicationReport`.
- `veracrawl.evidence.coverage`: field evidence coverage from extraction
  candidate field anchors, with graph, memory, and agent reasoning refs preserved
  only as diagnostics.
- `veracrawl.verify.review`: deterministic verification and review decision
  records for fixture acceptance and conflict cases.
- `veracrawl.publish.gates`: publication gate evaluation, immutable output
  manifest construction, and direct candidate publication rejection.
- `veracrawl.review_replay.publication`: replay completeness validation for
  evidence, verification, review, publication, policy, privacy, command, event,
  outbox, artifact, output, and replay refs.
- `veracrawl.cli.evidence`: `veracrawl-evidence run` fixture runner.

This slice proves the candidate-not-output boundary with source-backed field
evidence, accepted verification/review decisions, publication policy, privacy
refs, and replay completeness. It does not prove graph intelligence, memory
intelligence, export delivery, distributed persistence, production browser
rendering, review UI, or production scale readiness.

## Basic Site Graph Spine Slice

The basic graph slice turns acquisition, normalization, and site-understanding
refs into replayable graph records while preserving the rule that graph signals
cannot replace source evidence:

- `veracrawl.contracts.graph`: `GraphNode`, `GraphEdge`,
  `GraphEdgeProvenance`, `GraphBuildManifest`, `ProjectionWatermark`,
  `GraphBuildReport`, and `GraphFixtureManifest`.
- `veracrawl.graph.build`: deterministic URL, hyperlink, canonical, redirect,
  page type, and page-structure graph build records.
- `veracrawl.review_replay.graph`: graph replay completeness validation for
  manifest, node, edge, provenance, watermark, policy, command, event, and outbox
  refs.
- `veracrawl.cli.graph`: `veracrawl-graph run` fixture runner.

This slice proves basic site graph construction, stable rebuild hashes,
deduplicated graph keys, edge provenance, projection watermarks, and
graph-as-evidence rejection. It does not prove entity graph, temporal knowledge
graph, graph store adapters, graph-driven frontier scheduling, memory, export,
distributed persistence, production browser rendering, or production scale graph
operations.

## Advanced Graph Projection Spine Slice

The advanced graph projection slice turns basic graph manifests and canonical
source/evidence refs into replayable derived projections while preserving the
rule that graph and memory cannot become publication source of truth:

- `veracrawl.contracts.graph`: `ProjectionSpec`, `ProjectionRebuildJob`,
  `ProjectionMismatchReport`, `GraphDeltaReport`, `GraphSignal`,
  `GraphQualityReport`, `TemporalGraphProjectionRecord`,
  `AdvancedGraphProjectionReport`, and `AdvancedGraphFixtureManifest`.
- `veracrawl.graph.projection`: deterministic projection rebuild, mismatch,
  graph signal, quality, delta, and temporal record construction.
- `veracrawl.review_replay.graph`: advanced graph projection replay completeness
  validation for projection, rebuild, delta, quality, signal, temporal,
  watermark, policy, command, event, and outbox refs.
- `veracrawl.cli.projection`: `veracrawl-projection run` fixture runner.

This slice proves projection specs, deterministic rebuild jobs, projection
mismatch reports, graph deltas, graph quality reports, graph signals,
frontier/review signal contracts, temporal graph records, projection watermarks,
and graph-signal-as-evidence rejection. It does not prove production graph store
adapters, concrete graph-driven scheduling, memory, export, distributed
persistence, production browser rendering, graph explorer UI, or production
scale graph operations.

## Memory Kernel Slice

The memory kernel slice turns verified operational lessons and evidence-backed
run context into replayable scoped memory records while preserving the rule that
memory cannot become publication source evidence:

- `veracrawl.contracts.memory`: `MemoryEvent`, `MemoryRetrievalTrace`,
  `CrossScopeMemoryTunnel`, `OperationalTemporalMemoryRecord`,
  `MemoryKernelReport`, and `MemoryFixtureManifest`.
- `veracrawl.memory.kernel`: deterministic memory write/retrieve,
  invalidation-exclusion, cross-scope tunnel, and memory-as-evidence failure
  records.
- `veracrawl.review_replay.memory`: memory replay completeness validation for
  memory event, retrieval, operational temporal, policy, command, event, and
  outbox refs.
- `veracrawl.cli.memory`: `veracrawl-memory run` fixture runner.

This slice proves scoped memory events, sanitized retrieval traces, invalidated
memory exclusion, cross-scope sanitized tunnel contracts, operational temporal
memory records, tainted-memory blocking, and memory-as-evidence rejection. It
does not prove production memory stores, vector/search retrieval, long-running
memory compaction, export delivery, distributed persistence, production browser
rendering, or production scale memory operations.

## Multi-Agent Repair Spine Slice

The multi-agent repair slice coordinates VeraCrawl-owned agent workflow records
without coupling core to any concrete agent framework:

- `veracrawl.contracts.agent`: `MultiAgentWorkflow`, `AgentHandoff`,
  `CoordinationDecision`, `DriftRepairSignal`, `MultiAgentRepairReport`, and
  `MultiAgentFixtureManifest`.
- `veracrawl.agents.orchestration`: deterministic workflow, handoff,
  arbitration, repair evidence, and boundary failure records.
- `veracrawl.review_replay.agents`: multi-agent replay completeness validation.
- `veracrawl.cli.agents`: `veracrawl-agent-workflow run` fixture runner.

This slice proves framework-neutral workflow state, explicit handoffs,
coordination decisions, owner-service command boundaries, before/after repair
evidence, rollback refs, and agent-reasoning-as-evidence rejection. It does not
prove concrete agent framework integration, model SDK integration, review UI,
export delivery, distributed persistence, production browser rendering, or
production scale agent operations.

## Target Port Matrix

Every concrete infrastructure dependency must be reached through a VeraCrawl-owned port.

| Port | Owner package | Input contracts | Output contracts | Idempotency and error semantics |
| --- | --- | --- | --- | --- |
| UnitOfWorkPort | `ports` / used by owner services | aggregate commands, expected versions | committed aggregate changes, outbox events | commit is atomic; version conflict returns rejected CommandResult |
| EventStorePort | `runtime_events` | CrawlRunEvent, EventTypeSpec | append result, stream cursor | append is idempotent by event ID and run sequence; gaps fail replay checks |
| MetadataRepositoryPort | owner service package | aggregate models | aggregate snapshots | writes require owner service and expected version |
| ArtifactStorePort | `ports` | artifact bytes/metadata | content-addressed refs, lifecycle refs | writes idempotent by content hash; partial writes produce orphan recovery task |
| QueuePort | `scheduler` / workers | queue item, shard key, lease request | lease token, heartbeat, ack/nack | leases expire; ack requires token; retry class controls delay/dead letter |
| SourceAdapterPort family | adapter packages | SourceAdapterSpec, adapter command, policy snapshot | SourceAdapterResult plus adapter-native output refs | adapter emits blocked result for policy denial; retries preserve attempt lineage |
| BrowserPort | `browser` | BrowserInteractionStep, sandbox policy | DOM/screenshot/network artifact refs | runtime/size/egress violations create failed step and blocked-source report |
| CredentialVaultPort | `control` / adapters | credential scope ref, PolicyDecision | ephemeral credential handle, CredentialUseAudit | raw secret is never returned to agents or persisted in prompts |
| ContextStorePort | `agents` | ContextRef list, redaction policy, taint policy | ContextBundle, ContextBundleTrace | forbidden, stale, tainted, or unauthorized refs are excluded with reasons |
| ModelProviderPort | `agents` | ModelRequest, sanitized context refs | ModelResponse, ModelCallTrace | provider errors are classified retryable/permanent; raw content retention follows policy |
| ToolGatewayPort | `agents` | CommandEnvelope, AgentToolSpec | CommandResult, ToolCallTrace | mutating tools require policy and owner service command handling |
| GraphStorePort | `graph` | GraphBuildManifest, graph nodes/edges/signals | projection ref, watermark, quality report | graph rebuild is deterministic from input refs or emits mismatch report |
| ProjectionStorePort | `projection` | ProjectionSpec, ProjectionRebuildJob, EventCursor refs | ProjectionWatermark, ProjectionMismatchReport | generic projections track scoped cursors, rebuild hashes, and stale/delete/redaction propagation |
| MemoryStorePort | `memory` | MemoryEvent, MemoryRetrievalTrace query | retrieved memory refs, exclusion refs | tainted/stale/invalidated memory is excluded by policy |
| ExportTargetPort | `export` | OutputManifest, ExportJob | ExportAttempt, ExportDeliveryReceipt | dispatch uses outbox and idempotency key; withdrawal reconciles external IDs |
| MetricsPort | `ops` | measurement event | metric sample ref | metric failures do not block canonical state commits |
| TracingPort | `ops` | trace span refs | trace IDs | trace IDs are copied into events for replay correlation |
| ClockPort | `ports` | none | timestamp | tests use deterministic clock |
| RandomnessPort | `ports` | entropy request | generated value | IDs use deterministic test implementation and collision checks |

## Canonical State And Projections

Canonical state:

- Postgres metadata for projects, sites, objectives, plans, jobs, runs, frontier items, tasks, decisions, review items, outputs, manifests, exports, and command results.
- Object artifacts for raw snapshots, screenshots, normalized documents, anchor maps, large evidence artifacts, export files, and replay bundles.
- Append-only event log for crawl run events, agent tool calls, policy decisions, state transitions, publication events, export events, memory events, graph rebuild markers, and recovery actions.

Projection state:

- search index
- vector index
- graph store
- temporal knowledge graph projection
- memory retrieval indexes
- warehouse/database export targets
- analytics and quality dashboards

Projection rules:

- generic projection infrastructure is owned by `projection`
- `graph` owns graph-specific nodes, edges, graph signals, graph build manifests, and temporal KG graph projections
- search, vector, memory index, export status, analytics, and dashboard projections use `projection` infrastructure through ports owned by their domain packages
- projections must have rebuild watermarks
- stale projections must be detectable
- deletes, redactions, tombstones, and retention changes must propagate
- projections cannot be source of truth for publication or replay

## Storage, Projection, Replay, And Migration Matrix

| Aggregate or artifact | Owner | Canonical store | Artifact store | Events | Projections | Watermark and migration behavior | Failure mode and acceptance test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Project/Site/Policy/Schema | control | Postgres | none | policy/schema events | search/admin views | migrations are versioned; policy snapshots immutable | version conflict and rollback tests |
| Objective/Plan/Job/Run | control | Postgres | plan/replay bundle refs | objective/plan/job/run events | run dashboard | backfill creates run plan snapshots from events | replay reconstructs approved plan |
| FrontierItem | scheduler | Postgres or queue metadata | none | frontier_transitioned | queue metrics, graph priority views | shard watermark per site/run | crash/resume and duplicate ack tests |
| FetchAttempt/FetchResult/PageSnapshot | fetch/browser | Postgres metadata | raw HTML, DOM, screenshot, network logs | fetch_attempted, snapshot_written | search/index candidates | orphan artifact recovery and tombstone propagation | partial fetch and orphan cleanup tests |
| NormalizedDocument/Manifest | normalize | Postgres metadata | normalized text, anchor maps | processing_transitioned | search/vector, evidence views | transformation version migration creates new manifest | anchor replay tests |
| ExtractionCandidate | extract | Postgres | large candidate payload refs | candidate_created | review queue, quality dashboard | schema migration links old/new fields | candidate/schema migration tests |
| EvidencePacket | evidence | Postgres | evidence bundle refs | evidence_built | evidence viewer | coverage map versioned | missing evidence fails publication test |
| VerificationDecision/Conflict | verify/review | Postgres | review notes refs | verification_decided, conflict_adjudicated | quality dashboard, temporal KG inputs | conflict records never overwritten | contradiction fixture test |
| PublishedOutput/OutputManifest | publish | Postgres | immutable output manifest | output_published, output_withdrawn | result API, export outbox | manifest versions append-only | withdrawal and supersession tests |
| GraphProjection | graph | projection metadata | graph artifact snapshots | graph projection events | graph store, graph explorer | projection watermark and rebuild hash | rebuild determinism test |
| MemoryEvent/Index | memory | Postgres/event log | sanitized memory summaries | memory_written | memory index/vector/search | stale/taint invalidation backfills indexes | poisoned-memory exclusion test |
| ExportJob/Receipt/Withdrawal | export | Postgres/outbox | export files/receipts | export_dispatched, export_delivered, export_withdrawal_attempted, export_withdrawal_completed, export_withdrawal_failed | delivery dashboard | destination cursor and receipt reconciliation | retry, duplicate, withdrawal propagation tests |
| ArtifactLifecycleState | artifact_lifecycle | Postgres | tombstone/redaction artifacts | artifact_lifecycle_changed, delete_propagated | all secondary indexes | retention migration emits cleanup tasks | delete/redaction/legal-hold propagation test |

Implementation specs must define concrete table names, indexes, migration files, projection rebuild jobs, and failure recovery commands before code is marked implementation-ready.

## Aggregate Ownership

The authoritative ownership matrix is `ServiceOwnershipSpec` and target ownership coverage in [07-data-contracts.md](07-data-contracts.md). This table summarizes the same target ownership model for implementation planning.

| Aggregate | Owner package/service | Mutation path |
| --- | --- | --- |
| Project, Site, Policy, Schema | `control` | command -> policy -> control aggregate -> event |
| PolicyDecision, ApprovalDecision | `control` | policy/review gate -> decision record -> event |
| CommandEnvelope, CommandResult | target aggregate owner | command -> owner service -> command result -> events |
| Objective, Plan, Job, Run | `control` | command -> approval/policy -> event |
| FrontierItem, QueueItem, ShardLease, RetryDeadLetterRecord | `scheduler` | command or queue lease -> expected version/lease token -> event |
| FetchAttempt, FetchResult | `fetch` / `browser` | adapter result -> artifact write -> event |
| PageSnapshot | `fetch` / `browser` | object artifact write -> metadata event |
| NormalizedDocument | `normalize` | processing task -> artifact write -> manifest event |
| ExtractionCandidate | `extract` | tool/worker result -> validator -> candidate event |
| EvidencePacket | `evidence` | candidate + anchors -> coverage validation -> event |
| VerificationDecision | `verify` | recommendation/review/policy -> decision event |
| PublishedOutput | `publish` | accepted decision + manifest -> output event |
| ArtifactLifecycleState | `artifact_lifecycle` | classify/redact/tombstone/delete/legal hold command -> lifecycle event -> projection cleanup |
| ProjectionSpec, ProjectionWatermark, ProjectionRebuildJob, ProjectionMismatchReport | `projection` | scoped event cursors/artifacts -> watermark/rebuild/mismatch event |
| GraphProjection, GraphBuildManifest, GraphNode, GraphEdge, GraphSignal | `graph` | graph build command -> graph records -> graph event |
| MemoryEvent, MemoryRetrievalTrace, CrossScopeMemoryTunnel, OperationalTemporalMemoryRecord | `memory` | approved memory write/retrieval/tunnel command -> evidence/taint policy -> event/index |
| Agent traces and multi-agent workflow records | `agents` | agent run/context/tool/model/workflow event -> trace record |
| ExportJob and receipt | `export` | output manifest -> outbox -> receipt event |
| ReviewDecision | `review_replay` | reviewer action -> event |
| FailureRecord, RecoveryAction, BackpressureSignal, AutoscalingDecision, DRRestoreReport | `ops` | failure/signal/recovery command -> ops event |

No package may directly mutate another package's aggregate tables.

## Agent Runtime Architecture

Agents are VeraCrawl roles executed by a framework-neutral runtime. External agent frameworks are optional adapters, not core architecture.

```text
AgentRunRequest
  -> ContextAssembler
  -> PromptInjectionGuard
  -> AgentRuntimePort
  -> ModelProviderAdapter or AgentFrameworkAdapter
  -> ToolRequestValidator
  -> PolicyGuard
  -> ToolGateway
  -> Owner service command
  -> CommandResult
  -> CrawlRunEvent / AgentActionTrace
```

Core interfaces:

```python
class AgentRuntimePort(Protocol):
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...

class ModelProviderPort(Protocol):
    def complete(self, request: ModelRequest) -> ModelResponse: ...

class ToolGatewayPort(Protocol):
    def execute(self, command: CommandEnvelope) -> CommandResult: ...

class ContextStorePort(Protocol):
    def read_context_refs(self, refs: list[ContextRef]) -> ContextBundle: ...
```

Agent runtime requirements:

- every agent input is referenced by stable context refs
- web-derived content is taint-labeled before prompt assembly
- raw credentials never enter prompt context
- raw secrets never enter logs, replay bundles, agent-visible state, or untrusted page text
- customer-approved credential presentation to an authorized origin is allowed only through audited scoped delivery modes and `CredentialUseAudit`
- tool requests must validate against `AgentToolSpec`
- mutating tools must pass policy checks
- owner services, not agents, apply durable mutations
- every agent run records model/provider refs, prompt template version, tool calls, command results, policy decisions, and output refs
- replay uses recorded refs and events, not framework-native state

Agent reasoning quality requirements:

- Planner must record ambiguities, assumptions, rejected alternatives, selected adapter rationale, evidence requirements, policy risks, and expected failure modes.
- Site Understanding must justify page type and template hypotheses against observed artifacts and uncertainty notes.
- Frontier recommendations must explain objective relevance, graph/memory inputs, freshness, uncertainty, and budget impact.
- Extractor must justify schema mapping and evidence anchor choices.
- Verifier must distinguish source evidence, prior verified output refs, graph signals, memory, and temporal KG context.
- Drift and repair plans must include before/after evidence, affected schemas, risk, and rollback path.
- Ops recommendations must include metric evidence, severity, blast radius, and operator action.

These reasoning outputs are not free-form hidden thoughts. They are structured summaries, assumptions, alternatives, rationale refs, and uncertainty notes stored in VeraCrawl trace contracts.

## Target Agent Roles

| Agent | Required target responsibility | Durable output |
| --- | --- | --- |
| Planner | objective interpretation, plan proposal, adapter choice, evidence requirements, risk notes | CrawlPlan, RunPlanSnapshot, AgentActionTrace |
| Site Understanding | page type inference, template clustering, site model, low-value zone detection | SiteModel, GraphBuildManifest, PageTypeClassification |
| Frontier | priority recommendations, retirement proposals, freshness/uncertainty routing | FrontierRecommendation, policy-checked transitions |
| Fetch Analysis | failure clustering, adapter change recommendations, blocked-source reporting | FailureRecord, RecoveryAction, review item |
| Extractor | candidate creation, schema mapping, anchor proposal, exploratory field proposals | ExtractionCandidate, ExtractionStrategy |
| Verifier | evidence evaluation, contradiction detection, accept/reject/review recommendation | VerificationRecommendation, ConflictRecord |
| Drift | template/selector/schema/content drift detection and repair proposal | DriftEvent, repair plan, review item |
| Memory | memory writes, retrieval indexing, freshness/invalidation, evidence backrefs | MemoryEvent, retrieval trace |
| Ops | health analysis, cost anomaly detection, pause/retry/review recommendations | QualityReport, alert, review item |

## Source Adapter Architecture

Adapters implement source-specific ports and produce canonical `SourceAdapterResult` records. Fetch-like adapters produce fetch artifacts; non-fetch adapters must not fake `FetchResult` or `PageSnapshot` semantics.

Target adapters:

- HTTP adapter
- sitemap adapter
- RSS/feed adapter
- browser snapshot adapter
- authorized session adapter
- API-like source adapter
- document/file adapter
- prior snapshot adapter
- manual seed adapter

Adapter requirements:

- declare supported source types and transformation schemas
- emit `SourceAdapterResult` records and natural output contracts for the adapter type
- enforce scope, egress, rate, budget, credential, and robots/terms policy decisions
- produce raw artifacts before normalization when the adapter actually yields source content; manual seed, prior snapshot, session-state, and other non-content adapters must instead emit adapter-native output refs
- provide idempotency keys and freshness semantics
- never bypass blocked or unavailable sources

Adapter result mapping:

| Adapter | Natural owner and result |
| --- | --- |
| HTTP | `fetch` -> FetchAttempt, FetchResult, PageSnapshot, SourceAdapterResult |
| Sitemap/RSS | `fetch` -> FetchAttempt, LinkProvenance, SourceAdapterResult |
| Browser snapshot | `browser` -> BrowserInteractionStep, PageSnapshot, SourceAdapterResult |
| Authorized session | `control` credential/session authority -> AuthorizedSessionSpec, CredentialUseAudit, SourceAdapterResult; browser/fetch adapters only reference session specs and audit refs |
| API source | `fetch` -> FetchResult or API payload artifact, SourceAdapterResult |
| Document source | `normalize` -> DocumentNormalizationArtifact, NormalizationManifest, SourceAdapterResult |
| File import | `artifact_lifecycle` + `normalize` -> ArtifactLifecycleState, DocumentNormalizationArtifact, SourceAdapterResult |
| Manual seed | `control` -> CrawlObjective/CrawlPlan seed refs, SourceAdapterResult |
| Prior snapshot | `control` + `artifact_lifecycle` -> PageSnapshot ref, RunPlanSnapshot ref, SourceAdapterResult |

## Browser Execution Design

Browser capability is target architecture, not a shortcut around safety.

Browser workers must:

- run in isolated contexts
- enforce egress allowlists and private-network denylists
- block file URLs unless explicitly authorized
- cap DOM, screenshot, network log, response, download, and artifact sizes
- keep raw secret material out of agent context, model prompts, logs, replay bundles, and untrusted page text
- present customer-approved credentials to authorized origins only through scoped headers, scoped cookies, request signing, or vault-brokered form fill with origin allowlist and `CredentialUseAudit`
- record browser minutes, interaction steps, artifact refs, and policy decisions
- classify every interaction by purpose and side-effect class before execution
- reject destructive, purchase/cart, account-changing, message-send, unknown, or out-of-scope interactions unless a future explicit approval policy permits a narrower audited mode
- emit blocked-source reports instead of bypass attempts

## Graph Architecture

Graph projections are derived from canonical artifacts and events.

Graph layers:

- URL graph
- hyperlink graph
- redirect/canonical graph
- page-structure graph
- template graph
- entity graph
- source/evidence graph
- task graph
- temporal knowledge graph projection

Graph requirements:

- every graph build has a manifest with input refs, projection version, watermark, and quality metrics
- graph signals can influence frontier and review routing
- graph signals cannot replace evidence for publication
- graph projections can be rebuilt from canonical events and artifacts
- graph deltas can trigger drift and review workflows

Temporal KG requirements:

- temporal KG projections derive only from `VerifiedFact`, accepted `PublishedOutput` records, and canonical events that record verification, publication, supersession, conflict, expiration, or invalidation.
- `EvidencePacket` refs may appear on temporal KG records only as lineage for an accepted verified output; unverified evidence packets cannot create temporal KG state by themselves.
- every projected relation records valid time and transaction time.
- entity identity records preserve alias evidence and confidence.
- conflicts, supersessions, expiration, and invalidation are represented explicitly.
- temporal KG reads are allowed for planning, contradiction detection, freshness analysis, and repair routing.
- temporal KG reads are forbidden as publication evidence unless separately represented by accepted evidence packets.
- rebuilds must reproduce projection records or emit a projection mismatch report.

## Memory Architecture

Memory is a planning and adaptation layer, not source evidence.

Memory stores:

- site behavior memory
- page type memory
- extraction strategy memory
- failure and repair memory
- task memory
- agent diary memory
- cross-site pattern tunnels

Memory requirements:

- memory writes are evented and scoped
- memory items include freshness, confidence, provenance, invalidation rules, and evidence refs where relevant
- memory items include trust level, taint labels, poisoning check refs, promotion policy refs, and allowed prompt-use mode
- retrieval is scoped by project, site, objective, schema, page type, run, and agent role
- retrieval excludes stale, invalidated, untrusted, or prompt-forbidden memory unless a policy explicitly allows sanitized summary use
- web-derived memory is sanitized before prompt use
- cross-site or cross-project memory uses `CrossScopeMemoryTunnel` with authorization, policy decisions, taint exclusion rules, and sanitized-only prompt use
- operational temporal memory is stored separately from publication temporal KG and cannot support publication evidence or authoritative entity identity
- memory-derived strategies must re-anchor to current or selected historical evidence
- stale or invalidated memory must be excluded from planning and agent context

## Evidence And Publication Design

Publication is strict even when exploration and extraction are aggressive.

Pipeline:

```text
raw artifact
  -> normalized document and anchor map
  -> extraction candidate
  -> evidence packet
  -> verification recommendation
  -> verification decision
  -> output manifest
  -> published output
  -> export receipt
```

Rules:

- extraction candidates are not published outputs
- evidence packets must include source, snapshot, normalized anchor, transformation manifest, extractor version, schema field refs, and freshness context
- accepted publication requires verification decision, publication policy, evidence coverage, and immutable output manifest
- conflicts create review or adjudication, not silent overwrite
- outputs can be withdrawn or superseded through events and delivery reconciliation

## Review, Replay, And Operations Design

Target operations surfaces:

- run dashboard
- frontier dashboard
- evidence viewer
- snapshot viewer
- graph explorer
- memory retrieval trace viewer
- review queue
- replay console
- export receipt and withdrawal viewer
- quality dashboard
- cost dashboard
- alerting and runbooks

Replay bundle must include:

- `ReplayBundleManifest`
- objective, plan, job, run config, policy snapshots, schema snapshots
- commands and command results
- crawl run events
- agent action traces
- tool call inputs and output refs
- `SourceAdapterResult` records, `source_adapter_result_recorded` events, fetch attempts where applicable, and adapter-native output refs
- normalization manifests
- candidates, evidence packets, verification decisions, review decisions, outputs, exports
- projection watermarks and memory refs used by agents

Replay uses `ReplayBundleManifest` as the contract for event cursors, schema versions, artifact hashes, trace refs, projection watermarks, redaction map, deterministic clock/random seed, missing-ref behavior, replay mode, and completeness result.

### Review Replay Ops Console Slice

The executable target slice materializes the data surface behind the review
queue, replay console, quality dashboard, recovery view, and DR restore view
before a production UI exists.

Required records:

- `ReviewItem` for operator-visible review queue state.
- `ReplayAuditView` for replay bundle, command, event cursor, artifact hash, projection watermark, redaction, and policy refs.
- `FailureRecord` for typed operational failure visibility.
- `RecoveryAction` for policy/review/approval-gated recovery decisions.
- `DRRestoreReport` for disaster recovery validation refs.
- `QualityReport` for quality and cost dashboard data.
- `OpsDashboardSnapshot` for projection-watermarked dashboard state.
- `OpsConsoleReport` for end-to-end completion and replay refs.

Rules:

- passing ops console reports require review, replay audit, quality, dashboard, DR restore, policy, command, event cursor, and outbox refs.
- side-effecting recovery actions require policy and approval refs.
- stale dashboard projections fail instead of being presented as fresh state.
- missing review evidence and unresolved failures create explicit failure records.
- this slice does not implement a production dashboard frontend, production
  observability backend, alerting system, export delivery, distributed
  persistence, production browser rendering, or production scale operations.

### Export Connectors Slice

The executable target export slice materializes destination-neutral delivery,
receipt, withdrawal, correction, and reconciliation records before concrete
destination adapters exist.

Required records:

- `ExportTargetSpec` for file, API, database, warehouse, object store, and queue targets.
- `ExportJob` and `ExportAttempt` for idempotent dispatch.
- `ExportDeliveryReceipt` for destination acknowledgement and external object ids.
- `ExportWithdrawalJob` and `ExportWithdrawalAttempt` for withdrawal propagation.
- `ExportCorrectionRecord` for supersession and replacement propagation.
- `ExportReconciliationReport` for replay-visible completion.

Rules:

- export core depends on `ExportTargetPort`, not concrete destination clients.
- dispatch success requires immutable output refs, idempotency key, policy refs, receipt, and destination object mappings.
- withdrawal requires object mappings; unsupported withdrawal creates reviewable `destination_unsupported`.
- correction requires withdrawal linkage and replacement export linkage.
- this slice does not implement concrete destination adapters, external writes,
  production export worker fleets, distributed persistence, production browser
  rendering, or production scale operations.

## Multi-agent Coordination Design

Target multi-agent behavior is coordinated through durable workflow contracts, not hidden framework state.

Required records:

- `MultiAgentWorkflow`: workflow graph, role sequence, loop budget, termination rules, escalation rules, and arbitration policy.
- `AgentHandoff`: explicit context transfer between agent roles with required output schema and policy refs.
- `CoordinationDecision`: arbitration for conflicting plans, recommendations, repair proposals, termination, and escalation.

Rules:

- every multi-agent workflow has a loop budget and termination rule before execution.
- conflicting recommendations must be resolved by `CoordinationDecision`, not implicit last-writer-wins behavior.
- repair workflows must preserve before/after evidence and rollback paths.
- workflow state is replayable through agent traces, handoffs, coordination decisions, commands, and events.
- owner services still apply durable mutations; multi-agent coordination only proposes, recommends, or escalates.

## Migration And Rebuild Execution Design

Target migrations and rebuilds are executable workflows, not notes.

Required records:

- `ProjectionWatermark` for projection freshness, lag, rebuild hash, and stale status.
- `ProjectionRebuildJob` for projection rebuild inputs, scoped event cursors, expected/actual hash, mismatch report, and status.
- `SchemaMigrationRun` for schema migration validation, backfill, and rollback.
- `EventMigrationRun` for event upcasters, replay validation, and rollback.
- `BackfillJob` for idempotent long-running migration, projection, artifact lifecycle, or export reconciliation work.

Rules:

- schema and event migrations must include rollback plans.
- projection rebuilds must either match deterministic hashes or emit `ProjectionMismatchReport`.
- delete and redaction migrations must propagate to every affected projection.
- stale projections must be visible to agents and cannot be used as fresh planning context without policy acknowledgement.

## Scale And Reliability Architecture

Target scale is implemented through deterministic sharding, leases, backpressure, projection watermarks, and recovery.

Queue topology:

- shard key: project ID + site ID + adapter type + priority band
- queues: frontier queue, processing queue, verification/review queue, export outbox, projection queue, recovery queue
- each queue item carries run ID, aggregate ID, idempotency key, expected version, lease token, retry class, priority, and deadline

Worker lease model:

- workers acquire leases with a visibility timeout and heartbeat interval
- ack/nack requires the current lease token
- expired leases return to the queue with retry metadata
- duplicate workers must be harmless because owner services enforce expected versions and idempotency keys

Fairness and backpressure:

- per-project and per-site concurrency limits are mandatory
- high-volume sites cannot consume all global worker capacity
- backpressure signals include queue lag, retry rate, browser minutes, token spend, object store growth, projection lag, export lag, and error rate
- budget-triggered pause emits policy and run events

Dead-letter and retry:

- retry classes: transient, rate_limited, policy_blocked, permanent_source_failure, adapter_bug, worker_crash, projection_mismatch, destination_rejected
- dead-letter items must create `FailureRecord` and optional `RecoveryAction`
- recovery actions must be replayable and reviewable

Autoscaling:

- scale fetch/browser/processing/export/projection workers from queue lag, lease wait time, CPU/memory, browser minutes, and destination throttling
- autoscaling changes must not change correctness; they only change throughput

Scale hardening executable slice:

- `QueueTopologySpec` records every target queue, deterministic shard key parts, per-project and per-site concurrency limits, fairness refs, and scheduler policy refs.
- `QueueItem` records queue family, shard key, aggregate refs, command ref, idempotency key, expected version ref, retry class, lease token, attempts, deadline, and transition status.
- `ShardLease` records worker identity, heartbeat, expiry, fencing token, policy refs, and lease status.
- `BackpressureSignal` and `AutoscalingDecision` record policy-visible throughput pressure and capacity changes; capacity-changing decisions require policy refs.
- `RetryDeadLetterRecord` records exhausted retry class, attempts, final reason, failure record, and recovery actions.
- `ScaleRecoveryReport` ties scale recovery to queue topology, queue items, leases, backpressure, autoscaling, dead letters, failure/recovery, DR restore, policy, command, event cursor, outbox, and replay refs.
- stale leases, unfair site starvation, autoscaling without policy, dead letters without failure records, and replay gaps are target-profile failures.
- the target spine remains queue/storage/cloud/metrics/tracing-neutral; concrete brokers, stores, telemetry backends, and cloud autoscalers are adapter work, not core coupling.

Disaster recovery:

- canonical Postgres, object artifacts, and event log are the recovery source of truth
- projections rebuild from canonical state and watermarks
- recovery work must be executed through `DRRestorePlan`, `DRRestoreRun`, and `DRRestoreReport`
- restore phases must declare restore point refs, ordered phase inputs/outputs, validation gates, rollback behavior, emitted events, and failure states
- recovery procedure restores metadata, validates artifact reachability, replays events, rebuilds projections, reconciles exports, validates unresolved refs, and emits `dr_restore_reported`

## Implementation Readiness Gates

Before a target capability is implemented, the spec must define:

- owner package/service
- contracts and IDs
- command and event types
- state machine
- storage and projection behavior
- policy decisions
- replay records
- test fixtures
- acceptance gates
- failure modes and recovery behavior

Before a capability is marked implemented, code must include:

- unit tests for domain rules
- contract tests for schemas and ports
- integration tests for adapters and persistence
- replay tests for event reconstruction
- policy and security tests
- observability hooks
- migration or projection rebuild path if state changes

## Target Implementation Order

Implementation order is for dependency management, not schedule reduction:

1. Contracts, IDs, policy, command/result, event log, state machines, artifact lifecycle.
2. Core runtime spine: control, scheduler, fetch, normalize, extract, evidence, verify, publish, replay.
3. Framework-neutral agent runtime and model provider adapter.
4. Browser, document, authorized session, and API-like source adapters.
5. Graph projections and graph-driven frontier/review workflows.
6. Memory kernel and scoped retrieval/invalidation.
7. Full multi-agent orchestration and repair loops.
8. Review/replay/ops console and quality dashboards.
9. Export connectors, receipts, withdrawal, and correction propagation.
10. Scale hardening, autoscaling, backpressure, chaos, DR, security, privacy, and compliance.

The product must not claim target architecture completion until all target capability profiles are verified and operational.
