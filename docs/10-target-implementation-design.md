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

## Production Run-Control Persistence Wiring Slice

The production persistence wiring slice connects the row 039 run-control API to
production-shaped persistence surfaces while preserving adapter ownership:

- `veracrawl.contracts`: `ProductionPersistenceRuntimeReport` and
  `ProductionPersistenceFixtureManifest` prove canonical run-control state,
  transaction, command, idempotency, event cursor, outbox, artifact index, queue,
  lease, policy, failure/recovery, and replay refs.
- `veracrawl.ports.persistence`: canonical document save/load methods expose
  typed metadata persistence without leaking adapter internals into core.
- `veracrawl.control.run_control`: detailed run-control execution exposes the
  actual project, site scope, objective, plan, run, budget, policy snapshot,
  approval, policy decision, lifecycle, and report contracts created by the
  run-control path.
- `veracrawl.control.production_persistence`: owner-service wiring commits those
  contracts through port-shaped persistence, appends run-control events, creates
  persistence command/outbox/idempotency records, records queue lease and
  recovery operations, reopens the adapter, and validates replay-visible refs.
- `veracrawl.runtime_support.persistence_store` and JSON-document persistence
  adapters implement the canonical document methods behind ports.
- `veracrawl.cli.production_persistence`: `veracrawl-production-persistence`
  runs success, duplicate replay, queue recovery, and missing-ref fixtures.

This slice proves that canonical run-control state and persistence side effects
survive adapter reopen and replay without importing psycopg, Redis, boto3,
browser libraries, model SDKs, or agent frameworks into core. It does not prove
live HTTP acquisition, browser execution, managed cloud operations, deployment,
worker autoscaling, metrics/tracing backends, or disaster recovery.

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

## Live HTTP Acquisition Runtime Slice

The live HTTP acquisition runtime composes the row 039 control plane, row 040
production persistence wiring, and adapter-owned local HTTP acquisition into one
target-architecture proof:

- `veracrawl.contracts.network`: `LiveHttpAcquisitionReport` and
  `LiveHttpAcquisitionFixtureManifest` require run-control, production
  persistence, network/source acquisition, snapshot, source observation,
  artifact, content hash, canonical URL, policy, command/event/outbox, and
  replay refs before a live HTTP pass can be claimed.
- `veracrawl.fetch.live_http`: core runtime depends on contracts, production
  persistence ports, `NetworkSourceAdapterPort`, and existing network/source
  acquisition functions. It does not import concrete HTTP clients or read
  fixture source files directly.
- `veracrawl.cli.live_http`: fixture runner loads the standard-library HTTP
  adapter and local benchmark server at the CLI edge, writes reference
  persistence state, and validates success, redirect, unsafe network, malformed,
  replay, missing artifact, and direct-bypass fixtures.
- `TargetSourceObservationRecord`: passing HTTP acquisition creates a source
  observation that later normalization, evidence, graph, and replay specs can
  consume.

This slice proves authorized local HTTP acquisition through production
run-control/persistence and source adapter ports. It does not prove structured
sitemap/RSS/API/document adapters, browser rendering, credentialed sessions,
distributed worker fleets, external website benchmarking, or production network
operations.

## Structured Source Adapters Runtime Slice

The structured source adapters runtime proves non-browser structured source
families behind source adapter ports:

- `veracrawl.contracts.source_runtime`: `StructuredSourceAdapterRecord`,
  `StructuredSourceAdaptersRuntimeReport`, and
  `StructuredSourceAdaptersFixtureManifest` require sitemap, RSS/feed,
  API-like, document, and file-import source families before pass.
- `veracrawl.fetch.structured_source`: core aggregate runtime validates typed
  records and remains independent from concrete parsers, filesystems, network
  clients, browser libraries, model SDKs, and agent frameworks.
- `veracrawl.adapters.sources.structured_runtime`: adapter-owned fixture parser
  uses standard-library XML, JSON, document, and CSV parsing to materialize
  discovered URL refs, API payload refs, document artifact refs, file artifact
  refs, content hashes, evidence seed refs, and replay refs.
- `veracrawl.cli.structured_source`: `veracrawl-structured-source` dynamically
  loads the adapter module and runs success plus malformed/policy/unsupported
  and replay negative fixtures.

This slice proves structured source adapter semantics and lineage. It does not
normalize, extract, publish, render browser pages, handle credentials, run
external website benchmarks, or claim production worker fleet readiness.

## Browser Snapshot Runtime Slice

The browser snapshot runtime proves JavaScript-required page observation behind
browser ports while preserving upstream acquisition and replay boundaries:

- `veracrawl.contracts.browser`: `BrowserSnapshotRuntimeReport` and
  `BrowserSnapshotFixtureManifest` require live HTTP prerequisite refs,
  structured source prerequisite refs, sandbox policy refs, browser step refs,
  DOM/screenshot/network trace/console/timing artifact refs, browser budget
  refs, prompt-taint boundary refs, policy refs, command/event/outbox refs, and
  replay refs before pass.
- `veracrawl.browser.snapshot_runtime`: core aggregate runtime depends on
  browser contracts, `BrowserSourceAdapterPort`, and existing browser
  observation functions. It does not import concrete browser engines, concrete
  adapters, storage clients, model SDKs, or agent frameworks.
- `veracrawl.adapters.browser.deterministic`: fixture adapter materializes
  deterministic DOM, screenshot, network trace, console, and timing artifact
  refs without persisting browser-native state as canonical VeraCrawl state.
- `veracrawl.cli.browser_snapshot`: `veracrawl-browser-snapshot` dynamically
  loads the deterministic browser adapter and local benchmark server at the CLI
  edge, runs row 041 and row 042 prerequisite paths, and validates success plus
  egress, unsafe-interaction, budget, prompt-taint, missing-artifact, and replay
  negative fixtures.

This slice proves browser snapshot semantics and lineage. It does not solve
CAPTCHA, bypass paywalls, evade WAFs, automate unauthorized login walls, handle
credentials, normalize/extract rendered content, run an external browser fleet,
or claim final production benchmark readiness.

## Credentialed Session Runtime Slice

The credentialed session runtime proves authorized session use without allowing
secrets or adapter-native session state to become canonical VeraCrawl state:

- `veracrawl.contracts.security_privacy`:
  `CredentialedSessionRuntimeReport`,
  `CredentialedSessionFixtureManifest`, and existing `CredentialUseAudit`
  require live HTTP prerequisite refs, browser snapshot prerequisite refs,
  credential scope/origin/approval refs, redaction map refs, redacted session
  artifacts, redacted replay refs, policy refs, command/event/outbox refs, and
  replay refs before pass.
- `veracrawl.ports.session`: session capability is exposed through
  `CredentialedSessionAdapterPort`; core receives redacted session refs rather
  than raw credentials, cookies, or vault-native state.
- `veracrawl.fetch.credentialed_session`: core aggregate runtime builds
  credential audit refs, enforces scope/authorization/redaction gates, and does
  not import concrete session, browser, network, model, or agent adapters.
- `veracrawl.adapters.session.deterministic`: fixture adapter materializes
  deterministic redacted session state, redacted artifacts, and redacted replay
  refs without exposing raw secrets.
- `veracrawl.cli.credentialed_session`: `veracrawl-credentialed-session`
  dynamically loads deterministic adapters and runs row 041 and row 043
  prerequisite paths before validating success plus missing-authorization,
  out-of-scope, raw-secret-leak, unsafe-use, missing-audit,
  missing-redacted-replay, and replay-mismatch fixtures.

This slice proves credentialed session semantics and lineage. It does not steal
credentials, bypass login walls, automate unauthorized access, implement a real
external vault, normalize/extract authenticated content, or claim final
production benchmark readiness.

## Live Normalization And Site Understanding Runtime Slice

The live normalization runtime proves that acquired live artifacts can become
replayable processing and site-understanding refs without turning derived
context into source evidence:

- `veracrawl.contracts.processing`: `LiveNormalizationRuntimeReport` and
  `LiveNormalizationFixtureManifest` require live HTTP, structured source, and
  browser snapshot prerequisite refs plus normalized document, normalization
  manifest, source anchor, anchor map, link analysis, page type, site model,
  artifact, policy, command/event/outbox, derived-context, and replay refs
  before pass.
- `veracrawl.normalize.live_runtime`: core aggregate runtime receives acquired
  content and upstream refs through explicit inputs, calls the existing
  normalization pipeline, and does not import concrete network, browser, source,
  storage, model, or agent framework adapters.
- Linked pages record real `LinkProvenance` refs. Linkless detail or
  browser-shaped pages record deterministic no-link analysis refs instead of
  fabricated link provenance.
- `veracrawl.cli.live_normalization`: `veracrawl-live-normalization`
  dynamically loads local HTTP, structured source, and browser fixture adapters
  at the CLI edge, then validates listing, detail, browser, missing-upstream,
  empty-content, missing-anchor-map, missing-site-model, and replay-mismatch
  fixtures.

This slice proves normalization and site-understanding lineage over acquired
local live artifacts. It does not publish outputs, treat site models as source
evidence, implement schema extraction candidates, or claim final production
benchmark readiness.

## Schema Extraction Candidate Runtime Slice

The schema extraction runtime proves that live normalization results can produce
intermediate, schema-bound candidates without bypassing evidence or publication
gates:

- `veracrawl.contracts.processing`: `SchemaExtractionRuntimeReport` and
  `SchemaExtractionFixtureManifest` require live normalization refs, normalized
  document refs, source anchors, extraction strategy refs, extraction candidate
  refs, candidate field anchor refs, schema refs, schema validation refs,
  framework-neutral model/tool trace refs, confidence refs, policy refs,
  command/event/outbox refs, and replay refs before pass.
- `ExtractionCandidate` carries schema validation refs, model trace refs, tool
  trace refs, rejection refs, and replay refs while remaining an intermediate
  record.
- `veracrawl.extract.schema_runtime`: core aggregate runtime receives row 045
  normalization objects and refs through explicit inputs, reuses generic
  extraction helpers, enforces anchor/schema/trace/publication/replay gates, and
  does not import concrete source, browser, model, agent framework, storage, or
  site-specific scraper adapters.
- `veracrawl.cli.schema_extraction`: `veracrawl-schema-extraction` composes the
  local live HTTP, structured source, browser snapshot, and live normalization
  prerequisites at the CLI edge before validating declared schema, approved
  exploratory schema, browser-shaped content, drift repair, and negative
  candidate fixtures.

This slice proves candidate generation semantics and lineage. It does not build
evidence packets, verify candidates, publish outputs, call real model providers,
or claim final production benchmark readiness.

## Live Evidence And Verification Runtime Slice

The live evidence runtime proves that schema extraction candidates become
publishable candidates only after source-backed evidence and verification pass:

- `veracrawl.contracts.evidence`: `LiveEvidenceVerificationRuntimeReport` and
  `LiveEvidenceVerificationFixtureManifest` require schema extraction refs,
  candidate refs, normalized document refs, source anchor refs, evidence coverage
  refs, evidence packet refs, evidence anchor refs, evidence manifest refs,
  verification refs, review refs, freshness refs, policy/privacy refs,
  command/event/outbox refs, and replay refs before pass.
- `veracrawl.evidence.live_verification`: core aggregate runtime receives row
  046 candidates and row 045 source refs through explicit inputs, builds field
  evidence through the evidence owner helper, routes verification and review
  decisions through the verification owner helper, and does not import concrete
  source, browser, model, agent framework, storage, or site-specific scraper
  adapters.
- Graph signals, memory refs, and agent reasoning refs remain diagnostic only;
  they cannot satisfy source evidence and fail when used as the only evidence.
- `veracrawl.cli.live_evidence`: `veracrawl-live-evidence` composes local live
  HTTP, structured source, browser snapshot, live normalization, and schema
  extraction prerequisites at the CLI edge before validating evidence,
  verification, conflict, freshness, replay, and publication-bypass fixtures.

This slice proves source-backed evidence and verification semantics. It does
not publish outputs, export results, call real model providers, orchestrate
multi-agent repair, or claim final production benchmark readiness.

## Result Publication And Export Runtime Slice

The result publication runtime proves that verified evidence becomes published
and exportable only through publication, privacy, Result API, export, withdrawal,
correction, and replay gates:

- `veracrawl.contracts.publication`: `ResultApiSnapshot`,
  `ResultPublicationExportRuntimeReport`, and
  `ResultPublicationExportFixtureManifest` require live evidence refs,
  candidate/evidence/verification refs, publication report refs, published
  output refs, output manifest refs, Result API refs, export refs, delivery
  receipt refs, withdrawal/correction refs, destination mapping refs,
  policy/privacy refs, command/event/outbox refs, and replay refs before pass.
- `veracrawl.publish.result_runtime`: core aggregate runtime receives row 047
  evidence objects and refs through explicit inputs, reuses publication gates,
  materializes Result API snapshots, creates destination-neutral export records,
  and does not import concrete source, browser, model, agent framework, storage,
  or export connector adapters.
- `veracrawl.cli.result_publication`: `veracrawl-result-publication` composes
  local live HTTP, structured source, browser snapshot, live normalization,
  schema extraction, and live evidence prerequisites at the CLI edge before
  validating publication/export success and negative fixtures.

This slice proves publication/export lineage. It does not implement arbitrary
external warehouse/SaaS connectors, production worker orchestration, operator
console workflows, or final benchmark readiness.

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

## Target Output Type Coverage Gate Slice

The output coverage gate proves that every target output family can pass the same
evidence-backed publication boundary:

- `OutputTypeCoverageRecord` records per-output-type source evidence, evidence
  coverage, verification, publication, output manifest, privacy lifecycle,
  type-specific, command, event cursor, outbox, and replay refs.
- `OutputTypePublicationGateReport` can claim `pass` only when `record`,
  `table`, `document_metadata`, `document`, `file`, `dataset`, and `fact` are
  all covered.
- `veracrawl.publish.output_coverage` is deterministic and imports only
  VeraCrawl contracts.
- `veracrawl-output-coverage` runs success, no-runtime, aggregate negative, and
  source-specific derived-context negative fixtures without static dependencies
  on storage, queues, export targets, browsers, model SDKs, agent frameworks,
  HTTP clients, or site-specific scrapers.

Rules:

- candidate, graph, memory, agent reasoning, and temporal KG refs are diagnostic
  only and cannot satisfy source evidence requirements.
- candidate-as-evidence, graph-as-evidence, memory-as-evidence,
  agent-reasoning-as-evidence, and temporal-KG-as-evidence each have their own
  deterministic negative fixture and failure type.
- table outputs require row/cell evidence refs.
- file outputs require hash, MIME, and lifecycle refs.
- dataset outputs require item and item evidence refs.
- fact outputs require fact verification refs.
- this slice proves target output type publication readiness. It does not prove
  external export delivery, warehouse/database/object-store writes, production
  persistence, or production browser rendering.

## Target Website Pattern Coverage Gate Slice

The website pattern coverage gate proves that every target website pattern has a
deterministic benchmark fixture/oracle path before target completion can be
claimed:

- `WebsitePatternCoverageRecord` records per-pattern source adapter, source
  evidence, site model/page type, output/evidence oracle, policy, artifact,
  event, graph, safety, pattern-specific, command, event cursor, outbox, and
  replay refs.
- `WebsitePatternCoverageReport` can claim `pass` only when `static`,
  `sitemap_rss_feed`, `listing_detail`, `search`, `non_destructive_forms`,
  `javascript_pages`, `authenticated_sources`, `api_like_endpoints`,
  `documents`, `multi_language_pages`, `drifted_sites`, and `high_volume_sites`
  are all covered.
- `veracrawl.patterns.coverage` is deterministic and imports only VeraCrawl
  contracts.
- `veracrawl-website-patterns` runs success, no-runtime, single-site,
  scaffold-only, unsupported, missing-ref, unsafe-interaction, and replay
  fixtures without static dependencies on storage, queues, browsers, HTTP
  clients, model SDKs, agent frameworks, export targets, or site-specific
  scrapers.

Rules:

- single-site fixtures, fixed selector sets, and scaffold-only manifests cannot
  satisfy target website pattern coverage.
- browser, forms, authenticated, API, document, multilingual, drift, and
  high-volume patterns require explicit pattern-specific safety/evidence refs.
- this slice proves target website pattern benchmark readiness. It does not
  prove production browser fleets, production external websites, managed
  credential vaults, production parser farms, production queue scale, or
  production scale readiness.

## Target Product Acceptance Gate Slice

The product acceptance gate proves that target architecture is not only
technically covered but product-ready across buyer-value workflows:

- `ProductWorkflowReadinessRecord` records per-workflow buyer value, evidence,
  replay, operator-visible result, policy, command, event cursor, outbox,
  artifact, acceptance oracle, workflow-specific, capability state, status
  accuracy, export reconciliation, and recovery refs.
- `ProductAcceptanceGateReport` can claim `pass` only when multi-site
  onboarding, objective-to-plan approval, dynamic/auth/document/API crawl,
  evidence review, conflict resolution, drift repair, memory reuse,
  export/withdrawal, replay/audit, and operator recovery all have readiness refs
  and every minimum product gate is present.
- `veracrawl.product_acceptance.gate` is deterministic and imports only
  VeraCrawl contracts.
- `veracrawl-product-acceptance` runs success, no-runtime, missing-workflow,
  missing-gate, missing-ref, scaffold-only, contract-only, false-complete,
  degraded-operational, and missing-export-reconciliation fixtures with typed
  statuses.
- technical contract-only reports, mock UI screenshots, scaffold manifests,
  false completion labels, and degraded operational labels cannot satisfy
  product readiness.

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

## Multi-Agent Orchestration And Repair Runtime Slice

The multi-agent repair slice coordinates VeraCrawl-owned agent workflow records
without coupling core to any concrete agent framework and now gates repair on
row 049 real agent/model adapter runtime refs plus row 047 live evidence refs:

- `veracrawl.contracts.agent`: `MultiAgentWorkflow`, `AgentHandoff`,
  `CoordinationDecision`, `DriftRepairSignal`, `MultiAgentRepairReport`, and
  `MultiAgentFixtureManifest`.
- `veracrawl.agents.orchestration`: deterministic workflow, handoff,
  arbitration, crawl/extraction/drift repair evidence, controlled tool refs,
  owner command refs, review escalation, and boundary failure records.
- `veracrawl.review_replay.agents`: multi-agent replay completeness validation.
- `veracrawl.cli.agents`: `veracrawl-agent-workflow run` fixture runner.

This slice proves framework-neutral workflow state, explicit handoffs,
coordination decisions, controlled tools, owner-service command boundaries,
before/after repair evidence, rollback refs, row 049/047 dependency refs,
review escalation, replay bundle closure, and agent-reasoning-as-evidence
rejection. It does not prove external vendor account readiness, review UI,
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

### Model Provider Adapter Operational Gate Slice

The model provider gate proves that provider integrations map into VeraCrawl canonical model contracts before any provider runtime is trusted by agent workflows.

Required implementation:

- `ModelProviderAdapterExecutionRecord` records one provider family execution with runtime spec, `ModelRequest`, `ModelResponse`, `ModelCallTrace`, `ContextBundleTrace`, `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, command result, policy, observability, security/privacy, runtime/contract adapter, diagnostic provider state, and replay refs.
- `ModelProviderAdapterReport` aggregates all required provider families and can claim `pass` only when OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and FutureProvider all produce canonical execution refs through the same adapter contract.
- `ModelProviderAdapterFixtureManifest` defines success, no-runtime, and negative provider fixtures with expected operator status and failure type.
- `veracrawl.agents.model_provider_gate` is core-owned and imports only VeraCrawl contracts.
- `veracrawl.adapters.model_providers.contract` is adapter-owned and provides deterministic provider contract adapters without importing real SDKs.
- `veracrawl-model-providers` loads adapter modules dynamically so CLI fixture execution does not create static dependencies on OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint clients, local model runtime clients, browser libraries, storage clients, or queue clients.

Rules:

- missing live provider runtime/API credential refs return `needs_review`; contract-only refs cannot claim operational pass.
- raw prompts, raw responses, and raw credentials must never be persisted as canonical state.
- provider-native transcripts can be stored only as diagnostic refs and cannot satisfy canonical replay or completion requirements.
- missing context traces, security/privacy refs, observability refs, replay refs, unsafe tool suggestions, or unsupported provider names are deterministic failures.
- this slice proves provider-neutral adapter mapping and boundary enforcement. It does not prove production model provider accounts, vendor service availability, token billing, model selection optimization, review UI, export delivery, distributed persistence, production browser rendering, or production scale readiness.

### Agent Runtime Adapter Operational Gate Slice

The adapter gate proves that agent framework and model provider integrations map into VeraCrawl canonical contracts before any concrete framework is trusted by core.

Required implementation:

- `AgentAdapterExecutionRecord` records one framework family execution with runtime spec, `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, model call, tool call, context bundle, command result, policy, observability, security/privacy, runtime/contract adapter, diagnostic framework state, and replay refs.
- `AgentRuntimeAdapterReport` aggregates all required framework families and can claim `pass` only when OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and FutureFramework all produce canonical execution refs through the same adapter contract.
- `AgentRuntimeAdapterFixtureManifest` defines success, no-runtime, and negative adapter fixtures with expected operator status and failure type.
- `veracrawl.agents.adapter_gate` is core-owned and imports only VeraCrawl contracts.
- `veracrawl.adapters.agent_frameworks.contract` is adapter-owned and provides deterministic contract adapters without importing real SDKs.
- `veracrawl-agent-adapters` loads adapter modules dynamically so CLI fixture execution does not create static dependencies on OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, model SDKs, browser libraries, storage clients, or queue clients.

Rules:

- missing live SDK/runtime refs return `needs_review`; contract-only refs cannot claim operational pass.
- raw prompts and raw responses must never be persisted as canonical state.
- framework-native state can be stored only as diagnostic refs and cannot satisfy canonical replay or completion requirements.
- missing model traces, tool traces, security/privacy refs, observability refs, replay refs, or unsupported framework names are deterministic failures.
- this slice proves framework-neutral adapter mapping and boundary enforcement. It does not prove production model provider accounts, vendor service availability, review UI, export delivery, distributed persistence, production browser rendering, or production scale readiness.

### Real Agent And Model Adapter Runtime Slice

The real adapter runtime composes model provider and agent framework adapters
through ports so VeraCrawl planning, extraction, and repair can execute without
coupling core packages to any SDK or framework.

Required implementation:

- `AgentModelAdapterRuntimeReport` aggregates row 039 run-control refs, row 045
  live-normalization refs, row 046 schema-extraction refs, planner/extractor/
  repair agent run refs, provider/framework execution refs, model request/
  response/trace refs, agent request/result/action trace refs, context/tool
  trace refs, adapter runtime refs, policy/security/observability refs,
  command/event/outbox refs, and replay refs.
- `veracrawl.agents.real_adapter_runtime` is core-owned and imports only
  VeraCrawl contracts and ports. It receives `ModelRuntimeBinding` and
  `AgentRuntimeBinding` values whose ports are composed outside core.
- `veracrawl.adapters.model_providers.local_runtime` and
  `veracrawl.adapters.agent_frameworks.native_runtime` provide executable local
  adapters for deterministic validation.
- `veracrawl.adapters.model_providers.external_runtime` and
  `veracrawl.adapters.agent_frameworks.external_runtime` provide generic
  wrapper adapters for SDK/framework-specific modules without adding static
  dependencies to core.
- `veracrawl-agent-model-runtime` dynamically loads adapter modules at the CLI
  edge and records unavailable external SDKs or wrapper callables as
  `needs_review`.

Rules:

- a passing runtime must prove planner, extractor, and repair/drift turns.
- external OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic
  Kernel, OpenAI, Anthropic, Gemini, OpenAI-compatible, local, or future
  adapters must remain replaceable adapter modules.
- missing external SDKs, credentials, or wrapper callables are `needs_review`,
  not a fake pass.
- raw prompts, raw responses, raw credentials, provider-native transcripts, and
  framework-native state cannot become canonical VeraCrawl state.
- unsupported provider/framework names, missing model/tool/context traces,
  replay gaps, or core imports of adapter packages are deterministic failures.

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

### Source Coverage Adapter Operational Gate Slice

The source coverage gate proves that all target source adapter families map into
VeraCrawl canonical source contracts before any concrete browser, parser,
credential, API, or source runtime is trusted by core.

Required implementation:

- `SourceCoverageAdapterExecutionRecord` records one source adapter family with
  adapter type, natural result type, `SourceAdapterSpec`, `SourceAdapterResult`,
  natural output refs, adapter-specific fetch/browser/session/document/API refs,
  command result, policy, observability, security/privacy, runtime/contract
  adapter, diagnostic adapter state, and replay refs.
- `SourceCoverageAdapterReport` aggregates HTTP, sitemap, RSS/feed, browser
  snapshot, authorized session, API-like source, document source, file import,
  manual seed, and prior snapshot families and can claim `pass` only when all
  required canonical refs are present.
- `SourceCoverageAdapterFixtureManifest` defines success, no-runtime, and
  negative source coverage fixtures with expected operator status and failure
  type.
- `veracrawl.fetch.source_coverage_gate` is core-owned and imports only
  VeraCrawl contracts.
- `veracrawl.adapters.source_coverage.contract` is adapter-owned and provides
  deterministic source coverage descriptors without importing real browser,
  parser, vault, API, HTTP, storage, queue, model provider, or agent framework
  SDKs.
- `veracrawl-source-coverage` loads adapter modules dynamically so CLI fixture
  execution does not create static dependencies on concrete source runtimes.

Rules:

- missing live source, browser, parser, credential/session, or API runtime refs
  return `needs_review`; contract-only refs cannot claim operational pass.
- raw secrets must never be persisted as canonical state.
- adapter-native state can be stored only as diagnostic refs and cannot satisfy
  canonical replay or completion requirements.
- non-fetch adapters such as manual seed and prior snapshot must not fake
  `FetchAttempt` or `PageSnapshot` semantics.
- missing browser/session/document/API/replay refs, unsafe browser side effects,
  unsupported adapters, or source-specific hacks are deterministic failures.
- this slice proves broad target source mapping and boundary enforcement. It
  does not prove production JavaScript rendering, managed credential vaults,
  production parser farms, external API crawling, distributed persistence,
  review UI, export delivery, or production scale readiness.

### Dynamic Source Adapter Runtime Foundation Slice

The dynamic source runtime foundation proves that target source adapter families
can produce executable runtime records through ports/adapters without coupling
core to concrete browser, parser, credential vault, API, HTTP, storage, queue,
model provider, agent framework, or site-specific scraper packages.

Required implementation:

- `DynamicSourceRuntimeAdapterRecord` records one adapter runtime with adapter
  type, `SourceAdapterResult`, natural output refs, adapter-specific
  fetch/browser/session/document/API/file/seed/prior refs, command result,
  policy, observability, security/privacy, event cursor, outbox, runtime or
  contract adapter refs, diagnostic state refs, and replay bundle ref.
- `DynamicSourceRuntimeReport` aggregates HTTP, sitemap, RSS/feed, browser
  snapshot, authorized session, API-like source, document source, file import,
  manual seed, and prior snapshot runtime records and can claim `pass` only
  when every required target family is verified.
- `DynamicSourceRuntimeFixtureManifest` defines success, no-runtime, and
  negative fixtures with expected completion result and failure type.
- `veracrawl.fetch.dynamic_source_runtime` is core-owned and imports only
  VeraCrawl contracts.
- `veracrawl.adapters.sources.dynamic_runtime` is adapter-owned and provides
  deterministic/local runtime records for target source families.
- `veracrawl-source-runtime` dynamically loads adapter modules so fixture
  execution does not create static dependencies from core/CLI into concrete
  source runtime packages.

Rules:

- missing live source, browser, parser, credential/session, or API runtime refs
  return `needs_review`; contract-only descriptors cannot claim runtime pass.
- raw secrets must never be persisted as canonical state.
- adapter-native state can be stored only as diagnostic refs and cannot satisfy
  canonical replay or completion requirements.
- non-fetch adapters such as authorized session, file import, manual seed, and
  prior snapshot must emit native refs and must not fake `FetchAttempt` or
  `PageSnapshot` refs.
- missing browser/session/document/API/file/seed/prior/replay refs, unsafe
  browser side effects, unsupported adapters, or source-specific hacks are
  deterministic failures.
- this slice proves target source runtime shape and boundary enforcement. It
  does not claim production JavaScript rendering, managed credential vaults,
  production parser farms, external API crawling, export delivery, distributed
  storage, distributed queueing, or production scale readiness.

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

### Graph-Driven Frontier And Review Runtime Gate Slice

The graph frontier/review gate turns graph signals into replayable scheduler and
review decisions without making graph signals evidence or publication truth.

Required implementation:

- `GraphFrontierDecisionRecord` records priority, retry, retire, and expand
  decisions with `GraphSignal`, `FrontierItem`, source graph, explanation,
  policy, command, event cursor, outbox, and replay refs.
- `GraphReviewRouteDecisionRecord` records review routing decisions with
  `GraphSignal`, `ReviewItem`, source graph, explanation, policy, command,
  event cursor, outbox, and replay refs.
- `GraphFrontierReviewRuntimeReport` can claim `pass` only when frontier
  priority/retry/retire/expand and review route decisions are all present.
- `veracrawl.graph.frontier_review` is core-owned and imports only VeraCrawl
  contracts.
- `veracrawl-graph-frontier-review` runs success, no-runtime, and negative
  fixtures without static dependencies on graph stores, queue clients, storage
  clients, browser libraries, model SDKs, agent frameworks, or HTTP clients.

Rules:

- graph signals may influence frontier/review decisions only through typed
  decision records.
- graph signals must not satisfy `source_evidence_refs`, evidence coverage,
  verification decisions, publication pass, or output manifest evidence.
- missing live graph, scheduler, or review runtime refs return `needs_review`.
- graph-signal-as-evidence, missing source graph refs, missing explanations,
  unauthorized frontier mutations, missing review route refs, missing replay
  refs, and unsupported signals are deterministic failures.
- this slice proves graph-driven frontier/review runtime shape. It does not
  implement production graph stores, production queue backends, review UI,
  memory stores, export delivery, or production scale graph operations.

Temporal KG requirements:

- temporal KG projections derive only from `VerifiedFact`, accepted `PublishedOutput` records, and canonical events that record verification, publication, supersession, conflict, expiration, or invalidation.
- `EvidencePacket` refs may appear on temporal KG records only as lineage for an accepted verified output; unverified evidence packets cannot create temporal KG state by themselves.
- every projected relation records valid time and transaction time.
- entity identity records preserve alias evidence and confidence.
- conflicts, supersessions, expiration, and invalidation are represented explicitly.
- temporal KG reads are allowed for planning, contradiction detection, freshness analysis, and repair routing.
- temporal KG reads are forbidden as publication evidence unless separately represented by accepted evidence packets.
- rebuilds must reproduce projection records or emit a projection mismatch report.

### Temporal KG Identity Projection Gate Slice

The temporal KG gate turns verified facts, published outputs, canonical events,
evidence packets, and projection watermarks into replayable authoritative
identity and bitemporal projection records.

Required implementation:

- `TemporalKGEntityIdentity` records identity evidence, canonical source refs,
  valid-time refs, transaction-time refs, identity status, and explicit
  invalidation or supersession refs.
- `TemporalKGProjectionRecord` records bitemporal subject/predicate/value
  projections with evidence packet refs, canonical event refs, verified/published
  source refs, status, and projection watermark refs.
- `TemporalKGIdentityAdjudicationRecord` records false-merge and false-split
  repair decisions with conflict, authority, evidence, source event, policy,
  command, event cursor, outbox, and replay refs.
- `TemporalKGRuntimeReport` can claim `pass` only when identity, projection,
  canonical source, evidence, watermark, policy, command, event/outbox, and
  replay refs are complete.
- `veracrawl.graph.temporal_kg` is core-owned and imports only VeraCrawl
  contracts.
- `veracrawl-temporal-kg` runs success, no-runtime, false-merge, false-split,
  and negative fixtures without static dependencies on graph stores, queue
  clients, storage clients, browser libraries, model SDKs, agent frameworks, or
  HTTP clients.

Rules:

- provisional graph clustering cannot become authoritative temporal KG identity.
- temporal KG projections must not satisfy source evidence, verification,
  publication, or output manifest requirements.
- missing live temporal KG runtime refs return `needs_review`.
- projection-as-evidence, missing canonical source, missing bitemporal refs,
  false merge without adjudication, false split without supersession, and missing
  replay refs are deterministic failures.
- this slice proves temporal KG identity/projection semantics. It does not
  implement production graph stores, graph query APIs, graph explorer UI, vector
  search, export delivery, memory stores, or production scale graph operations.

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

Worker orchestration and scale runtime slice:

- `WorkerOrchestrationRuntimeReport` composes production persistence runtime refs, queue broker conformance refs, live HTTP acquisition refs, live normalization refs, live evidence verification refs, and `ScaleRecoveryReport` refs into one replayable worker-runtime acceptance record.
- worker pools cover frontier, fetch, browser, processing, verification, review, export, projection, and recovery without binding core to a concrete worker framework, queue client, browser engine, model SDK, or agent framework.
- passing worker orchestration requires worker pool refs, worker heartbeat refs, worker capacity refs, queue topology, queue item, shard lease, lease heartbeat, fencing token, visibility timeout, fairness, retry, dead-letter, failure, recovery, duplicate suppression, backpressure, autoscaling, pending outbox, event gap, policy, command, event cursor, outbox, and replay refs.
- `veracrawl.scale.worker_orchestration` is deterministic core runtime composition; adapter-owned brokers, stores, telemetry, browsers, and worker process managers remain outside core and must connect through ports/adapters.
- `veracrawl-worker-orchestration run` executes target-profile success and negative fixtures and writes a stable `run_report.json`.
- missing production persistence, missing queue broker conformance, unrecovered stale leases, missing lease heartbeats, hidden dead letters, duplicate pollution, backpressure/autoscaling without policy, and replay mismatch are typed `WorkerOrchestrationFailureType` failures.

Production persistence and queue runtime slice:

- `PersistenceAdapterSpec` records adapter capability refs for metadata store, event log, outbox, artifact index, and queue ports without binding core to a concrete database, queue broker, object store, or cloud SDK.
- `PersistenceTransactionRecord` records atomic unit-of-work boundaries across command, event, outbox, artifact, idempotency, and queue operation refs.
- `IdempotencyPersistenceRecord` persists command identity, idempotency key, command result, event, outbox, duplicate, and rejection refs so worker retries are side-effect safe after adapter reopen.
- `PersistentQueueOperationRecord` records enqueue, lease, heartbeat, ack, nack, and dead-letter transitions with lease/fencing, failure, and recovery refs.
- `PersistenceRuntimeReport` ties adapter, transaction, durable command, idempotency, event cursor, outbox, artifact index, queue operation, lease, policy, and replay refs into one replayable acceptance record.
- the standard-library reference filesystem store proves adapter contract semantics in fixtures; it is not the target's only production storage strategy.
- non-atomic commits, missing idempotency persistence, event cursor gaps, unrecovered pending outbox records, missing artifact index refs, and missing lease heartbeat/recovery refs are target-profile failures.

Concrete persistence adapter family slice:

- `veracrawl.persistence.adapter_conformance` is core-owned and imports only VeraCrawl contracts/ports. It executes adapter conformance for operational adapters without importing `veracrawl.adapters`, database drivers, queue clients, or cloud SDKs.
- `veracrawl.adapters.persistence.sqlite` is the executable standard-library SQLite adapter. It persists canonical documents for metadata, events, outbox, artifact index, queue operations, transactions, idempotency records, and migrations behind the same port-shaped API.
- `veracrawl.adapters.persistence.postgres_contract` is a contract descriptor only. It declares required Postgres-facing ports and returns `needs_review` in the conformance harness until an operational Postgres adapter is implemented and tested.
- `veracrawl.adapters.persistence.postgres` is the operational Postgres JSONB adapter. It uses optional `psycopg` only inside the adapter package, runs adapter-owned SQL migrations, and passes conformance only against an explicit live DSN.
- `PersistenceMigrationRecord` proves migration version transitions, rollback plans, validation event cursors, and failure refs.
- `PersistenceAdapterConformanceReport` proves adapter, transaction, migration, idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay refs for operational passes; contract-only descriptors must use `contract_only_refs` and cannot claim pass.
- `veracrawl-persistence-adapter` loads concrete adapter modules dynamically so CLI fixture execution does not create a core-to-adapter static dependency.
- missing adapter capability, missing idempotency persistence, event cursor gaps, outbox visibility gaps, and missing migration refs are adapter conformance failures.
- this slice does not implement external queue brokers, object storage, cloud deployment, metrics/tracing backends, managed Postgres operations, or production observability. Those remain future concrete adapter specs and gates.

Operational queue broker adapter slice:

- `veracrawl.scale.broker_conformance` is core-owned and imports only VeraCrawl contracts/ports. It executes broker conformance without importing `veracrawl.adapters`, Redis, Kafka, cloud queues, or broker SDKs.
- `QueueBrokerAdapterSpec` records queue names, broker capabilities, visibility timeout, fencing-token support, idempotency support, fairness refs, backpressure refs, and policy refs.
- `QueueBrokerOperationRecord` records enqueue, duplicate enqueue, lease, heartbeat, ack, nack, dead-letter, fencing token, visibility timeout, retry, failure/recovery, fairness, backpressure, and policy refs.
- `QueueBrokerConformanceReport` can claim `pass` only when a live operational broker produces topology, queue item, operation, lease, heartbeat, ack/nack, dead-letter, fencing, retry, fairness, backpressure, policy, and replay refs.
- `veracrawl.adapters.queue_brokers.redis` is the operational Redis/Valkey-style adapter. It uses optional `redis` only inside the adapter package and passes conformance only against an explicit live URL or Docker-backed gate.
- `redis-broker-runtime-unavailable` returns `needs_review` with `contract_only_refs`; no missing runtime or contract-only broker path may claim operational pass.
- `veracrawl-queue-broker` loads concrete broker modules dynamically so fixture execution does not create a core-to-adapter static dependency.
- missing fencing tokens, missing heartbeat refs, and missing dead-letter refs are queue broker conformance failures.
- this slice does not implement managed Redis operations, Kafka, cloud queues, production autoscaling, production worker fleets, deployment, metrics/tracing backends, or production observability. Those remain separate adapter and operations specs with their own live gates.

Operational object store adapter slice:

- `veracrawl.artifact_lifecycle.object_store_conformance` is core-owned and imports only VeraCrawl contracts/ports. It executes object store conformance without importing `veracrawl.adapters`, boto3, botocore, cloud SDKs, or object-store SDKs.
- `ObjectStoreAdapterSpec` records adapter kind, capability refs, bucket/namespace refs, content-addressing support, digest verification support, lifecycle support, retention refs, privacy refs, and policy refs.
- `ObjectStoreOperationRecord` records put, duplicate put, get, head, list, delete, artifact refs, object key refs, content digest refs, etag refs, read/head/list/delete refs, lifecycle refs, retention refs, privacy refs, policy refs, and failure/recovery refs.
- `ObjectStoreConformanceReport` can claim `pass` only when a live operational object store produces adapter, artifact, object operation, content digest, read, head, list, delete, lifecycle, retention, privacy, policy, and replay refs.
- `veracrawl.adapters.object_stores.s3` is the operational S3-compatible/MinIO adapter. It uses optional `boto3`/`botocore` only inside the adapter package and passes conformance only against an explicit live endpoint or Docker-backed MinIO gate.
- `s3-object-store-runtime-unavailable` returns `needs_review` with `contract_only_refs`; no missing endpoint/runtime or contract-only object store path may claim operational pass.
- `veracrawl-object-store` loads concrete object store modules dynamically so fixture execution does not create a core-to-adapter static dependency.
- missing content digest refs, missing read-after-write refs, and missing delete/lifecycle refs are object store conformance failures.
- this slice does not implement managed S3 operations, cloud IAM, CDN behavior, encryption key management, deployment, metrics/tracing backends, or production observability. Those remain separate adapter and operations specs with their own live gates.

Operational runtime infrastructure gate slice:

- `veracrawl.runtime_support.infrastructure_gate` is core-owned and imports only VeraCrawl contracts and core conformance result types. It aggregates results from operational persistence, queue broker, and object store conformance without importing concrete adapters or SDKs.
- `RuntimeInfrastructureSpec` records the required live Postgres persistence, Redis/Valkey queue broker, and S3-compatible object store adapter refs plus policy refs.
- `RuntimeInfrastructureReport` can claim `pass` only when persistence, queue broker, object store, adapter, command, idempotency, event cursor, outbox, queue operation, lease, heartbeat, ack, nack, dead-letter, artifact, object operation, digest, read, head, list, delete, lifecycle, policy, and replay refs are present in one integrated report.
- `veracrawl-infrastructure` loads concrete adapter modules dynamically so fixture execution does not create static core or CLI dependencies on `psycopg`, `redis`, `boto3`, `botocore`, cloud SDKs, model SDKs, browser libraries, or agent frameworks.
- `operational-infrastructure-runtime-unavailable` returns `needs_review` with contract-only refs; no single adapter pass, deterministic fixture store, or contract-only path may claim integrated runtime pass.
- missing persistence refs, missing queue refs, missing object refs, and missing replay refs are runtime infrastructure conformance failures.
- this slice does not implement managed cloud operations, deployment, production worker fleets, metrics/tracing backends, production observability, browser rendering, model SDK integration, or concrete agent framework integration. Those remain separate target gates.

Operational disaster recovery gate slice:

- `veracrawl.runtime_support.disaster_recovery` is core-owned and imports only VeraCrawl contracts plus the integrated runtime infrastructure report contract.
- `DRRestorePlan` records restore scope, restore point, backup manifest, metadata and artifact snapshot refs, ordered phase refs, validation gates, rollback behavior, policy refs, and approval refs.
- `DRRestoreRun` records ordered phase execution, phase validation outputs, emitted events, unresolved refs, failures, and terminal status.
- `DRRestoreReport` can claim `pass` only when metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, queue recovery, integrated runtime infrastructure, policy, command, event cursor, outbox, validation, failure/recovery, and replay refs are present and no unresolved refs or data loss exist.
- `veracrawl-dr` loads operational infrastructure through adapter-owned boundaries so fixture execution does not create static core dependencies on `psycopg`, `redis`, `boto3`, `botocore`, cloud SDKs, browser libraries, model SDKs, or agent frameworks.
- no-runtime DR returns `needs_review`; missing metadata, artifact, event replay, projection, export, unresolved refs, data loss, and unsafe recovery without approval are deterministic failures.
- this slice does not implement managed cloud backup, cross-region replication, deployment automation, production observability, alerting backends, on-call runbook automation, or production worker fleets. Those remain separate target gates.

Operational observability gate slice:

- `veracrawl.runtime_support.observability` is core-owned and imports only VeraCrawl contracts.
- `ObservabilitySignal` records owner service, severity, source, metric, trace, alert, policy, redaction, and replay refs for platform-visible signals.
- `MetricSample`, `TraceSpan`, `AlertRecord`, and `RunbookAction` record backend-neutral operational measurements, execution correlation, alert state, and operator/recovery action refs.
- `ObservabilityReport` can claim `pass` only when signal, metric, trace, alert, runbook, quality, cost, dashboard, projection watermark, failure/recovery, DR restore, policy, command, event cursor, outbox, redaction, collector handoff, telemetry backend, and replay refs are present.
- `veracrawl-observability` runs success, no-runtime, data-surface-only, and negative observability fixtures without static dependencies on Prometheus, OpenTelemetry, Grafana, cloud monitoring SDKs, browser libraries, model SDKs, or agent frameworks.
- no-runtime and ops-console-only observability return `needs_review`; missing metrics, traces, alerts, runbooks, dashboard watermarks, DR refs, redaction refs, replay refs, secret leakage, and unsafe runbook actions without approval are deterministic failures.
- this slice does not implement managed telemetry storage, OpenTelemetry collector deployment, Grafana dashboards, cloud monitoring accounts, paging integrations, on-call automation, deployment automation, production worker fleets, browser rendering, model SDK integration, or concrete agent framework integration. Those remain separate target gates.

Ops replay and observability runtime slice:

- `OpsReplayObservabilityRuntimeReport` composes row 048 result publication/export refs, row 052 worker orchestration refs, `OpsConsoleReport`, and `ObservabilityReport` into one operator-visible acceptance aggregate.
- `veracrawl.ops.replay_observability_runtime` is deterministic core runtime composition; it imports only VeraCrawl contracts and core runtimes, while UI frameworks, telemetry backends, storage clients, queue clients, browser engines, model SDKs, agent frameworks, and site-specific scraper code remain outside core.
- passing reports require run-control action refs, review item refs, evidence review refs, replay audit refs, graph/debug refs, export/withdrawal status refs, failure/recovery refs, DR restore refs, quality refs, dashboard refs, alert/runbook refs, cost/signal/metric/trace refs, policy refs, command/event/outbox refs, redaction refs, and replay bundle refs.
- `veracrawl-ops-runtime run` executes target-profile review/replay, incident recovery, and cost/alert success fixtures plus missing dependency and unsafe-operator negative fixtures, then writes a stable `run_report.json`.
- missing result publication, missing worker orchestration, missing ops console, missing observability, stale dashboard, unresolved recovery, unsafe operator action, and replay mismatch are typed `OpsReplayObservabilityFailureType` failures.
- this slice does not implement a production dashboard frontend, managed telemetry storage, paging integrations, production deployment automation, cloud autoscaling control, or concrete worker fleet management; it proves the canonical operator runtime contract is wired and replayable.

Production benchmark release gate slice:

- `ProductionBenchmarkReleaseReport` composes target runtime, source coverage, product acceptance, security/privacy, result publication/export, worker orchestration, and ops replay/observability reports into one final release decision.
- `veracrawl.release.benchmark_gate` is deterministic core runtime composition and imports only VeraCrawl contracts plus existing core runtimes; concrete UI, telemetry, storage, queue, browser, model, agent framework, cloud, and site-specific scraper implementations remain outside core.
- passing reports require authorized benchmark manifest/corpus refs, scenario refs, source, processing, evidence, verification, publication, export, replay, ops, scale, safety, policy, command/event/outbox, artifact, redaction, benchmark run, SLO metric, release decision, and audit refs.
- `veracrawl-release-gate run` executes target-profile success and negative release fixtures and writes a stable `run_report.json`.
- missing target runtime, missing source coverage, missing product acceptance, missing security/privacy, missing publication, missing worker orchestration, missing ops runtime, SLO violation, release blocker, false-ready status, and replay mismatch are typed `ProductionBenchmarkReleaseFailureType` failures.
- this slice does not implement managed deployment, production UI, external benchmark services, cloud autoscaling control, paging integrations, or unauthorized public crawling; it proves the canonical target release contract is wired and replayable.

Security/privacy lifecycle gate slice:

- `veracrawl.runtime_support.security_privacy` is core-owned and imports only VeraCrawl contracts.
- `SecurityPolicyCheck`, `CredentialUseAudit`, `PromptTaintBoundary`, `ArtifactLifecycleAction`, and `ProjectionCleanupRecord` are the executable contract spine for egress/private-network denial, credential isolation, prompt-taint boundaries, artifact lifecycle actions, and projection cleanup.
- `SecurityPrivacyReport` can claim `pass` only when security policy checks, credential audit refs, prompt taint boundary refs, artifact lifecycle actions, projection cleanup, redacted replay, observability, policy, command, event cursor, outbox, failure/recovery, redaction, and replay refs are present and leakage count is 0.
- `veracrawl-security-privacy` runs success, policy-only, and negative security/privacy fixtures without static dependencies on browser libraries, model SDKs, agent frameworks, cloud SDKs, telemetry SDKs, vault SDKs, or security vendor SDKs.
- policy-only security/privacy returns `needs_review`; unsafe network access, prompt-injection/tool misuse, credential leakage, missing lifecycle propagation, legal-hold delete, missing projection cleanup, missing redacted replay, and missing observability refs are deterministic failures.
- this slice does not implement CAPTCHA solving, paywall bypass, login wall circumvention, WAF evasion, stealth automation, credential theft, raw secret form-fill bypass, production browser rendering, managed DLP, external SIEM/SOAR integrations, or production compliance workflows. Those are outside VeraCrawl's authorized crawler boundary or require separate approved adapter specs.

Target crawl runtime slice:

- production run-control fixtures add `ProductionProject`,
  `ProductionSiteScope`, `RunBudget`, `RunPolicySnapshot`,
  `RunApprovalRecord`, `RunLifecycleRecord`,
  `ProductionRunControlReport`, and `ProductionRunControlFixtureManifest`.
  `veracrawl-run-control` proves the control plane can create, approve, start,
  pause, resume, cancel, complete, block, and replay runs through canonical
  commands/events before live source acquisition is connected.
- production run-control completion requires project, site scope, objective,
  plan, approval, budget, policy snapshot, command result, event, lifecycle,
  policy, and replay refs. Policy denial, missing approval, missing budget,
  invalid lifecycle transitions, and missing replay refs fail deterministically.
- `veracrawl.target_runtime.runner` is core-owned and imports only VeraCrawl contracts plus standard library helpers. It composes target runtime fixture results from objective, plan, pattern, AI, evidence, graph, export, privacy, and replay refs without importing concrete adapters or SDKs.
- `TargetCrawlPatternRecord` is the per-pattern proof surface for frontier, source observation, source adapter, extraction, accepted output, evidence, verification, graph, policy, command, event cursor, outbox, artifact, replay, and operator-visible refs.
- `TargetAIRecommendationRecord` records framework-neutral planning and repair recommendations. It blocks framework-native canonical state and requires policy/tool/trace refs for accepted recommendations.
- `TargetRuntimeReport` can claim `complete` only when at least seven website patterns are covered in one run and all output, evidence, graph, export, policy, command/event/outbox, artifact, AI, privacy, and replay refs are present.
- `veracrawl-target-runtime` executes success, drift-repair, needs-review, policy-denied, prompt-injection, missing-evidence, replay-mismatch, partial-export, and false-complete fixtures and writes `run_report.json`.
- source-backed target runtime fixtures add `TargetSourceCorpusManifest`,
  `TargetSourceCorpusEntry`, and `TargetSourceObservationRecord` contracts. The
  runner reads local HTML, XML, JSON, and text source files declared by the
  fixture, computes content-hash refs, derives field/evidence/graph/export/replay
  refs from generic descriptors, records framework-neutral repair recommendations
  for drift aliases, and rejects policy-denied, prompt-tainted, missing-evidence,
  replay-mismatched, and partial-export source corpora.
- source-backed execution remains generic runtime infrastructure. It must not
  contain site-specific scraper modules, concrete agent framework imports, model
  SDK imports, browser runtime imports, HTTP client imports, storage clients, or
  export destination clients in core.
- adapter-backed target runtime fixtures add `TargetAdapterBackedSourceEntry`,
  `TargetAdapterBackedSourceManifest`, and `TargetAdapterBackedSourceRecord`.
  `veracrawl-target-runtime` may load deterministic local adapter materialization
  from adapter-owned modules, but `veracrawl.target_runtime.runner` receives only
  canonical records and does not import concrete adapters.
- adapter-backed completion requires source adapter result refs, adapter output
  refs, adapter-backed source refs, source observations, content hashes, evidence,
  graph, export, policy, command/event/outbox, privacy, and replay refs. Missing
  adapter result refs, adapter output mismatch, policy-denied adapter output,
  replay mismatch, and direct source bypass fail or block deterministically.
- processing/evidence target runtime fixtures add `TargetProcessingEvidenceEntry`,
  `TargetProcessingEvidenceManifest`, and `TargetProcessingEvidenceRecord`.
  Adapter-owned materialization may build deterministic processing/evidence
  records, but the core runner receives only canonical records and does not
  import processing adapters, parser implementations, agent frameworks, or model
  SDKs.
- processing/evidence completion requires normalized document refs, extraction
  candidate refs, candidate anchors, evidence packet refs, evidence anchor refs,
  publication report refs, source observations, adapter output refs, policy refs,
  and replay refs. Missing normalization, missing candidate anchors, missing
  evidence packets, graph-only derived context used as evidence, publication
  bypass, or mismatched adapter/source lineage fail deterministically.
- this slice is an executable target architecture runtime path over deterministic fixtures. It is not a claim that live Internet crawling, production browser fleets, production credential vaults, concrete agent frameworks, managed model providers, production export destinations, or production worker fleets are operational.

Graph and memory production runtime:

- `veracrawl.contracts.graph_memory` owns
  `GraphMemoryProductionRuntimeReport` and
  `GraphMemoryProductionFixtureManifest`; graph and memory owner-service
  contracts remain authoritative for their own lower-level records.
- `veracrawl.graph_memory.runtime` composes row 045 live normalization refs, row
  047 live evidence refs, row 050 multi-agent repair refs, advanced graph
  projection refs, graph frontier/review refs, temporal KG refs, and memory
  kernel refs into one replayable aggregate.
- `veracrawl.cli.graph_memory_runtime` exposes
  `veracrawl-graph-memory-runtime run` for deterministic success and negative
  fixtures. The CLI validates target profile, expected status, typed failure,
  and writes `run_report.json`.
- passing graph/memory production requires URL, redirect, canonical,
  page-structure, entity, task, temporal graph refs, graph signal refs, site,
  task, repair, and run-diary memory refs, retrieval trace refs, freshness,
  invalidation/exclusion refs, frontier and repair explanations, source
  evidence, verification, policy, command/event/outbox, and replay refs.
- graph, temporal KG, memory, and agent reasoning influence planning and repair
  only. They cannot satisfy source evidence, verification, publication, or
  output manifest requirements.
- missing dependencies, graph-as-evidence, memory-as-evidence, stale memory,
  missing invalidation, missing frontier/repair explanation, and replay mismatch
  fail deterministically with `GraphMemoryProductionFailureType`.
- the runtime imports only VeraCrawl contracts and core deterministic runtime
  modules. It does not import graph stores, vector stores, concrete queues,
  storage clients, browser engines, model SDKs, agent frameworks, or
  site-specific scraper code.

Real-world benchmark corpus gate:

- `veracrawl.contracts.real_world_benchmark` owns
  `RealWorldBenchmarkCorpusManifest`, `RealWorldBenchmarkSiteSpec`,
  `RealWorldBenchmarkSiteObservation`, and `RealWorldBenchmarkRunReport`.
- `veracrawl.benchmarks.real_world` composes manifest-declared public site specs
  with existing live HTTP acquisition. It accepts injected robots fetchers and
  network adapter factories so tests can stay deterministic while the CLI can
  run a real external corpus.
- `veracrawl.cli.real_benchmark` exposes `veracrawl-real-benchmark run` for
  public corpus execution. The CLI performs same-origin robots preflight,
  constructs the stdlib HTTP adapter, writes `run_report.json`,
  `site_observations.json`, `summary.json`, and state files under the selected
  output directory.
- passing real-world benchmark reports require origin allowlist refs, robots
  policy refs, live HTTP report refs, network response refs, source observation
  refs, artifact/content hash/canonical URL refs, observation refs,
  command/event/outbox refs, and replay refs.
- private-network targets, off-allowlist origins, robots denial, live HTTP
  failure, observation mismatch, missing evidence refs, and replay mismatch fail
  with `RealWorldBenchmarkFailureType`.
- the runtime does not import concrete HTTP adapters, browser engines, model
  SDKs, agent frameworks, credential systems, export targets, or site-specific
  scraper modules into core.

Real-world AI agent benchmark gate:

- `veracrawl.contracts.real_world_ai_agent` owns
  `RealWorldAIAgentDecisionTrace`, `RealWorldAIAgentExtractionCandidate`,
  `RealWorldAIAgentBenchmarkRunReport`, and
  `RealWorldAIAgentBenchmarkManifest`.
- `veracrawl.benchmarks.real_world_ai_agent` composes a passing row 055 public
  corpus result with `ModelProviderPort` and `AgentRuntimePort`. Core receives
  adapter bindings through ports and never imports concrete model SDKs or agent
  frameworks.
- `veracrawl.cli.real_ai_benchmark` exposes `veracrawl-real-ai-benchmark run`.
  The CLI runs the referenced public corpus, dynamically loads either the
  default local model provider or the OpenAI Responses API model provider behind
  `ModelProviderPort`, dynamically loads the VeraCrawl native agent adapter, and
  writes aggregate reports, decision traces, candidates, model/agent/tool/context
  traces, and summary JSON under the selected output directory.
- `veracrawl.adapters.model_providers.openai_responses` calls the OpenAI
  Responses API through Python standard-library HTTP, not the OpenAI SDK. It
  records provider response ids and token usage in framework-neutral
  `ModelResponse` and `ModelCallTrace` refs without persisting raw prompt or raw
  response text as source evidence.
- every passing public site observation requires four AI decision types: crawl
  planning, site understanding, extraction candidate generation, and
  verification/repair. Each decision has model request/response, model call
  trace, agent run request/result, agent action trace, controlled tool trace,
  context bundle trace, policy, command/event/outbox, and replay refs.
- extraction candidates are source-bound. Candidate field anchors must point to
  source anchor refs backed by public crawl artifacts and content hashes. Model
  or agent output can propose a candidate but cannot become source evidence.
- direct publication refs are rejected unless evidence coverage, evidence
  packet, evidence anchor, verification, review, and publication gate refs are
  present. This benchmark records gate readiness, not published real-site
  outputs.
- missing AI traces, missing source anchors, LLM output as evidence, publication
  bypass, framework-native canonical state, core import coupling, adapter
  unavailability, and replay gaps fail with
  `RealWorldAIAgentBenchmarkFailureType`.

Expanded real-world public quality corpus gate:

- `veracrawl.contracts.real_world_quality` owns
  `RealWorldQualityCorpusManifest`, `RealWorldQualityTargetSpec`,
  `RealWorldQualitySiteObservation`, `RealWorldQualityPatternCoverageRecord`,
  and `RealWorldQualityCorpusReport`.
- `veracrawl.benchmarks.real_world_quality` composes row 055
  `run_real_world_benchmark_corpus` instead of adding another HTTP path. Passing
  quality coverage counts only row 055 passing site observations.
- `veracrawl.cli.real_quality_corpus` exposes
  `veracrawl-real-quality-corpus run`, dynamically reusing the row 055 CLI
  adapter factory and robots fetcher at the CLI edge while keeping core free of
  concrete network clients, browser engines, model SDKs, and agent frameworks.
- passing quality reports require at least 40 passing targets, 15 passing
  origins, and 10 passing pattern families plus policy refs, artifacts, content
  hashes, canonical URL refs, command/event/outbox refs, and replay refs.
- policy-denied, network-unavailable, drifted, missing-evidence, and
  missing-replay targets are visible diagnostics and do not count as passing
  quality coverage.
- this gate proves expanded corpus and pattern coverage only. JavaScript/browser
  quality, multi-page deep crawl quality, field-level oracles, precision/recall,
  repair success, and cost/latency/stability release are handled by later
  quality gates 059-064.

JavaScript browser quality benchmark:

- `veracrawl.contracts.browser_quality` owns
  `BrowserQualityCorpusManifest`, `BrowserQualityTargetSpec`,
  `BrowserQualityObservation`, `BrowserQualityDeltaRecord`, and
  `BrowserQualityReport`.
- `veracrawl.benchmarks.browser_quality` compares HTTP-only evidence with
  browser-rendered evidence for each manifest target. Passing observations
  require browser-only recovered oracle fragments, DOM/screenshot/network/
  console/timing artifacts, rendered content hashes, source anchors, browser
  budget refs, prompt-taint boundary refs, command/event/outbox refs, and replay
  refs.
- `veracrawl.adapters.browser.playwright` is the optional live browser adapter.
  It is dynamically loaded by `veracrawl.cli.browser_quality`; core benchmark
  runtime and contracts do not import Playwright or persist browser-native
  state.
- unsafe action, prompt-taint bypass, egress/policy denial, missing
  artifacts/anchors, budget exhaustion, replay mismatch, adapter unavailability,
  and insufficient browser-required target coverage fail with
  `BrowserQualityFailureType`.
- this gate proves JS/browser rendering quality for declared targets only.
  Credentialed browsing, CAPTCHA solving, stealth automation, field-level
  oracles, precision/recall, repair success, and cost/latency/stability release
  remain separate specs.

Multi-page deep crawl frontier benchmark:

- `veracrawl.contracts.deep_crawl` owns `DeepCrawlQualityManifest`,
  `DeepCrawlSiteSpec`, `DeepCrawlPageSpec`, `FrontierDecisionTrace`,
  `DeepCrawlPageObservation`, `DeepCrawlStopReasonRecord`, and
  `DeepCrawlQualityReport`.
- `veracrawl.benchmarks.deep_crawl` executes manifest-declared bounded site
  graphs through general frontier expansion, pagination/detail coverage,
  sitemap/feed links, canonicalization, duplicate suppression, off-origin and
  private-network skips, robots skips, depth/page/rate budgets, and replayable
  stop reasons.
- AI/agent/graph/memory influence is represented only as VeraCrawl model call,
  agent action, tool call, context bundle, graph, and memory refs on frontier
  priority decisions. Those refs can explain priority but cannot satisfy page
  source evidence.
- `veracrawl.cli.deep_crawl` exposes `veracrawl-deep-crawl-benchmark run`.
  Passing reports require at least 5 sites and 50 required pages plus source
  anchors, artifacts, content hashes, link provenance, canonical refs, duplicate
  suppression refs, graph refs, policy refs, command/event/outbox refs, and
  replay refs.
- duplicate loops, off-origin pollution, robots-denied bypass, budget
  exhaustion, infinite pagination, replay mismatch, missing frontier decisions,
  missing graph refs, missing replay refs, missing stop reasons, and
  insufficient coverage fail with `DeepCrawlFailureType`.
- this gate proves bounded deep crawl frontier quality only. Field-level oracle
  extraction, precision/recall, repair success, and cost/latency/stability
  release remain later production-quality specs.

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
3. Framework-neutral agent runtime, model provider adapter, and agent framework adapter gate.
4. Browser, document, authorized session, and API-like source adapters.
5. Graph projections and graph-driven frontier/review workflows.
6. Memory kernel and scoped retrieval/invalidation.
7. Full multi-agent orchestration and repair loops.
8. Review/replay/ops console and quality dashboards.
9. Export connectors, receipts, withdrawal, and correction propagation.
10. Scale hardening, autoscaling, backpressure, chaos, DR, security, privacy, and compliance.

The product must not claim target architecture completion until all target capability profiles are verified and operational.
