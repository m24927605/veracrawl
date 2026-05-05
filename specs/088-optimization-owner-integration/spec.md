# Feature Specification: Optimization Owner-Service Integration Roadmap

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: User description: "List and write the required specs, then implement the complete optimization owner-service integration set using the Spec Kit workflow only. The set activates specs 089-096 after the completed crawler intelligence optimization contracts and runtime wiring from specs 080-087."

## Purpose

This control spec fixes the finite post-087 optimization activation roadmap.
Specs 089-096 connect the already implemented crawler optimization contracts
and runtime wiring into owner-service integration surfaces for scheduler,
normalize/browser, extract/verify, graph/dedupe, publish/ranking, ops/cost,
drift/recovery feedback, and regression release gates.

The goal is to move from standalone optimization runtime services to
replayable owner-service decisions while preserving VeraCrawl as a
general-purpose AI agent crawler. This roadmap does not authorize new source
adapters, external model SDK coupling, browser bypass behavior, or single-site
scraper assumptions.

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: The integration set is generic across
  websites, source patterns, page types, schemas, output domains, and ranking
  profiles. Ecommerce remains only a validation surface, not the product
  boundary.
- **Target/V1 boundary**: This is target architecture integration layered after
  specs 080-087. V1 paths may consume deterministic HTTP-first optimization
  decisions only when they stay within the V1 profile documented in
  `docs/01-product-definition.md`, `docs/02-production-architecture.md`,
  `docs/07-data-contracts.md`, and `docs/08-build-roadmap.md`.
- **Evidence and replay impact**: Frontier priorities, normalized DOM context,
  extractor attempts, field confidence, canonical URLs, fingerprints, identity
  decisions, ranking outputs, cache/budget decisions, drift feedback, ops
  reports, command/event/outbox refs, policy refs, artifact refs, and replay
  refs become owner-service-visible integration outputs.
- **Safety and policy impact**: Source scope, robots/terms, private-network
  denial, credential isolation, browser approval, prompt-taint boundaries,
  cache freshness, retry budgets, publication gates, privacy lifecycle, and
  no-bypass rules remain hard gates before any optimization output mutates or
  publishes owner-service state.
- **Required reference docs**: `docs/README.md`,
  `docs/01-product-definition.md`, `docs/02-production-architecture.md`,
  `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## Approved Integration Specs

| Spec | Name | Purpose | Blocking Dependencies | Completion Gate |
| --- | --- | --- | --- | --- |
| 089 | Priority Frontier Scheduler Integration | Consume runtime frontier optimization decisions through scheduler-owned priority, retire, block, and stop-condition integration refs. | 081, 087, 088 | Scheduler integration emits replayable optimized enqueue/block/retire decisions without importing benchmark, adapter, or agent-framework code. |
| 090 | DOM Intelligence Normalize Integration | Consume DOM pruning, page zones, and interactive element rankings through normalize/browser-owned context refs. | 082, 087, 088 | Normalization integration emits DOM intelligence refs with source anchors, artifact refs, prompt-taint policy refs, and reduced context sizes. |
| 091 | Extraction Fallback Verification Integration | Consume extractor fallback plans, deterministic attempts, field confidence, abstention, and LLM-fallback guards through extract/verify boundaries. | 083, 090 | Extract/verify integration accepts source-backed fields, rejects LLM-only evidence, and routes low-confidence fields to review. |
| 092 | Canonical Dedupe Identity Integration | Consume canonicalization, fingerprints, duplicate suppression, and variant preservation through scheduler/normalize/graph boundaries. | 084, 089, 091 | Dedupe integration suppresses tracking/session duplicates while preserving declared variants and replaying identity decisions. |
| 093 | Recommendation Ranking Publication Integration | Consume ranking scores and retained outputs through publish/projection boundaries without changing evidence or verification status. | 085, 091, 092 | Publication integration emits ranked output refs and explanations for retained evidence-backed outputs only. |
| 094 | Optimization Cost Cache Budget Runtime | Consume cost, cache, fetch/browser/token budget, and replay metrics across owner-service decisions. | 086, 089-093 | Cost/cache integration blocks stale cache reuse, budget overrun, and missing metric refs before optimization release. |
| 095 | Drift Recovery Feedback Runtime | Feed selector drift, retry classification, repair outcomes, and failure memory refs back into future optimization decisions without treating memory as evidence. | 083, 086, 091, 094 | Recovery integration records typed drift and repair feedback with policy/replay refs and no owner-service bypass. |
| 096 | Optimization Regression Release Gate | Aggregate 089-095 owner-service integration evidence into a release-blocking regression gate. | 089-095 | Release gate passes only when lower integration refs, replay refs, quality metrics, duplicate metrics, cost metrics, and negative fixtures all pass. |

## Roadmap Rules

- **RR-001**: Specs 089-096 are the approved post-087 optimization
  owner-service integration specs. They are not production-grade closure specs
  and must not modify the aggregate 075 production-grade release semantics.
- **RR-002**: No additional optimization integration specs may be added without
  amending this spec, `docs/08-build-roadmap.md`,
  `specs/038-production-runtime-closure/spec.md`, and
  `specs/080-crawler-intelligence-optimization-roadmap/spec.md` first.
- **RR-003**: Owner services remain responsible for durable state mutation.
  Optimization services may compute typed decisions, but scheduler,
  normalize/browser, extract/verify, graph, publish/projection, and ops own
  adoption and publication boundaries.
- **RR-004**: LLM, embedding, graph, memory, and ranking signals remain
  advisory. Published output still requires source-backed evidence,
  verification, publication policy, privacy, and replay.
- **RR-005**: Each activated spec must use Spec Kit specify, plan, tasks,
  analyze, implement, and validation recording. This control spec may implement
  the full 089-096 set as one cohesive activation only because the user
  explicitly requested all listed specs and implementation in one run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scheduler Consumes Optimization Decisions (Priority: P1)

An approved crawl run can route discovered URL candidates through optimization
runtime decisions and have the scheduler enqueue, block, retire, or stop using
typed score refs instead of raw priority integers.

**Why this priority**: Frontier integration is the first owner-service mutation
point and determines downstream recall, cost, duplicate load, and latency.

**Independent Test**: A deterministic scheduler fixture submits allowed,
blocked, duplicate-risk, and low-score URL candidates and receives scheduler
integration records with policy refs, score refs, command/event/outbox refs,
and replay refs.

**Acceptance Scenarios**:

1. **Given** allowed URL candidates with optimization scores, **When** scheduler
   integration runs, **Then** candidates are returned as priority-ordered
   enqueue records with score breakdown refs.
2. **Given** policy-blocked or low-marginal-gain candidates, **When** scheduler
   integration runs, **Then** candidates are blocked or retired with typed stop
   reasons and no enqueue mutation.

---

### User Story 2 - Processing Owners Consume DOM And Extraction Context (Priority: P1)

Normalized source artifacts can be converted into DOM intelligence and
extractor/verification integration records that preserve anchors and keep
deterministic source-backed attempts ahead of LLM fallback.

**Why this priority**: Extraction stability and token efficiency depend on
normalize and extract/verify owner-service adoption, not only standalone
runtime helpers.

**Independent Test**: A normalized HTML fixture emits normalize integration and
extract/verify integration records that include DOM context refs, extractor
attempt refs, field confidence refs, abstention refs, and review refs for
low-confidence or LLM-only fields.

**Acceptance Scenarios**:

1. **Given** an HTML artifact with repeated product/article/table-like blocks,
   **When** normalize integration runs, **Then** pruned DOM, page zone, and
   element ranking refs are owner-service visible.
2. **Given** accepted deterministic fields and LLM-only field proposals,
   **When** extract/verify integration runs, **Then** source-backed fields are
   accepted and LLM-only evidence is rejected or routed to review.

---

### User Story 3 - Publication Uses Dedupe And Ranking Without Rewriting Evidence (Priority: P2)

Projection and publication flows can suppress duplicate candidate outputs and
rank retained outputs while leaving verification and evidence decisions
unchanged.

**Why this priority**: Ranking improves user-visible result quality, but it
must not fabricate fields or bypass verification.

**Independent Test**: A projection fixture feeds canonical URL refs,
fingerprints, identity decisions, and verified field refs into dedupe/ranking
integration and receives retained/suppressed refs plus ranked output refs.

**Acceptance Scenarios**:

1. **Given** duplicate URL variants and declared product/document variants,
   **When** dedupe integration runs, **Then** tracking duplicates are suppressed
   and true variants remain retained or needs-review.
2. **Given** retained evidence-backed outputs, **When** ranking integration
   runs, **Then** ranked refs include score breakdowns and preserve every input
   verification status.

---

### User Story 4 - Ops Gates Cost, Recovery, And Regression Evidence (Priority: P2)

Operators can see whether owner-service optimization integration improves
quality, cost, duplicate rate, latency, recovery behavior, and replay
completeness before release.

**Why this priority**: Runtime integration must remain measurable and
release-blocking, otherwise optimization changes can silently regress crawler
quality.

**Independent Test**: An ops fixture aggregates 089-095 integration refs and
fails when lower refs, replay refs, stale cache diagnostics, unsafe recovery,
quality metrics, or cost metrics are missing or regressed.

**Acceptance Scenarios**:

1. **Given** complete lower integration refs and metric slices, **When** the
   regression release gate runs, **Then** it emits a pass report with replay
   refs and no false-ready blockers.
2. **Given** missing replay, stale cache reuse, unsafe recovery, or metric
   regression, **When** the release gate runs, **Then** it fails with typed
   diagnostics.

### Edge Cases

- Optimization scoring suggests a URL that policy, robots, source scope,
  private-network denial, credential scope, or browser approval blocks.
- DOM artifacts are missing anchors, stale, oversized, prompt-tainted, or
  derived from a browser path without approval.
- Extractor fallback produces LLM-only values, contradictory values, invalid
  price/currency/availability fields, or fields below confidence thresholds.
- Canonicalization removes tracking parameters but must preserve semantic
  search, pagination, locale, product id, SKU, and variant parameters.
- Ranking input lacks optional price, delivery, rating, review count, seller, or
  freshness fields.
- Cache entries are stale, content hashes mismatch, budgets are exhausted, or
  replay-critical command/event/artifact refs are unavailable.
- Drift repair recommendations would bypass owner services, policy gates, or
  evidence verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define specs 089-096 with purpose, dependencies,
  completion gates, non-goals, and owner-service boundaries.
- **FR-002**: System MUST expose scheduler integration records that map
  frontier optimization decisions to enqueue, block, retire, or stop outcomes
  with score refs, policy refs, and replay refs.
- **FR-003**: System MUST expose normalize integration records that map DOM
  context bundles, page zones, retained node refs, and interactive element refs
  to normalized document refs and artifact refs.
- **FR-004**: System MUST expose extract/verify integration records that map
  extractor plans, attempts, confidence scores, abstentions, and review refs to
  source-backed field outcomes.
- **FR-005**: System MUST reject LLM-only values, graph-only values, memory-only
  values, and ranking-only values as publication evidence.
- **FR-006**: System MUST expose dedupe/identity integration records that map
  canonical URL decisions, fingerprints, identity decisions, duplicate
  suppression refs, retained refs, and suppressed refs to owner-service refs.
- **FR-007**: System MUST expose ranking/publication integration records that
  map ranking scores and ranked output sets to retained, verified output refs
  without modifying evidence or verification decisions.
- **FR-008**: System MUST expose cost/cache/budget integration records that
  block stale cache reuse, missing metric refs, browser/token/fetch budget
  overrun, and missing replay refs.
- **FR-009**: System MUST expose drift/recovery feedback records that classify
  selector drift, retry outcomes, repair outcomes, and failure feedback without
  letting memory or repair suggestions become source evidence.
- **FR-010**: System MUST expose a regression release gate that aggregates
  089-095 lower integration refs and fails on missing lower refs, replay gaps,
  unsafe recovery, source-limited fabrication, duplicate regression, ranking
  regression, quality regression, or cost/SLO regression.
- **FR-011**: System MUST keep all integration code Python, framework-neutral,
  adapter-free, and benchmark-free in core owner-service packages.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid
  feature-specific assumptions that block other websites, source patterns,
  schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events,
  typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output
  manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection,
  privacy lifecycle, and export/withdrawal behavior when those boundaries are
  affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and
  acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **OptimizationOwnerIntegrationRoadmap**: Approved 089-096 spec set,
  dependency order, non-goals, policy refs, and replay refs.
- **SchedulerOptimizationIntegration**: Scheduler-owned adoption of frontier
  score decisions into enqueue/block/retire/stop outcomes.
- **NormalizeOptimizationIntegration**: Normalize/browser-owned adoption of DOM
  context, page zones, and interactive element rankings.
- **ExtractVerifyOptimizationIntegration**: Extract/verify-owned adoption of
  fallback attempts, field confidence, abstention, review, and publication
  eligibility.
- **DedupeIdentityOptimizationIntegration**: Scheduler/normalize/graph-owned
  adoption of canonicalization, fingerprint, identity, duplicate suppression,
  retained, and suppressed refs.
- **RankingPublicationOptimizationIntegration**: Publish/projection-owned
  adoption of ranked output refs without rewriting evidence.
- **CostCacheBudgetOptimizationIntegration**: Ops-owned cost, cache, budget,
  stale-cache, and metric-gate integration record.
- **DriftRecoveryFeedbackIntegration**: Typed drift and recovery feedback for
  future optimization decisions.
- **OptimizationRegressionReleaseGate**: Aggregate pass/fail report over lower
  integration refs, replay refs, metrics, false-ready guards, and diagnostics.

### Non-Goals *(mandatory)*

- This feature does not add new external source adapters, browser engines,
  storage clients, queue clients, model SDKs, or agent frameworks.
- This feature does not train a learning-to-rank model.
- This feature does not replace production evidence, verification, publication,
  or privacy gates.
- This feature does not make graph, memory, embedding, ranking, or LLM output
  authoritative source evidence.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Specs 089-096 exist with clear purpose, dependencies, completion
  gates, non-goals, owner-service boundaries, and negative cases.
- **SC-002**: Scheduler integration fixtures produce enqueue/block/retire/stop
  records for 100% of candidate decisions with policy and replay refs.
- **SC-003**: DOM/extraction integration fixtures retain all required source
  anchors while rejecting LLM-only evidence in 100% of negative cases.
- **SC-004**: Dedupe/ranking integration fixtures suppress declared duplicates
  without collapsing declared variants and rank retained verified refs without
  changing verification status.
- **SC-005**: Cost/cache/recovery fixtures fail on stale cache reuse, budget
  overrun, unsafe recovery, missing metrics, and missing replay refs.
- **SC-006**: Regression release gate passes only when all lower integration
  refs and replay refs are present and all quality, duplicate, ranking, cost,
  latency, and recovery thresholds pass.

## Assumptions

- Specs 080-087 are implemented and remain the source of optimization
  algorithms, contracts, and runtime wiring decisions.
- The first owner-service integration can be deterministic and fixture-backed;
  production adapters remain behind existing ports.
- Owner services may expose thin integration modules that consume optimization
  runtime decisions without coupling their existing core runtime to benchmark
  fixtures or external adapters.

## Implementation Closure

- Specs 089-096 were written and implemented through this Spec Kit control
  workflow as a finite post-087 owner-service integration set.
- Owner-service integration contracts were added to
  `src/veracrawl/contracts/crawler_optimization.py` and registered in
  `src/veracrawl/contracts/registry.py`.
- Adapter-free integration modules were added for scheduler, normalize,
  extract/verify, graph/dedupe, publish/ranking, ops cost/cache, drift/recovery,
  and regression gating.
- Replay validation lives in
  `src/veracrawl/review_replay/crawler_optimization_owner_integration.py`.
- Spec 096 release gating was hardened so passing reports must be built from
  typed lower integration records with complete lower-kind coverage, replay
  refs, metric slices, and regression checks; raw string-only lower refs fail.
- Validation passed: targeted owner integration pytest suite, Spec 096
  representative release evidence tests, `ruff check`, targeted `mypy`, full
  `pytest` with 1404 passed and 5 skipped, and
  `git diff --check`.
