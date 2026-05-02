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
