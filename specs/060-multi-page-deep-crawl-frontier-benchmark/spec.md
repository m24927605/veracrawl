# Feature Specification: Multi-Page Deep Crawl Frontier Benchmark

**Feature Branch**: `060-multi-page-deep-crawl-frontier-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Prove bounded multi-page crawl depth, frontier planning, and replayable stop reasons.

## Constitution Alignment

- **General-purpose crawler impact**: Validates frontier expansion across
  pagination, detail pages, canonical URLs, redirects, duplicate suppression,
  sitemaps, feeds, and browser-discovered links without site-specific rules.
- **Target/V1 boundary**: Quality benchmark after expanded corpus and browser
  quality; it does not claim field extraction or final quality release.
- **Evidence and replay impact**: Requires crawl plan refs, frontier decisions,
  graph refs, page observations, link provenance, stop reasons, artifacts,
  command/event/outbox refs, and replay bundles.
- **Safety and policy impact**: Crawl depth, page count, origin scope, robots,
  request rate, browser budget, and private-network denial must gate every
  frontier expansion.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`,
  `specs/045-live-normalization-site-understanding/spec.md`,
  `specs/050-multi-agent-orchestration-repair-runtime/spec.md`,
  `specs/051-graph-memory-production-runtime/spec.md`,
  `specs/052-worker-orchestration-scale-runtime/spec.md`,
  `specs/058-expanded-real-world-corpus-benchmark/spec.md`, and
  `specs/059-js-browser-crawl-quality-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Run Bounded Deep Crawl (Priority: P1)

An operator can run a depth-limited crawl and prove frontier expansion covered
expected pages without exceeding policy budgets.

**Independent Test**: Run `veracrawl-deep-crawl-benchmark run
tests/fixtures/deep-crawl-quality-corpus --profile quality --out
.veracrawl-real-runs/deep-crawl-quality-corpus`.

**Acceptance Scenarios**:

1. **Given** a crawl objective with depth and page limits, **When** the crawler
   runs, **Then** it records every frontier decision, fetched page, skipped page,
   and stop reason.
2. **Given** a passing deep crawl, **When** coverage is inspected, **Then**
   expected listing, detail, pagination, sitemap/feed, and canonical pages are
   represented according to the oracle.

### User Story 2 - Prevent Frontier Pollution (Priority: P2)

The benchmark must catch duplicate, off-origin, low-value, and unsafe frontier
choices.

**Independent Test**: Negative fixtures seed redirect loops, duplicate canonicals,
off-origin links, infinite pagination, robots-denied links, and empty pages.

### User Story 3 - Prove AI/Graph Frontier Influence (Priority: P3)

When AI/graph/memory participate, their influence must be traceable and bounded.

**Independent Test**: Validate model/agent traces, graph refs, memory refs, and
controlled tool refs for frontier prioritization decisions where enabled.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define deep crawl manifests, frontier decision traces,
  page coverage oracles, stop reason records, and deep crawl reports.
- **FR-002**: System MUST enforce depth, page, origin, rate, browser, retry, and
  private-network budgets before frontier expansion.
- **FR-003**: System MUST record link provenance, source anchors, canonical URL
  refs, duplicate suppression refs, graph frontier refs, and skipped-link refs.
- **FR-004**: System MUST record AI model/agent/tool/context traces when AI
  influences frontier priority, but AI output MUST NOT be source evidence.
- **FR-005**: System MUST report coverage gaps, frontier pollution, loop
  detection, budget exhaustion, policy denial, and replay mismatch as typed
  outcomes.
- **FR-006**: System MUST make replay deterministic enough to verify the same
  frontier decisions from recorded artifacts and policy snapshots.

### VeraCrawl Contract Requirements

- **VC-001**: General crawl planning and frontier logic must not depend on one
  website's URL shape or DOM conventions.
- **VC-002**: Owner services, commands, events, policy decisions, graph refs,
  outbox refs, and replay refs are mandatory for frontier state changes.
- **VC-003**: Deep crawl page observations may seed later extraction/evidence
  but do not publish results in this spec.
- **VC-004**: Scope, robots, rate, budget, browser, credential, prompt-injection,
  and privacy boundaries must gate frontier decisions.
- **VC-005**: Include positive, negative, replay, frontier pollution,
  import-boundary, and live/deep validation tests before completion.

### Key Entities

- **DeepCrawlQualityManifest**: Declares objectives, seeds, budgets, expected
  coverage, allowed origins, and oracle files.
- **FrontierDecisionTrace**: Records one keep/skip/prioritize/stop decision with
  source, policy, graph, AI, command/event/outbox, and replay refs.
- **DeepCrawlQualityReport**: Aggregates page coverage, frontier quality,
  stop reasons, budget use, policy outcomes, and replay status.

### Non-Goals

- This spec does not implement unbounded crawling, broad web discovery,
  credentialed crawling, extraction quality, or publication quality.
- Unsafe automation and policy bypass remain forbidden.

## Success Criteria

- **SC-001**: Quality profile crawls at least 5 bounded sites and at least 50
  total pages while respecting per-origin budgets.
- **SC-002**: 100% of frontier expansion decisions have policy, source, command,
  event, outbox, and replay refs.
- **SC-003**: Duplicate loops, off-origin expansion, robots denial, infinite
  pagination, budget exhaustion, and replay mismatch fail with typed diagnostics.
- **SC-004**: Validation results are recorded in `tasks.md`.

## Assumptions

- Public deep crawl targets are selected for low-impact traversal and conservative
  rate limits; deterministic local fixtures cover risky edge cases.
