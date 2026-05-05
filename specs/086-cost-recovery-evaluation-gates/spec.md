# Feature Specification: Cost Recovery Evaluation Gates

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 086  
**Input**: Optimization roadmap requirement: prove cost efficiency, recovery, drift resistance, benchmark quality, and regression safety for specs 081-085.

## Summary

Create the aggregate optimization gate for crawler intelligence improvements.
It measures quality, cost, latency, token usage, browser usage, cache hit rate,
duplicate rate, crawl success, extraction accuracy, repair success, ranking
quality, drift detection, regression safety, and replay completeness across
specs 081-085.

## Constitution Alignment

- **General-purpose crawler impact**: The aggregate gate evaluates crawler
  quality across sites, source types, page patterns, schemas, and output types.
- **Target/V1 boundary**: Target architecture work layered on operations,
  quality, and specs 081-085. It supplements but does not weaken specs 073,
  074, or 075.
- **Evidence and replay impact**: Optimization metrics and recovery reports must
  be derived from canonical reports, artifacts, command/event/outbox refs, and
  replay refs.
- **Safety and policy impact**: Recovery and cost optimization cannot bypass
  policy, source scope, robots, credentials, prompt-taint, privacy, or retention
  gates.
- **Required reference docs**: `docs/02-production-architecture.md`,
  `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## User Scenarios & Testing

### User Story 1 - Prove Optimization Benefits (Priority: P1)

Operators need evidence that new scoring, DOM, extraction, dedupe, and ranking
capabilities improve outcomes rather than adding complexity.

**Why this priority**: Production optimization must be validated with release
blocking metrics, not anecdotes.

**Independent Test**: An optimization corpus runs baseline and optimized modes
and reports precision, recall, duplicate rate, cost per successful result,
latency, and ranking metrics.

**Acceptance Scenarios**:

1. **Given** baseline and optimized runs over the same corpus, **When**
   evaluation runs, **Then** it reports quality, cost, latency, duplicate, and
   replay deltas by site, pattern, source type, schema, and output type.
2. **Given** metrics regress beyond threshold, **When** the gate evaluates the
   run, **Then** it blocks optimization release with typed blockers.

### User Story 2 - Recover From Failures And Drift (Priority: P1)

Crawler failures, selector drift, timeout clusters, source limitations, and
duplicate pollution should become actionable recovery and review records.

**Why this priority**: Optimization can only be trusted if failure modes remain
visible and repairable.

**Independent Test**: Seeded failure fixtures cover timeout, robots denial,
browser timeout, selector drift, stale cache, duplicate loop, low confidence,
and ranking regression.

**Acceptance Scenarios**:

1. **Given** a seeded selector drift case, **When** extraction fails, **Then**
   the system records drift, proposes repair, and blocks publication until
   validation passes.
2. **Given** repeated timeout or source-limited cases, **When** recovery runs,
   **Then** it applies bounded retries or routes to review without bypass.

### Edge Cases

- Baseline and optimized runs use different corpus refs or source artifacts.
- Cache hit rate improves but stale cache reuse causes quality regression.
- Cost improves by skipping required coverage.
- Repair succeeds in fixture mode but lacks source-backed validation.
- Dead letters, blocked sources, or source-limited cases are hidden by aggregate
  pass metrics.
- Metrics are missing slices for a site, schema, field, or acquisition mode.
- Replay bundle refs are missing for one lower optimization report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `OptimizationBenchmarkManifest`,
  `OptimizationBaselineRun`, `OptimizationMetricSlice`,
  `OptimizationRegressionRecord`, `CacheEfficiencyReport`,
  `DriftRecoveryEvaluation`, `OptimizationReleaseGateReport`, and
  `OptimizationFalseReadyGuard` contracts.
- **FR-002**: System MUST compute metrics for crawl precision, recall,
  extraction accuracy, duplicate rate, crawl success rate, cost per successful
  result, p50/p95/p99 latency, token calls and tokens per successful result,
  browser seconds per successful result, cache hit rate, retry rate, dead-letter
  rate, source-limited rate, repair success rate, ranking NDCG/MRR/precision at
  k, and replay completeness.
- **FR-003**: System MUST compare optimized runs against baseline reports using
  fixed corpus refs, manifest refs, artifact/content hash refs, policy refs,
  command/event/outbox refs, and replay refs.
- **FR-004**: System MUST define cache eligibility for robots, HTTP responses,
  redirects, snapshots, normalized documents, embeddings, model calls, DOM
  summaries, extractor attempts, and ranking features with privacy, freshness,
  invalidation, and legal-hold constraints.
- **FR-005**: System MUST record failure and recovery outcomes for timeout,
  HTTP error, robots denial, source limitation, browser budget exhaustion,
  prompt-taint, selector drift, extraction low confidence, duplicate loops,
  stale cache, ranking regression, and replay mismatch.
- **FR-006**: System MUST block optimization release for quality regression,
  unsupported publication, unsafe recovery, missing replay, cost budget
  violation, duplicate pollution, source-limited fabrication, stale cache reuse,
  or missing lower optimization reports.
- **FR-007**: System MUST require at least three stability runs for optimization
  release readiness.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST keep optimization evaluation broad across crawler
  capabilities and avoid optimizing for one site or vertical.
- **VC-002**: System MUST define ops-owned commands, events, metric reports,
  regression records, blockers, false-ready guards, and replay refs.
- **VC-003**: System MUST preserve source-backed quality and publication gates;
  cost improvements cannot justify lower precision or fabricated evidence.
- **VC-004**: System MUST enforce policy, credential, prompt-injection, privacy,
  retention, cache invalidation, recovery, and operator visibility rules.
- **VC-005**: System MUST define benchmark, negative, replay, stability, and
  import-boundary tests before implementation.

### Key Entities

- **OptimizationBenchmarkManifest**: Corpus, baselines, expected metrics,
  thresholds, source policies, and required lower reports.
- **OptimizationMetricSlice**: Metrics by site, pattern, adapter, schema, field,
  output type, acquisition mode, and ranking profile.
- **DriftRecoveryEvaluation**: Seeded and observed failures, recovery attempts,
  validation results, rollback/review refs, and unsafe-bypass checks.
- **OptimizationReleaseGateReport**: Aggregate pass/needs-review/fail decision
  with blockers and false-ready guards.

### Non-Goals

- This spec does not weaken 073 quality thresholds or 074 operations gates.
- This spec does not hide blocked or source-limited sites behind aggregate
  success.
- This spec does not authorize CAPTCHA solving, stealth browser operation,
  proxy rotation, WAF evasion, or robots/terms bypass.

## Success Criteria

- **SC-001**: Optimization release gate ingests passing reports from specs
  081-085 or blocks with missing-lower-gate diagnostics.
- **SC-002**: Optimized corpus shows no precision regression and meets target
  improvements for duplicate rate, cost per successful result, and model/browser
  usage compared with baseline.
- **SC-003**: Seeded repair cases reach at least 0.80 repair success for
  repairable cases, unsafe bypass rate equals 0, and unresolved critical repair
  rate equals 0.
- **SC-004**: Every metric and regression record carries corpus, artifact,
  policy, command/event/outbox, and replay refs.
- **SC-005**: Negative fixtures fail for stale cache reuse, hidden dead letters,
  missing lower reports, cost/SLO violation, unsafe recovery, low quality
  metrics, source-limited fabrication, and replay gaps.

## Assumptions

- Existing specs 064, 073, and 074 remain authoritative quality and operations
  baselines.
- Baseline and optimized runs may initially use deterministic/local corpora
  before live public corpus evidence is added.

## Implementation Closure

- Materialized in `OptimizationMetricSlice`, `CrawlerOptimizationReport`,
  `CrawlerOptimizationManifest`, `CrawlerOptimizationArchitectureSpec`, and
  `AlgorithmRecommendation`.
- Implemented the aggregate optimization gate, negative fixture mapping, replay
  checks, and CLI output surface in `src/veracrawl/benchmarks/`,
  `src/veracrawl/review_replay/`, and `src/veracrawl/cli/`.
- Validated by success and negative fixtures for missing frontier score,
  LLM-as-evidence, unsafe recovery, ranking quality regression, and missing
  replay refs.
