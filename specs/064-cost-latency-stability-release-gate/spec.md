# Feature Specification: Cost Latency Stability Release Gate

**Feature Branch**: `064-cost-latency-stability-release-gate`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Aggregate production crawl quality, cost, latency, and stability into a release decision.

## Constitution Alignment

- **General-purpose crawler impact**: Aggregates quality evidence across corpus,
  browser, deep crawl, field oracle, precision/recall, and repair benchmarks.
- **Target/V1 boundary**: Final production crawl quality release gate for specs
  058-063. It does not claim cloud deployment or managed operations readiness
  beyond the measured benchmark environment.
- **Evidence and replay impact**: Requires upstream benchmark report refs, cost
  metric refs, latency traces, token/call usage, retry/dead-letter refs,
  stability run refs, command/event/outbox refs, and replay refs.
- **Safety and policy impact**: A release cannot pass with policy bypass,
  unsafe repair, direct publication, LLM-as-evidence, missing replay, or
  false-ready diagnostics.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`,
  `specs/058-expanded-real-world-corpus-benchmark/spec.md`,
  `specs/059-js-browser-crawl-quality-benchmark/spec.md`,
  `specs/060-multi-page-deep-crawl-frontier-benchmark/spec.md`,
  `specs/061-field-level-oracle-extraction-benchmark/spec.md`,
  `specs/062-precision-recall-quality-benchmark/spec.md`, and
  `specs/063-repair-success-rate-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Produce Quality Release Decision (Priority: P1)

An operator can run one release gate command and receive a pass/fail/needs-review
decision backed by all production crawl quality reports.

**Independent Test**: Run `veracrawl-quality-release-gate run
tests/fixtures/quality-release-gate --profile quality --out
.veracrawl-real-runs/quality-release-gate`.

**Acceptance Scenarios**:

1. **Given** passing reports from specs 058-063, **When** the release gate runs,
   **Then** it emits a pass only if every required report, metric, SLO, policy,
   and replay ref exists.
2. **Given** any missing or failed upstream report, **When** the gate runs,
   **Then** it emits fail or needs-review and does not claim production quality.

### User Story 2 - Enforce Cost And Latency Budgets (Priority: P2)

Maintainers can see request counts, browser time, model calls, token usage,
estimated provider cost, wall-clock latency, queue latency, retry count, and
throughput.

**Independent Test**: Negative fixtures exceed token, call, request, browser,
retry, p95 latency, and total wall-clock budgets.

### User Story 3 - Prove Multi-Run Stability (Priority: P3)

The release gate proves quality is stable across repeated runs, not a one-off
success.

**Independent Test**: Run three stability fixtures and validate report digests,
metric variance, typed drift, and replay consistency.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define quality release manifests, benchmark input
  report refs, SLO/cost budgets, stability run records, and quality release
  decision reports.
- **FR-002**: System MUST require reports from specs 058, 059, 060, 061, 062,
  and 063 before a quality release pass is possible.
- **FR-003**: System MUST record request count, browser render count/time,
  model call count, token usage, provider response refs, retry/dead-letter
  counts, wall-clock latency, queue latency, throughput, and estimated cost refs.
- **FR-004**: Default quality profile MUST require three consecutive comparable
  runs with no new critical typed failures, replay pass rate 100%, no false-ready
  status, and stable published-output digests for deterministic fixtures.
- **FR-005**: Default quality profile MUST block pass when precision/recall or
  repair thresholds from specs 062 and 063 fail.
- **FR-006**: System MUST fail any release decision that omits cost/latency
  metrics, hides provider/model usage, lacks replay refs, or reports pass with
  upstream failures.

### VeraCrawl Contract Requirements

- **VC-001**: Release gates aggregate general crawler quality; they must not be
  tuned to one corpus or one provider.
- **VC-002**: Release decisions must have owner-service, command, event, outbox,
  policy, typed failure, audit, and replay refs.
- **VC-003**: Publication correctness must inherit evidence and verification
  gates from upstream reports.
- **VC-004**: Cost, privacy, retention, redaction, credential, prompt-injection,
  and export/withdrawal boundaries must remain visible.
- **VC-005**: Include positive, negative, threshold, stability, replay,
  import-boundary, focused, full, Docker-backed, and real validation tasks.

### Key Entities

- **QualityReleaseManifest**: Declares required upstream reports, budgets,
  stability run count, threshold profile, and release policy.
- **CostLatencyMetricRecord**: Captures request, browser, model, queue, retry,
  throughput, latency, token, and estimated cost measurements.
- **StabilityRunRecord**: Captures repeated run identity, comparable inputs,
  report digests, drift, metric variance, and replay status.
- **QualityReleaseDecisionReport**: Final pass/fail/needs-review decision with
  all evidence, metric, policy, audit, and replay refs.

### Non-Goals

- This spec does not claim managed cloud deployment, autoscaling operations,
  full observability backend readiness, or unlimited web-scale crawling.
- It does not allow cost or latency goals to override policy, evidence,
  precision/recall, repair safety, or replay gates.

## Success Criteria

- **SC-001**: Release pass requires all reports from specs 058-063 and all
  threshold checks to pass.
- **SC-002**: Three comparable runs complete with 100% replay pass rate, no new
  critical typed failures, and stable deterministic output digests.
- **SC-003**: Cost, latency, request, browser, model call, token, retry,
  throughput, and queue metrics are present and linked to command/event/outbox
  and replay refs.
- **SC-004**: Missing upstream reports, SLO violations, metric omissions,
  replay gaps, policy bypass, direct publication, LLM-as-evidence, and false
  ready status fail with typed diagnostics.
- **SC-005**: Validation results are recorded in `tasks.md`.

## Assumptions

- Provider pricing can change, so canonical cost records store usage units and
  optional price-snapshot refs rather than hard-coding external prices.
- Stability thresholds may be tightened by future amendment but cannot be
  weakened by runtime configuration alone.
