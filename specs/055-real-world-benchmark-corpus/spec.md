# Feature Specification: Real-World Benchmark Corpus Gate

**Feature Branch**: `055-real-world-benchmark-corpus`  
**Created**: 2026-05-03  
**Status**: Draft  
**Input**: User request: "go" after defining the real crawl tests needed to prove production-grade crawler capability.

## Constitution Alignment

- **General-purpose crawler impact**: Adds a reusable real-world benchmark corpus gate that validates authorized public websites through generic HTTP acquisition, observation, policy, artifact, and replay checks. The gate must not hard-code a single website scraper or extraction pipeline.
- **Target/V1 boundary**: Target architecture validation work that supplements, but does not replace, deterministic fixture/oracle acceptance in `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Requires live HTTP reports, artifacts, content hashes, canonical URL refs, source observation refs, command/event/outbox refs, replay refs, and benchmark observation refs before a real-world corpus pass.
- **Safety and policy impact**: Enforces explicit corpus allowlists, read-only GET requests, private-network denial, same-origin robots preflight, rate/budget fields, and typed failures for robots denial, scope denial, observation mismatch, missing evidence refs, and replay mismatch.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `specs/038-production-runtime-closure/spec.md`, and `specs/054-production-benchmark-release-gate/spec.md`.

## User Scenarios & Testing

### User Story 1 - Run An Authorized Public Corpus (Priority: P1)

An operator can run one command against a declared real-world corpus of public, authorized URLs and receive a pass/fail report showing which sites were fetched, which observations matched, and which canonical refs were produced.

**Why this priority**: A single-page ad hoc curl-style test cannot prove production readiness. The first useful real-world proof is a repeatable, manifest-driven corpus gate.

**Independent Test**: Run `veracrawl-real-benchmark run tests/fixtures/real-world-public-corpus --profile target --out .veracrawl-real-runs/real-world-public-corpus` and verify a `RealWorldBenchmarkRunReport` with per-site observations, live HTTP refs, artifact refs, command/event/outbox refs, and replay refs.

**Acceptance Scenarios**:

1. **Given** a corpus manifest with four authorized public targets, **When** the runner executes within the declared allowlist, **Then** every target returns the expected status/content observations and the aggregate report passes.
2. **Given** a target response whose title, body, content type, or minimum size does not match its oracle, **When** the runner evaluates observations, **Then** the corpus report fails with typed observation mismatch diagnostics.

### User Story 2 - Enforce External Crawl Safety (Priority: P2)

An operator can trust that a real-world benchmark does not silently leave its declared scope or fetch private/internal URLs.

**Why this priority**: Real websites are inherently less controlled than fixtures. Production-grade validation must prove scope, robots, and private-network gates before treating any result as evidence.

**Independent Test**: Run negative unit and integration tests for private-network URLs, off-allowlist origins, robots-denied paths, missing robots preflight, and unsafe manifest shapes.

**Acceptance Scenarios**:

1. **Given** a corpus entry pointing at localhost, private IPs, or an undeclared origin, **When** the runner starts, **Then** it fails before acquisition with a typed safety failure.
2. **Given** robots policy disallows the target path, **When** the runner performs robots preflight, **Then** it does not fetch the target page and records a typed robots denial.

### User Story 3 - Publish Replayable Benchmark Evidence (Priority: P3)

An operator can inspect saved benchmark outputs and replay-critical refs after a real-world run.

**Why this priority**: Production-grade claims require auditability. A real external response is useful only when the evidence and replay surface is persisted and checkable.

**Independent Test**: Validate `run_report.json`, `site_observations.json`, `summary.json`, and state files under the output directory; run replay validation helpers over the aggregate report.

**Acceptance Scenarios**:

1. **Given** a successful corpus run, **When** saved outputs are loaded, **Then** every site has live HTTP report refs, network response refs, artifact refs, content hash refs, observation refs, command/event/outbox refs, and replay refs.
2. **Given** a report missing replay or artifact refs, **When** replay validation runs, **Then** the report fails before it can be counted as production validation.

## Edge Cases

- robots.txt returns 404 for a public sandbox site: treat as allowed only when the manifest explicitly permits the status code and the target origin is allowlisted.
- robots.txt returns 200 and disallows the target path: fail before target fetch.
- DNS, TLS, timeout, or transient network errors: return non-pass with `real_world_network_unavailable`, not a false production failure or pass.
- Target page content changes: fail with typed observation mismatch unless the manifest declares explicit tolerance.
- Redirects remain in-scope only when the final URL origin is also allowlisted.
- Private network, localhost, link-local, multicast, or unspecified IP targets are denied even if a manifest tries to include them.
- Prompt-injection text observed on a page must remain page content only; this spec does not pass page text into model prompts.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `RealWorldBenchmarkCorpusManifest`, `RealWorldBenchmarkSiteSpec`, `RealWorldBenchmarkSiteObservation`, and `RealWorldBenchmarkRunReport` contracts.
- **FR-002**: System MUST run real-world benchmarks from a manifest, not from hard-coded site-specific scraper logic.
- **FR-003**: System MUST enforce explicit allowed origins, read-only HTTP GET, positive timeout/size/rate budgets, and private-network denial before acquisition.
- **FR-004**: System MUST perform same-origin robots preflight for every real target and MUST block disallowed paths.
- **FR-005**: System MUST execute target acquisition through `NetworkSourceAdapterPort` and existing live HTTP runtime contracts.
- **FR-006**: System MUST evaluate expected status code, content type, minimum body size, required title fragments, required body fragments, and regex count observations declared by the corpus.
- **FR-007**: Passing aggregate reports MUST include site observation refs, live HTTP report refs, network response refs, source observation refs, artifact refs, content hash refs, canonical URL refs, policy refs, command/event/outbox refs, and replay refs.
- **FR-008**: Non-pass aggregate reports MUST include a `RealWorldBenchmarkFailureType`, failure refs, missing ref fields, and diagnostics.
- **FR-009**: CLI output MUST write deterministic JSON reports under the requested output directory and print a machine-readable summary.
- **FR-010**: Test suite MUST include contract, registry, import-boundary, unit, replay, fixture/oracle, negative safety, and live-run smoke validation.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST register owner services, commands, events, typed results, policy decisions, fixture oracles, and replay refs for the real-world benchmark gate.
- **VC-003**: System MUST not publish extracted outputs from real websites in this spec; it validates acquisition/evidence/replay readiness for the corpus.
- **VC-004**: System MUST define source scope, robots, private-network, prompt-injection, credential, and privacy boundaries even though this spec does not use credentials or browser execution.
- **VC-005**: System MUST define deterministic tests and explicit live-run validation before the gate can be reported complete.

### Key Entities

- **RealWorldBenchmarkCorpusManifest**: Declares corpus id, profile refs, sites, allowed origins, rate/budget settings, expected aggregate status, and negative-case expectations.
- **RealWorldBenchmarkSiteSpec**: Declares one authorized public URL, robots URL, expected observations, and safety budgets.
- **RealWorldBenchmarkSiteObservation**: Records one live target result, matched observations, response metadata, and canonical refs.
- **RealWorldBenchmarkRunReport**: Aggregates all site observations and pass/fail diagnostics for the real-world corpus.

### Non-Goals

- This spec does not claim full production crawler readiness by itself; it supplements deterministic release gates with a real external corpus gate.
- This spec does not implement multi-page frontier expansion, browser rendering, credentialed sessions, extraction publication, export delivery, or long-running distributed load tests against external websites.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A declared real-world public corpus of at least four URLs runs through one CLI command and produces a passing aggregate report when the external sites match their oracles.
- **SC-002**: 100% of passing site observations include live HTTP, network response, source observation, artifact, content hash, canonical URL, command, event cursor, outbox, policy, and replay refs.
- **SC-003**: Private-network, off-allowlist, robots-denied, observation-mismatch, missing-evidence, and replay-mismatch cases fail with typed diagnostics.
- **SC-004**: Contract registry validation includes the real-world benchmark contracts, commands, events, fixtures, and target area.
- **SC-005**: Focused tests and at least one live external corpus run complete successfully before implementation is marked done.

## Assumptions

- Public test sites used in the default corpus are low-risk educational/demo targets or standards-reserved examples: `books.toscrape.com`, `quotes.toscrape.com`, `example.com`, and `httpbin.org/json`.
- The default runner uses one GET per target plus one same-origin robots preflight per target.
- Network-backed tests are environment-dependent; deterministic unit/integration tests use injected adapters, while the live CLI run is recorded in `tasks.md` validation results.
- Real external sites can change; observation assertions are intentionally coarse enough to detect meaningful drift without pretending external content is deterministic.
