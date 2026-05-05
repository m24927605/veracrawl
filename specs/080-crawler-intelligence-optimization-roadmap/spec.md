# Feature Specification: Crawler Intelligence Optimization Roadmap

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Roadmap Control Spec  
**Input**: User request: "Plan and write the related specs for crawler intelligence optimizations covering search accuracy, extraction stability, cost efficiency, drift resistance, dedupe, ranking, and agent decision quality."

## Purpose

This spec fixes the post-079 crawler intelligence optimization roadmap. It
captures the next bounded set of production follow-up specs for VeraCrawl's
general-purpose crawling intelligence: frontier scoring, DOM understanding,
extraction fallback and confidence, canonical dedupe and identity, ranking, and
cost/recovery/evaluation gates.

These specs improve production-grade crawler quality after the closure gate.
They do not replace specs 069-075, do not weaken the aggregate production-grade
release rules, and do not create a single-site or ecommerce-only product path.

## Constitution Alignment

- **General-purpose crawler impact**: The roadmap applies across websites,
  source adapters, page patterns, schemas, output types, and data domains. It
  uses ecommerce offer ranking as one validation surface only, not as the
  product boundary.
- **Target/V1 boundary**: This is target architecture and production follow-up
  sequencing layered after specs 069-079. V1 runtime paths may adopt only the
  pieces permitted by the V1 profile, while target contracts preserve full
  graph, memory, browser, multi-agent, export, scale, and operations capability.
- **Evidence and replay impact**: Frontier scores, DOM element rankings,
  extraction confidence, dedupe clusters, ranking scores, recovery decisions,
  and evaluation gates must carry source refs, command/event/outbox refs,
  policy refs, artifact refs, model/tool/context trace refs when AI is used,
  and replay refs. None of these signals may substitute for source evidence.
- **Safety and policy impact**: The roadmap preserves robots, terms, source
  scope, credential, private-network, browser sandbox, prompt-taint, privacy,
  retention, and no-bypass boundaries from the production closure specs.
- **Required reference docs**: `docs/01-product-definition.md`,
  `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`,
  `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## Approved Optimization Specs

| Spec | Name | Purpose | Blocking Dependencies | Completion Gate |
| --- | --- | --- | --- | --- |
| 081 | Focused Frontier Scoring Runtime | Replace raw priority integers with replayable score breakdowns for objective relevance, page type value, URL pattern, anchor/title signals, semantic similarity, graph distance, freshness, historical success, duplicate risk, policy risk, and expected cost. | 072, 028, 051, 060, 080 | Bounded crawls use score-backed priority decisions with deterministic stop reasons and lower duplicate fetch/cost rates on fixture and live corpora. |
| 082 | DOM Page Understanding And Element Ranking Runtime | Create pruned DOM artifacts, page/element classifiers, interactive element rankings, and LLM-ready context bundles for search boxes, filters, pagination, sort controls, product cards, price blocks, tables, and document metadata zones. | 045, 070, 081 | Normalized/browser pages produce replayable DOM intelligence artifacts that improve page classification and reduce model context size without losing required evidence anchors. |
| 083 | Extractor Fallback And Confidence Runtime | Implement a deterministic-first extractor fallback chain with official/authorized sources, structured data, meta tags, tables/repeated DOM blocks, selector memories, regex, and LLM structured extraction only as a bounded fallback with field confidence and abstention. | 046, 047, 073, 082 | Field extraction passes source-backed oracle gates with calibrated confidence, abstains on low evidence, and never publishes LLM-only values. |
| 084 | Canonical Dedupe And Identity Runtime | Add URL canonicalization policy, parameter normalization, content/template duplicate detection, SimHash/MinHash clusters, embedding similarity advisory clusters, and entity/product/article identity records with variant handling. | 072, 073, 081, 083 | Duplicate loops, tracking/session parameters, same-page/template duplicates, same-product/article clusters, and variant splits are replayably classified with reduced duplicate pollution. |
| 085 | Recommendation Ranking Runtime | Add generic ranking score records for results/offers/documents using intent match, evidence quality, source reliability, freshness, availability, price, delivery, ratings, confidence, and source-limited penalties, with heuristic ranking first and learning-to-rank only after labels exist. | 078, 079, 083, 084 | Ranked outputs are deterministic, evidence-backed, explainable, and improve offline ranking metrics without fabricating missing fields. |
| 086 | Cost Recovery Evaluation Runtime | Aggregate token/browser/fetch/storage cost controls, cache hit metrics, retry and repair outcomes, drift signals, benchmark metrics, regression gates, and optimization release readiness across specs 081-085. | 074, 081-085 | Optimization release passes only when quality, duplicate rate, cost per successful result, latency, repair success, and replay completeness meet thresholds. |

## Roadmap Rules

- **RR-001**: Specs 081-086 are the approved optimization follow-up specs. They
  are not additional production-grade closure specs and must not change the
  aggregate 075 gate without an explicit release-gate amendment.
- **RR-002**: These specs may improve production-grade claims for new validated
  corpora only when their reports are supplied as supplemental quality evidence.
  They must not invalidate the existing 069-075 lower gate structure.
- **RR-003**: No optimization may narrow VeraCrawl into a single-site scraper,
  ecommerce-only comparison engine, browser automation demo, or LLM-only
  extractor.
- **RR-004**: Scoring, ranking, graph, memory, and model output are planning or
  review signals. Published output still requires source-backed evidence,
  verification, policy, privacy, and replay.
- **RR-005**: Implementation must proceed in spec order unless this roadmap,
  `docs/08-build-roadmap.md`, and
  `specs/038-production-runtime-closure/spec.md` are amended.
- **RR-006**: Each activated spec must run Spec Kit clarify where ambiguity
  remains, plan, tasks, analyze when available, implementation, and real
  verification with validation results recorded in `tasks.md`.

## User Scenarios & Testing

### User Story 1 - Prioritize High-Value Crawl Paths (Priority: P1)

An operator runs an approved crawl objective and expects VeraCrawl to spend
fetch, browser, and model budget on pages most likely to satisfy the objective,
while retiring low-value, duplicate, unsafe, or exhausted paths with visible
stop reasons.

**Why this priority**: Frontier quality is the highest-leverage way to improve
search accuracy, cost efficiency, and agent decision quality.

**Independent Test**: A deep-crawl fixture with listing/detail/pagination,
duplicates, and low-value zones must emit frontier score breakdowns and fetch
the required pages before exhausting budget.

**Acceptance Scenarios**:

1. **Given** a crawl objective and candidate URLs with mixed relevance, **When**
   frontier scoring runs, **Then** high-intent listing/detail/document pages are
   scheduled ahead of duplicate, off-topic, and high-cost pages.
2. **Given** a crawl loop, duplicate URL variants, or exhausted budget, **When**
   the scheduler stops, **Then** it records replayable duplicate, budget, or
   marginal-gain stop reasons.

### User Story 2 - Extract Stable Fields From Changing Pages (Priority: P1)

A data operator needs records, tables, product offers, document metadata, and
facts extracted through stable source-backed methods before any LLM fallback is
used.

**Why this priority**: Extraction stability and abstention directly determine
publication quality and reviewer workload.

**Independent Test**: Field-oracle fixtures with JSON-LD, meta, repeated DOM
cards, table rows, selector drift, and missing evidence must pass or abstain
with typed diagnostics.

**Acceptance Scenarios**:

1. **Given** a page with structured data and visible DOM fields, **When**
   extraction runs, **Then** deterministic extractors produce anchored
   candidates before LLM extraction is considered.
2. **Given** selector drift or contradictory fields, **When** verification
   evaluates candidates, **Then** outputs are blocked or routed to repair/review
   instead of silently publishing.

### User Story 3 - Rank Results With Evidence And Cost Awareness (Priority: P2)

Downstream users need ranked records, offers, or documents that balance intent
match, quality, freshness, availability, price, delivery, source reliability,
and extraction confidence without fabricating unsupported fields.

**Why this priority**: Ranking quality matters after the crawler can discover
and verify enough source-backed candidates.

**Independent Test**: Ranking fixtures with accepted, partial, stale, duplicate,
and source-limited outputs must produce explainable score records and improve
offline ranking metrics.

**Acceptance Scenarios**:

1. **Given** multiple evidence-backed candidate outputs, **When** ranking runs,
   **Then** it emits score breakdowns and sorted refs for the configured ranking
   profile.
2. **Given** missing delivery, price, rating, or availability fields, **When**
   ranking runs, **Then** missing fields are penalized or marked absent without
   fabrication.

## Edge Cases

- Search/listing pages expose candidate URLs only in structured scripts rather
  than anchor tags.
- Pages contain JavaScript app shells, lazy-loaded fields, infinite pagination,
  login walls, human checks, or source-limited responses.
- Tracking, sorting, session, locale, and pagination parameters create large URL
  variant sets.
- Product/article/document identity is ambiguous or includes variants that
  should not be merged.
- Model output proposes a URL, value, or ranking reason without source anchors.
- Cached artifacts are stale, redacted, deleted, or legally held.
- Replay-critical command, event, artifact, trace, score, or policy refs are
  missing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define specs 081-086 with purpose, dependencies,
  requirements, completion gates, and non-goals.
- **FR-002**: System MUST define optimization metrics for crawl precision,
  recall, extraction accuracy, duplicate rate, crawl success rate, cost per
  successful result, latency, repair success, ranking quality, and replay
  completeness.
- **FR-003**: System MUST require deterministic owner-service decisions for
  canonicalization, dedupe, field validation, publication gates, cache use,
  budget enforcement, retry classification, and stop conditions.
- **FR-004**: System MUST restrict LLM use to bounded planning, low-confidence
  classification, extraction fallback, repair recommendation, and verification
  recommendation paths with trace refs.
- **FR-005**: System MUST keep optimization score records advisory unless they
  are consumed by the owning scheduler, verifier, publisher, review router, or
  ops service through typed commands and events.
- **FR-006**: System MUST define negative tests for LLM-as-evidence,
  graph/memory-as-evidence, unsupported publication, duplicate pollution,
  unsafe browser interaction, source-limited fabrication, missing replay, and
  unbounded budget use.

### VeraCrawl Contract Requirements

- **VC-001**: Preserve general-purpose crawling across many websites, source
  patterns, schemas, page types, and domains.
- **VC-002**: Define owner services, commands, events, typed reports, policy
  decisions, score refs, artifact refs, and replay refs for every optimization
  signal that affects scheduling, extraction, dedupe, ranking, review, or ops.
- **VC-003**: Ensure all outputs still pass evidence, verification,
  publication, and output manifest gates before publication.
- **VC-004**: Preserve security, credential, prompt-injection, privacy
  lifecycle, retention, and export/withdrawal behavior.
- **VC-005**: Require fixture/oracle, negative, replay, import-boundary,
  registry, live/fixture, and regression tests before implementation.

### Key Entities

- **CrawlerOptimizationRoadmap**: Approved sequence of optimization specs and
  their dependency gates.
- **OptimizationMetricSet**: Canonical metric keys, thresholds, slices, and
  release-blocking status.
- **OptimizationCapabilityReport**: Aggregate readiness report over the
  optimization specs, lower reports, blockers, and false-ready guards.

### Non-Goals

- This roadmap does not implement runtime code by itself.
- This roadmap does not claim every website is crawlable or every optimization
  is complete.
- This roadmap does not replace specs 069-075 or weaken the aggregate
  production-grade release gate.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria

- **SC-001**: Specs 081-086 exist with clear purpose, dependency, functional
  requirements, completion gates, and non-goals.
- **SC-002**: `docs/08-build-roadmap.md`,
  `specs/038-production-runtime-closure/spec.md`, and
  `specs/068-production-grade-crawler-closure-roadmap/spec.md` reference this
  roadmap without changing the 069-075 production-grade closure structure.
- **SC-003**: The roadmap defines measurable optimization metrics and required
  negative cases before implementation.
- **SC-004**: The roadmap keeps AI, graph, memory, score, ranking, and cache
  signals separate from source evidence.
- **SC-005**: Future extensions can proceed spec-by-spec without inventing
  additional ad hoc optimization specs.

## Assumptions

- Specs 069-075 remain the current production-grade closure gate.
- Specs 076-079 remain ecommerce market follow-ups layered on source-backed
  product discovery and offer projection.
- Optimization work may amend acceptance thresholds for future validation
  corpora, but it must not weaken existing source-backed evidence, policy, or
  replay requirements.

## Implementation Closure

- Specs 081-086 were implemented as a shared, general-purpose optimization gate
  rather than a single-site scraper or vertical-only pipeline.
- Runtime materialization lives in `src/veracrawl/contracts/`,
  `src/veracrawl/benchmarks/`, `src/veracrawl/cli/`, and
  `src/veracrawl/review_replay/` with registry, fixture, contract, unit,
  integration, replay, import-boundary, lint, and type checks.
- The implemented gate remains post-079 optimization evidence and does not
  modify the 069-075 production-grade release semantics.
