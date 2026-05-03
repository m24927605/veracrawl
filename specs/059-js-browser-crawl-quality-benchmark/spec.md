# Feature Specification: JavaScript Browser Crawl Quality Benchmark

**Feature Branch**: `059-js-browser-crawl-quality-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Prove JavaScript/browser crawl capability through measurable quality gains.

## Constitution Alignment

- **General-purpose crawler impact**: Adds browser rendering validation for
  general JS-dependent sites without domain-specific scraping rules.
- **Target/V1 boundary**: Quality benchmark after browser snapshot runtime and
  expanded real-world corpus; it does not complete deep crawl or extraction
  quality by itself.
- **Evidence and replay impact**: Requires DOM, screenshot, network, console,
  timing, artifact hash, source anchor, model/agent trace where AI is used,
  command/event/outbox, and replay refs.
- **Safety and policy impact**: Browser runs must be sandboxed, read-only,
  rate-budgeted, prompt-taint aware, egress controlled, and robots/scope gated.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`,
  `specs/043-browser-snapshot-runtime/spec.md`,
  `specs/056-real-world-ai-agent-benchmark/spec.md`, and
  `specs/058-expanded-real-world-corpus-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Detect Browser-Required Targets (Priority: P1)

An operator can run a browser quality benchmark and see which targets require
browser rendering because static HTTP is insufficient.

**Independent Test**: Run `veracrawl-browser-quality-benchmark run
tests/fixtures/browser-quality-corpus --profile quality --out
.veracrawl-real-runs/browser-quality-corpus`.

**Acceptance Scenarios**:

1. **Given** a JS-required target, **When** HTTP-only content misses required
   oracle content, **Then** browser rendering is attempted only if policy and
   budget allow it.
2. **Given** a successful browser render, **When** its report is inspected,
   **Then** DOM/screenshot/network/console/timing artifacts and source anchors
   exist.

### User Story 2 - Compare HTTP-Only And Browser Quality (Priority: P2)

Maintainers can prove browser rendering improved crawl evidence instead of only
adding cost.

**Independent Test**: Validate differential quality reports for HTTP-only versus
browser-rendered observations.

**Acceptance Scenarios**:

1. **Given** both HTTP-only and browser observations, **When** quality deltas are
   computed, **Then** the report shows which oracle fragments, links, structured
   data, or anchors were recovered only through browser rendering.
2. **Given** no quality improvement, **When** browser cost exceeds budget,
   **Then** the benchmark records a budget/benefit diagnostic.

### User Story 3 - Block Unsafe Browser Behavior (Priority: P3)

Unsafe browser actions must fail visibly.

**Independent Test**: Negative fixtures cover prompt-tainted page instructions,
egress denial, unsafe clicks/forms, budget exhaustion, missing screenshot, and
replay mismatch.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define browser quality target specs, render attempts,
  differential observations, and browser quality reports.
- **FR-002**: System MUST run HTTP-only observation before browser fallback so
  quality gain can be measured.
- **FR-003**: System MUST require DOM snapshot, screenshot, network trace,
  console log, timing, content hash, source anchor, policy, command/event/outbox,
  and replay refs for every passing browser observation.
- **FR-004**: System MUST record browser cost units, wall time, network request
  count, blocked request count, and budget refs.
- **FR-005**: System MUST isolate browser adapters from core and preserve import
  boundaries.
- **FR-006**: System MUST fail unsafe actions, egress denial, prompt-taint
  bypass, missing artifacts, missing anchors, budget exhaustion, and replay gaps.

### VeraCrawl Contract Requirements

- **VC-001**: Browser logic remains behind source/browser adapter ports.
- **VC-002**: Commands, events, owner services, typed results, policy decisions,
  and replay refs are mandatory for render attempts.
- **VC-003**: Browser artifacts may become source evidence only through source
  anchors and content hashes; screenshots alone are not enough.
- **VC-004**: Prompt-injection, sandbox, egress, credential, privacy, and
  retention rules must be explicit.
- **VC-005**: Include browser negative tests, replay tests, import-boundary
  tests, and live public browser validation before completion.

### Key Entities

- **BrowserQualityTargetSpec**: Declares the target URL, HTTP-only oracle,
  browser-required oracle, budget, and allowed browser actions.
- **BrowserQualityObservation**: Captures HTTP-only and browser-rendered
  evidence with artifacts, anchors, cost, and policy refs.
- **BrowserQualityReport**: Aggregates recovered content, quality deltas,
  budgets, failures, and replay status.

### Non-Goals

- This spec does not implement credentialed browsing, CAPTCHA solving, stealth
  automation, arbitrary clicking, form submission, or anti-bot evasion.
- This spec does not claim multi-page crawl or field extraction quality.

## Success Criteria

- **SC-001**: At least 8 browser-required targets pass with browser-only
  recovered oracle evidence and artifact refs.
- **SC-002**: 100% of passing browser observations have DOM, screenshot,
  network, console, timing, hash, anchor, policy, and replay refs.
- **SC-003**: Unsafe browser action, prompt-taint bypass, missing artifact,
  budget exhaustion, and replay mismatch fail with typed diagnostics.
- **SC-004**: Validation results are recorded in `tasks.md`, including focused,
  full, Docker-backed, and live browser benchmark runs.

## Assumptions

- Browser validation uses conservative read-only interactions and may combine
  stable public targets with local JS fixtures for deterministic negative cases.
