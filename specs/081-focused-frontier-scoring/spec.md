# Feature Specification: Focused Frontier Scoring Runtime

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 081  
**Input**: Optimization roadmap requirement: improve search accuracy, crawl cost efficiency, and agent decision quality through score-backed frontier scheduling.

## Summary

Build a focused, priority-queue frontier runtime that scores URLs and frontier
items from objective relevance, page type value, URL pattern, anchor/title
signals, semantic similarity, graph distance, freshness, historical success,
duplicate risk, policy risk, and expected acquisition/model cost. BFS and DFS
remain bounded traversal modes, but production scheduling uses best-first
priority decisions with replayable score breakdowns and stop reasons.

## Constitution Alignment

- **General-purpose crawler impact**: Scoring features are generic across
  content, ecommerce, documentation, listings, feeds, APIs, and document sites.
- **Target/V1 boundary**: Target architecture work layered on specs 072, 028,
  051, and 060. V1 may use URL/page-structure graph refs only and must not use
  graph signals as extraction or verification confidence.
- **Evidence and replay impact**: Frontier scoring is advisory planning data.
  Every priority change must emit score refs, command/event/outbox refs, policy
  refs, and replay refs.
- **Safety and policy impact**: Source scope, robots, rate, browser, token, and
  private-network gates remain hard filters before scoring can schedule work.
- **Required reference docs**: `docs/02-production-architecture.md`,
  `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, and
  `docs/10-target-implementation-design.md`.

## User Scenarios & Testing

### User Story 1 - Schedule Relevant URLs First (Priority: P1)

An approved crawl run discovers many links and VeraCrawl schedules the URLs most
likely to satisfy the objective before low-value, duplicate, or expensive URLs.

**Why this priority**: Scheduling quality controls recall, cost, latency, and
the number of useless pages the agent observes.

**Independent Test**: A fixture with home, listing, detail, pagination,
document, duplicate, tracking, and off-topic links proves high-value URLs are
leased first and low-value URLs are retired or deferred.

**Acceptance Scenarios**:

1. **Given** candidate URLs with source anchors and page-type hints, **When**
   score calculation runs, **Then** each URL receives a score breakdown and
   priority band.
2. **Given** duplicate or high-risk URLs, **When** the scheduler evaluates them,
   **Then** it lowers priority or retires them with typed reasons.

### User Story 2 - Stop When Marginal Gain Is Low (Priority: P1)

The crawler stops expanding paths when enough evidence-backed coverage exists
or when remaining URLs are too low-value for the configured budget.

**Why this priority**: Bounded crawling must explain why it stopped instead of
silently under-crawling or overspending.

**Independent Test**: A deep-crawl fixture emits frontier exhausted, budget
exhausted, duplicate saturated, confidence reached, and marginal-gain-low stop
reasons.

**Acceptance Scenarios**:

1. **Given** required coverage is satisfied, **When** remaining frontier scores
   fall below threshold, **Then** the run records a confidence-reached or
   marginal-gain-low stop reason.
2. **Given** budget is exhausted before coverage is satisfied, **When** the run
   stops, **Then** the coverage report identifies missing page types and
   budget-limited status.

### Edge Cases

- A URL has high semantic relevance but is blocked by robots or source scope.
- All remaining frontier items are low score but coverage requirements are not
  met.
- Historical success data is unavailable or stale.
- Graph or memory refs are missing, stale, or not enabled for the current
  profile.
- A site has many high-score pages and another site risks starvation.
- AI proposes a priority change without model/tool/context trace refs.
- A score profile is malformed or has weights outside accepted ranges.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `FrontierScoreProfile`,
  `FrontierScoreBreakdown`, `FrontierPriorityDecision`,
  `FrontierRetirementDecision`, and `FrontierStopCondition` contracts.
- **FR-002**: System MUST support bounded BFS for shallow coverage, bounded DFS
  for high-confidence listing/detail paths, and focused best-first priority
  queue crawling as the default production strategy.
- **FR-003**: System MUST calculate score features for intent match, page type
  value, anchor relevance, URL pattern score, semantic similarity, freshness
  debt, historical success, domain/source reliability, graph proximity,
  uncertainty value, duplicate risk, policy/source risk, expected browser cost,
  and retry failure risk.
- **FR-004**: System MUST use this default score formula unless an approved
  profile overrides weights:

```text
fetch_score =
  100 * (
    0.22 * intent_match +
    0.16 * page_type_value +
    0.12 * anchor_relevance +
    0.10 * url_pattern_score +
    0.10 * semantic_similarity +
    0.08 * freshness_debt +
    0.08 * historical_success_rate +
    0.06 * domain_reliability +
    0.05 * graph_proximity +
    0.03 * uncertainty_value
  )
  - 25 * duplicate_risk
  - 20 * policy_or_source_risk
  - 15 * expected_browser_cost
  - 10 * retry_failure_risk
```

- **FR-005**: System MUST enforce hard policy denials before score-based
  scheduling and record policy-blocked items separately from low-score items.
- **FR-006**: System MUST record model/agent/tool/context trace refs when AI
  influences any score feature or priority decision.
- **FR-007**: System MUST prevent starvation by applying per-site fairness,
  priority bands, retry caps, and max-defer counters.
- **FR-008**: System MUST emit replayable stop reasons for frontier exhausted,
  budget exhausted, confidence threshold reached, marginal gain low, duplicate
  saturation, policy blocked, source limited, and operator paused.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose frontier scheduling and avoid
  source-specific scoring logic in core runtime.
- **VC-002**: System MUST define scheduler-owned commands and events for score,
  priority, retry, retire, expand, and stop decisions.
- **VC-003**: System MUST preserve evidence boundaries: score records and graph
  signals cannot become source evidence or verification decisions.
- **VC-004**: System MUST enforce policy, rate, budget, private-network, and
  browser gates before any frontier item can be scheduled.
- **VC-005**: System MUST define contract, fixture/oracle, negative, replay, and
  import-boundary tests before implementation.

### Boundary Rules

- Frontier score records MUST remain planning signals and MUST NOT
  increase extraction or verification confidence by themselves.
- Scheduler remains the owner of durable frontier mutations.
- Graph and memory inputs require refs, freshness, and explanation
  metadata, and cannot become source evidence.
- Every priority, retry, retire, expand, and stop transition must
  carry command/event/outbox and replay refs.

### Key Entities

- **FrontierScoreProfile**: Weight configuration, feature allowlist, thresholds,
  priority bands, and version.
- **FrontierScoreBreakdown**: Per-frontier-item feature values, score, priority
  band, score version, explanation ref, and source refs.
- **FrontierPriorityDecision**: Scheduler-owned decision to enqueue, reprioritize,
  retry, retire, or expand.
- **FrontierStopCondition**: Replayable reason for bounded crawl termination.

### Non-Goals

- This spec does not train a learning-to-rank model.
- This spec does not let agents directly mutate durable scheduler state.
- This spec does not use graph, memory, or model output as source evidence.
- VeraCrawl MUST NOT implement CAPTCHA solving, WAF evasion, stealth
  automation, proxy rotation, or robots/terms bypass.

## Success Criteria

- **SC-001**: Deep-crawl fixture scheduling fetches required pages before
  low-value pages and reports priority decisions for every scheduled item.
- **SC-002**: Duplicate fetch rate decreases by at least 30% on the optimization
  fixture corpus compared with raw priority ordering.
- **SC-003**: Cost per successful evidence-backed result decreases by at least
  20% on the fixture corpus without reducing required-page recall.
- **SC-004**: Every passing priority decision includes policy, command, event,
  outbox, score, and replay refs.
- **SC-005**: Negative fixtures fail for missing score refs, policy bypass,
  graph-as-evidence, model-only priority without traces, starvation, and missing
  stop reasons.

## Assumptions

- Initial semantic similarity may use cached embeddings where available and a
  deterministic zero/unknown value where the vector runtime is unavailable.
- Historical success and domain reliability start from current and prior run
  reports; long-term memory use waits for Memory Kernel readiness.

## Implementation Closure

- Materialized in `FrontierScoringProfile` and `FrontierScoreBreakdown` under
  `src/veracrawl/contracts/crawler_optimization.py`.
- Implemented deterministic priority scoring in
  `src/veracrawl/benchmarks/crawler_optimization.py` with score formula,
  source-signal refs, policy refs, command/event/outbox refs, and replay refs.
- Validated by crawler optimization contract, runtime, fixture, and replay
  tests, including the missing-frontier-score negative fixture.
