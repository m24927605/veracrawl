# Feature Specification: Cost Latency Stability Release Gate

**Feature Branch**: `064-quality-release-gate`  
**Created**: 2026-05-04  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Aggregate quality, cost, latency, throughput, token/call usage,
retry behavior, replay completeness, and multi-run stability into the final
production crawl quality release decision.

## Constitution Alignment

- **General-purpose crawler impact**: Aggregates the whole quality benchmark
  suite rather than one site or scraper path.
- **Target/V1 boundary**: This is target architecture quality release work and
  does not weaken the general-purpose AI agent crawler architecture.
- **Evidence and replay impact**: Every release decision needs prior quality
  gate report refs, SLO metric refs, stability run refs, command/event/outbox
  refs, audit refs, and replay refs.
- **Safety and policy impact**: False-ready status, missing replay, missing
  quality reports, budget/SLO violations, and stability regressions must block
  release.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `specs/058-*` through
  `specs/063-*`, and this spec.

## User Scenarios & Testing

### User Story 1 - Aggregate Quality Release Decision (Priority: P1)

An operator can run one release gate that consumes refs for quality specs 058
through 063 and returns a release-ready or blocked decision.

**Independent Test**: Run `veracrawl-quality-release-gate run
tests/fixtures/quality-release-ready --profile quality --out
.veracrawl-test-runs/quality-release-ready`.

**Acceptance Scenarios**:

1. **Given** all six quality gate refs and stable SLO metrics, **When** the gate
   runs, **Then** the report passes with release-ready status and replay refs.
2. **Given** any prior quality gate is missing, **When** the gate runs, **Then**
   release is blocked with typed diagnostics.

### User Story 2 - Enforce Cost, Latency, Retry, And Stability (Priority: P2)

Maintainers can see total cost, p95 latency, throughput, retry rate, token/call
usage, and three-run stability before claiming production quality.

**Independent Test**: Negative fixtures violate cost, latency, retry, stability,
and run-count requirements and fail independently.

### User Story 3 - Block False Ready And Replay Gaps (Priority: P3)

The gate must fail any report that claims ready status while replay, audit,
policy, or command/event/outbox refs are missing.

**Independent Test**: Negative fixtures cover replay gap and false-ready status.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define quality release manifests, prior quality gate
  refs, stability run metrics, thresholds, and release reports.
- **FR-002**: Passing reports MUST include refs for specs 058, 059, 060, 061,
  062, and 063.
- **FR-003**: Passing reports MUST include at least three stability runs.
- **FR-004**: Passing reports MUST enforce total cost, p95 latency, retry rate,
  token/call usage, throughput, and stability thresholds.
- **FR-005**: Passing reports MUST include policy, command/event/outbox, audit,
  release decision, SLO metric, and replay refs.
- **FR-006**: Missing prior gates, cost budget violations, latency SLO
  violations, retry violations, stability regressions, insufficient runs,
  replay gaps, and false-ready status MUST fail with typed diagnostics.

### VeraCrawl Contract Requirements

- **VC-001**: The gate must aggregate general benchmark reports and must not
  encode single-site scraper assumptions.
- **VC-002**: Owner services, commands, events, policy decisions, audit refs,
  and replay refs are mandatory.
- **VC-003**: Release-ready output is a release decision only; it does not turn
  model output into source evidence.
- **VC-004**: Security, credential, prompt-injection, privacy, retention, and
  export/withdrawal boundaries remain inherited blockers from lower gates.
- **VC-005**: Include positive and negative fixtures, replay tests,
  import-boundary tests, focused/full/Docker validation, and recorded results.

### Key Entities

- **QualityReleaseGateRef**: One prior quality gate report ref and replay ref.
- **QualityReleaseStabilityRun**: One stability run with cost, latency,
  throughput, retry, token/call, and replay metrics.
- **QualityReleaseReport**: Final aggregate release decision and diagnostics.

### Non-Goals

- This spec does not bypass or rerun lower quality gates.
- This spec does not claim readiness if any required lower gate or replay ref is
  missing.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria

- **SC-001**: All six quality benchmark report refs are required for pass.
- **SC-002**: At least three stability runs are required for pass.
- **SC-003**: Cost, latency, retry, throughput, and stability thresholds block
  release when violated.
- **SC-004**: Replay and false-ready negative fixtures fail.
- **SC-005**: Validation results are recorded in `tasks.md`.

## Assumptions

- The gate consumes report refs from prior quality benchmark runs rather than
  rerunning those expensive benchmarks.
- Deterministic fixtures stand in for stable multi-run production telemetry.
