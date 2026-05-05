# Feature Specification: Crawler Optimization Runtime Wiring

**Feature Branch**: `087-crawler-optimization-runtime-wiring`  
**Created**: 2026-05-06  
**Status**: Implemented  
**Input**: User description: "Wire crawler intelligence optimization contracts into production runtime components so scheduler/frontier, DOM context, extractor fallback, canonical dedupe, ranking, and ops metric flows can consume the spec 080-086 optimization gate outputs through existing owner-service boundaries, commands, events, policy refs, and replay refs without coupling core packages to adapters or narrowing VeraCrawl into a single-site scraper."

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature wires generic crawler
  optimization contracts into the runtime spine. It must remain source-pattern,
  website, schema, and domain agnostic; no single ecommerce, documentation, or
  listing assumptions may become core behavior.
- **Target/V1 boundary**: This is target architecture integration work layered
  after specs 080-086. It may expose V1-compatible deterministic adapters for
  the production spine, but V1 acceptance must still stay inside documented V1
  profiles.
- **Evidence and replay impact**: Affected paths include frontier priority
  records, normalized DOM context artifacts, extractor attempts, canonical URL
  and duplicate decisions, ranked output refs, optimization metric slices,
  command/event/outbox refs, policy refs, artifact refs, content hashes, and
  replay refs.
- **Safety and policy impact**: Source scope, robots/terms, private-network
  denial, credential isolation, prompt-taint boundaries, browser approval,
  action budgets, cache freshness, and no-bypass rules remain hard gates before
  any optimization signal can schedule, extract, publish, or rank.
- **Required reference docs**: `docs/02-production-architecture.md`,
  `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and specs 080-086.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Runtime Uses Optimization Scores (Priority: P1)

An approved crawl run can score discovered URLs through the optimization
scoring profile and persist replayable score decisions that the scheduler can
consume without depending on benchmark-only code.

**Why this priority**: Frontier scheduling is the first place optimization
changes runtime behavior and controls downstream cost, recall, and latency.

**Independent Test**: A deterministic scheduler fixture submits discovered URLs
with source anchors and receives ordered `FrontierScoreBreakdown` refs plus
queue priorities, policy refs, command/event/outbox refs, and replay refs.

**Acceptance Scenarios**:

1. **Given** an approved run with candidate URLs and source anchors, **When**
   the runtime scoring service evaluates them, **Then** each candidate has a
   persisted score breakdown and scheduler priority.
2. **Given** a URL blocked by source policy or robots, **When** scoring is
   requested, **Then** the runtime records a blocked decision and does not
   enqueue the URL.

---

### User Story 2 - Runtime Produces DOM And Extraction Context (Priority: P1)

Normalized HTML or browser artifacts can be converted into pruned DOM context
and extractor fallback attempts that reuse source anchors, validators, and
confidence thresholds outside the benchmark gate.

**Why this priority**: Extraction stability and token efficiency depend on
runtime DOM/context creation before model or LLM fallback is invoked.

**Independent Test**: A normalized document fixture emits `DomContextBundle`,
`ExtractorFallbackPlan`, accepted `ExtractorAttemptRecord`, and
`FieldConfidenceScore` refs without treating model output as source evidence.

**Acceptance Scenarios**:

1. **Given** a normalized HTML artifact, **When** DOM context wiring runs,
   **Then** retained nodes, page zones, and interactive elements include source
   anchors and replay refs.
2. **Given** structured data or stable DOM fields, **When** extractor fallback
   runs, **Then** deterministic source-backed attempts are accepted before LLM
   fallback is considered.

---

### User Story 3 - Runtime Applies Dedupe And Ranking Before Publication (Priority: P2)

Publication and result projection can suppress duplicate candidates and rank
retained outputs using the generic optimization ranking profile before
operator-visible results are materialized.

**Why this priority**: Deduplication and ranking improve final result quality
but must not alter evidence verification or fabricate missing fields.

**Independent Test**: A projection fixture receives candidate refs, canonical
URL refs, fingerprints, and evidence-backed fields, then emits duplicate
suppression and ranked output refs with stable replay lineage.

**Acceptance Scenarios**:

1. **Given** candidate outputs with tracking variants and near-duplicates,
   **When** runtime dedupe runs, **Then** duplicate refs are suppressed while
   true variants remain retained or routed to review.
2. **Given** retained outputs with evidence-backed fields, **When** ranking
   runs, **Then** ranked refs include score breakdowns and do not change field
   verification decisions.

---

### User Story 4 - Ops Aggregates Runtime Optimization Metrics (Priority: P2)

Operators can see whether runtime optimization improves precision, recall,
duplicate rate, cost per successful result, latency, token usage, and replay
coverage compared with baseline behavior.

**Why this priority**: Optimization must be measurable and release-blocking
before runtime behavior can be treated as production-ready.

**Independent Test**: An ops fixture combines scheduler, DOM/extraction,
dedupe, ranking, and replay refs into an optimization report that passes only
when thresholds are met and all required refs are present.

**Acceptance Scenarios**:

1. **Given** runtime optimization lower refs, **When** ops aggregation runs,
   **Then** metric slices and an aggregate report are emitted with threshold
   status and replay refs.
2. **Given** missing lower refs, stale cache reuse, unsafe recovery, or quality
   regression, **When** ops aggregation runs, **Then** the report fails with
   typed diagnostics.

### Edge Cases

- Policy, robots, private-network, credential scope, or browser approval blocks
  an otherwise high-scoring URL.
- Source artifacts are redacted, missing, stale, oversized, or prompt-tainted.
- DOM structure changes and selector confidence drops below threshold.
- Canonicalization removes tracking parameters but must preserve semantic query
  parameters and variant dimensions.
- Ranking input lacks optional fields such as delivery, rating, or review
  count.
- Replay-critical command, event, artifact, source adapter result, or trace refs
  are unavailable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a runtime scoring service that converts
  discovered URL signals into `FrontierScoreBreakdown` records and scheduler
  priority decisions without importing concrete scheduler worker internals.
- **FR-002**: System MUST reject or block optimization decisions before scoring
  when policy, robots, source scope, private-network, credential, or browser
  approval gates deny access.
- **FR-003**: System MUST produce `DomContextBundle`, page zone, and interactive
  element refs from normalized source artifacts while preserving source anchors,
  artifact refs, prompt-taint labels, and replay refs.
- **FR-004**: System MUST expose extractor fallback orchestration that prefers
  deterministic source-backed extraction steps before LLM structured fallback.
- **FR-005**: System MUST validate accepted fields with field-level confidence,
  normalization, evidence, and publication gate refs, and MUST abstain rather
  than publish low-confidence or unanchored fields.
- **FR-006**: System MUST expose canonicalization, fingerprint, identity, and
  duplicate suppression services that can be called by scheduler and projection
  flows without deleting raw artifacts or verified evidence.
- **FR-007**: System MUST expose generic ranking services that rank retained
  outputs from evidence-backed fields and score features without changing
  verification decisions or fabricating missing fields.
- **FR-008**: System MUST aggregate runtime optimization metrics into
  `CrawlerOptimizationReport`-compatible outputs with pass/fail diagnostics,
  threshold refs, metric slices, command/event/outbox refs, and replay refs.
- **FR-009**: System MUST provide deterministic fixtures and negative cases for
  policy-blocked scoring, missing DOM anchors, LLM-as-evidence,
  duplicate-variant collapse, ranking quality regression, unsafe recovery, and
  missing replay refs.
- **FR-010**: System MUST keep core packages framework-neutral and adapter-free;
  model SDKs, browser engines, storage clients, queue clients, and agent
  frameworks must remain behind ports/adapters.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid
  feature-specific assumptions that block other websites, source patterns,
  schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events,
  typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output
  manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy
  lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and
  acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **RuntimeOptimizationSignalSet**: Runtime-safe URL, DOM, extraction, identity,
  cost, and quality signals passed to optimization services.
- **RuntimeFrontierOptimizationDecision**: Score, priority, policy status, and
  scheduler action for a discovered URL.
- **RuntimeDomExtractionContext**: Pruned DOM refs, extractor plan refs,
  confidence refs, and abstention/publication status for normalized artifacts.
- **RuntimeDedupeRankingDecision**: Canonical URL, fingerprint, identity,
  duplicate suppression, ranking score, and sorted output refs.
- **RuntimeOptimizationAggregate**: Ops metric slices, threshold status, lower
  refs, diagnostics, and replay refs.

### Non-Goals *(mandatory)*

- This feature does not train a learning-to-rank model.
- This feature does not replace production evidence, verification, or
  publication gates.
- This feature does not make graph, memory, embedding, or model output
  authoritative source evidence.
- This feature does not implement new external source adapters.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Runtime scoring fixtures emit score breakdowns and scheduler
  priority decisions for 100% of allowed candidate URLs and typed blocked
  decisions for 100% of denied URLs.
- **SC-002**: Runtime DOM fixtures retain all oracle-required anchors while
  reducing model context bytes by at least 50% compared with raw DOM input.
- **SC-003**: Runtime extraction fixtures accept deterministic source-backed
  fields before LLM fallback and reject LLM-only source evidence in 100% of
  negative cases.
- **SC-004**: Runtime dedupe fixtures reduce duplicate publication candidates
  by at least 50% without collapsing declared variants.
- **SC-005**: Runtime ranking fixtures emit score breakdown refs for 100% of
  ranked outputs and preserve verification status for every ranked item.
- **SC-006**: Ops aggregation fixtures fail on missing lower refs, missing replay
  refs, unsafe recovery, stale cache, or quality regression, and pass only when
  all required command/event/outbox/replay refs are present.

## Assumptions

- Existing optimization contracts from spec 080 can be reused rather than
  duplicated.
- Initial runtime wiring may use deterministic/local fixtures before live
  source corpora are extended.
- Existing scheduler, normalization, extraction, projection, and ops packages
  expose enough stable ports or helpers to add low-coupling services; if not,
  this feature must add ports before service code.

## Implementation Closure

- Runtime wiring contracts were added to
  `src/veracrawl/contracts/crawler_optimization.py` and registered through the
  canonical contract registry without introducing adapter or framework
  dependencies.
- Runtime services live in `src/veracrawl/optimization/runtime.py` and expose
  deterministic frontier scoring, DOM/extraction context, canonical
  dedupe/ranking, and aggregate metric wiring over typed runtime inputs.
- Replay validation lives in
  `src/veracrawl/review_replay/crawler_optimization_runtime.py`; contract,
  registry, import-boundary, unit, replay, lint, type, and full-suite checks
  passed before local commit.
