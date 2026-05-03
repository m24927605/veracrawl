# Feature Specification: Expanded Real-World Public Corpus Benchmark

**Feature Branch**: `058-expanded-real-world-corpus-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Expand VeraCrawl real public website validation beyond the 4-site smoke corpus.

## Constitution Alignment

- **General-purpose crawler impact**: Builds a diverse public corpus covering
  many website/source patterns instead of a single target or hand-coded scraper.
- **Target/V1 boundary**: Production quality validation after specs 055 and 056;
  it does not claim production quality without later specs 059-064.
- **Evidence and replay impact**: Requires policy decisions, network/source
  observations, artifacts, content hashes, canonical URLs, observation oracles,
  command/event/outbox refs, and replay refs for every target.
- **Safety and policy impact**: Only manifest-declared, allowlisted, low-impact,
  read-only public targets are allowed. Robots, origin scope, rate budgets,
  private-network denial, and drift reporting are mandatory.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `specs/055-real-world-benchmark-corpus/spec.md`,
  `specs/056-real-world-ai-agent-benchmark/spec.md`, and
  `specs/057-production-quality-benchmark-roadmap/spec.md`.

## User Scenarios & Testing

### User Story 1 - Run Quality-Tier Public Corpus (Priority: P1)

An operator can run one benchmark command against a manifest-declared public
quality corpus and receive a report proving broad public target coverage.

**Independent Test**: Run `veracrawl-real-quality-corpus run
tests/fixtures/real-world-quality-corpus --profile quality --out
.veracrawl-real-runs/real-world-quality-corpus` and verify a pass report.

**Acceptance Scenarios**:

1. **Given** a quality corpus manifest, **When** the benchmark runs, **Then** at
   least 40 public targets across at least 15 public origins are fetched or
   explicitly reported as policy/network drift.
2. **Given** a passing target, **When** its record is inspected, **Then** it has
   policy, observation, artifact, content hash, command/event/outbox, and replay
   refs.

### User Story 2 - Measure Website Pattern Coverage (Priority: P2)

Maintainers can see which website/source patterns are covered and which gaps
remain.

**Independent Test**: Validate the corpus coverage report against pattern
oracles.

**Acceptance Scenarios**:

1. **Given** a passing quality corpus, **When** pattern coverage is computed,
   **Then** at least 10 pattern families are represented, including static page,
   listing, detail, pagination, table, API/JSON, feed/sitemap/document, canonical
   redirect, sparse page, and error/empty-safe targets.
2. **Given** a pattern family with no passing target, **When** validation runs,
   **Then** the benchmark fails or returns `needs_review` with a typed gap.

### User Story 3 - Handle Public Drift Honestly (Priority: P3)

External website drift must not be hidden as success.

**Independent Test**: Run negative drift fixtures for changed status, content
type, required fragment, robots denial, and timeout.

**Acceptance Scenarios**:

1. **Given** a target whose oracle no longer matches, **When** the benchmark
   runs, **Then** it emits a typed drift diagnostic and does not count the target
   as passing.
2. **Given** robots or scope denial, **When** the run executes, **Then** the
   target is skipped or failed according to policy without attempting bypass.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `RealWorldQualityCorpusManifest`,
  `RealWorldQualityTargetSpec`, `RealWorldQualitySiteObservation`, and
  `RealWorldQualityCorpusReport` contracts.
- **FR-002**: System MUST support `smoke`, `quality`, and `release` corpus
  profiles. `quality` MUST require at least 40 targets, 15 origins, and 10
  pattern families.
- **FR-003**: System MUST record per-origin request budgets, robots results,
  private-network denial checks, canonical URL refs, artifacts, content hashes,
  and replay refs.
- **FR-004**: System MUST distinguish pass, policy-denied, network-unavailable,
  oracle-drift, and needs-review outcomes.
- **FR-005**: System MUST NOT count policy-denied, network-unavailable, or drift
  targets as passing.
- **FR-006**: System MUST write deterministic JSON reports and fixture oracles
  for corpus, target, pattern, policy, drift, and replay validation.

### VeraCrawl Contract Requirements

- **VC-001**: Preserve source-adapter abstraction and avoid site-specific parser
  behavior.
- **VC-002**: Register owner services, commands, events, typed failures, policy
  decisions, and replay refs for quality corpus runs.
- **VC-003**: Source observations may seed later evidence; no extraction output
  is published by this spec.
- **VC-004**: Enforce origin allowlists, robots, rate budgets, private-network
  denial, retention, and artifact redaction policy.
- **VC-005**: Include fixture/oracle, negative, replay, registry, focused, full,
  Docker-backed, and live public validation tasks before completion.

### Key Entities

- **RealWorldQualityCorpusManifest**: Declares public targets, origins, pattern
  labels, profile thresholds, rate budgets, and oracle files.
- **RealWorldQualitySiteObservation**: One target observation with policy,
  network/source, artifact, hash, oracle, and replay refs.
- **RealWorldQualityCorpusReport**: Aggregate coverage, pass/fail/needs-review,
  drift, policy, and replay report.

### Non-Goals

- This spec does not implement browser rendering, deep crawl frontier expansion,
  field-level extraction, precision/recall, repair metrics, or final quality
  release.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft,
  login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy
  tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

- **SC-001**: Quality profile passes only with at least 40 public targets, 15
  origins, and 10 pattern families.
- **SC-002**: 100% of passing targets have policy, artifact, content hash,
  command/event/outbox, and replay refs.
- **SC-003**: Drift, robots denial, scope denial, timeout, content mismatch, and
  replay gaps fail with typed diagnostics.
- **SC-004**: Ruff, mypy, registry validation, focused tests, full pytest,
  Docker-backed pytest, and one live quality corpus run are recorded in
  `tasks.md`.

## Assumptions

- Public targets are limited to stable, low-impact sites with conservative rate
  budgets.
- Corpus manifests may be refreshed by future amendments, but target removals
  must leave an audit trail and cannot lower coverage thresholds silently.
