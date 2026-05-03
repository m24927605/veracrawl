# Feature Specification: VeraCrawl Target Website Pattern Coverage Gate

**Feature Branch**: `031-website-pattern-coverage-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Target Website Pattern Coverage Gate：實作 static、sitemap/RSS/feed、listing/detail、search、non-destructive forms、JavaScript pages、authenticated sources、API-like endpoints、documents、multi-language pages、drifted sites、high-volume sites 這 12 種 target website pattern 的 deterministic benchmark fixture/oracle gate，必須證明每個 pattern 都有 source adapter refs、site model/page type refs、output/evidence/replay/policy refs、pattern-specific refs、failure oracle；不得以單站 scraper、單一 pattern demo、或 scaffold 假裝 target-complete；core 不得耦合 storage、queue、browser、HTTP client、agent framework、model SDK 或具體網站邏輯。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature proves VeraCrawl target coverage across website structures and interaction patterns instead of a single-site scraper, fixed selector set, or one-off crawl demo.
- **Target/V1 boundary**: This is target architecture coverage work for the Source Adapter, Website Pattern, And Output Coverage Profile in `docs/09-target-capability-model.md` and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Every website pattern coverage record must carry source adapter refs, source evidence refs, site model/page type refs, expected output refs, evidence coverage refs, policy refs, command/event/outbox refs, artifact/oracle refs, and replay refs before pass.
- **Safety and policy impact**: Browser, forms, authentication, API-like endpoints, drift repair, and high-volume patterns require explicit policy/safety refs. Unsafe side effects, credential leakage, private-network bypass, scaffold-only claims, and single-site assumptions fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove All Target Website Patterns (Priority: P1)

As a platform owner, I need a single deterministic gate proving that static pages, feeds, listings, search/forms, JavaScript pages, authenticated sources, APIs, documents, multilingual pages, drifted sites, and high-volume sites all have target fixture coverage.

**Why this priority**: VeraCrawl cannot claim general-purpose crawling if target coverage is proven only for simple static pages or one hand-built website.

**Independent Test**: Run `veracrawl-website-patterns run tests/fixtures/website-pattern-coverage-success --profile target --out .veracrawl-test-runs/website-pattern-coverage-success`; it emits coverage records for all 12 target website patterns and a pass report.

**Acceptance Scenarios**:

1. **Given** all 12 target patterns have source adapter, site model/page type, output, evidence, policy, oracle, command/event/outbox, and replay refs, **When** the coverage gate runs, **Then** it emits one coverage record per pattern and a pass report.
2. **Given** any target website pattern is omitted, **When** the coverage gate evaluates target completion, **Then** it fails with typed missing-pattern diagnostics.

---

### User Story 2 - Reject False Target Completion (Priority: P2)

As an architecture reviewer, I need scaffolded, single-site, single-pattern, or unsupported-pattern coverage claims to fail instead of being labeled target-complete.

**Why this priority**: A general-purpose crawler can be weakened silently if a narrow benchmark or placeholder fixture is allowed to satisfy target architecture.

**Independent Test**: Negative fixtures for `website-pattern-single-site-assumption`, `website-pattern-scaffold-only`, `website-pattern-unsupported-pattern`, and `website-pattern-missing-pattern` fail deterministically.

**Acceptance Scenarios**:

1. **Given** coverage records are tied to one concrete website or selector set, **When** the gate runs, **Then** it fails with a single-site assumption failure.
2. **Given** a fixture has manifests but no executable oracle refs, **When** the gate runs, **Then** it fails with scaffold-only diagnostics.

---

### User Story 3 - Enforce Pattern-Specific Safety And Evidence (Priority: P3)

As an operator, I need browser, forms, authenticated, API, document, drift, multilingual, and high-volume patterns to prove the refs that make those patterns safe and replayable.

**Why this priority**: A generic "pattern exists" flag is too weak for target architecture; each pattern has different safety and replay requirements.

**Independent Test**: Negative fixtures for missing source adapter, missing site model, missing output/evidence, missing pattern-specific refs, unsafe interaction, and missing replay fail with typed status.

**Acceptance Scenarios**:

1. **Given** JavaScript pages lack browser artifact refs, **When** coverage runs, **Then** the pattern-specific ref gate fails.
2. **Given** forms lack non-destructive interaction policy refs, **When** coverage runs, **Then** unsafe interaction fails before pass.
3. **Given** high-volume sites lack queue/backpressure refs, **When** coverage runs, **Then** pattern-specific refs fail.

### Edge Cases

- Live benchmark runtime refs are unavailable; report must return `needs_review`.
- One or more target patterns are omitted.
- Unsupported pattern names are supplied.
- Pattern records include fixture manifests but no executable oracles.
- Pattern records use one site, one selector set, or one adapter as a general target claim.
- Browser/forms/auth patterns lack policy, credential audit, sandbox, or redaction refs.
- Replay-critical command, event cursor, outbox, artifact hash, policy, or replay refs are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `WebsitePatternCoverageRecord`, `WebsitePatternCoverageReport`, and `WebsitePatternCoverageFixtureManifest` contracts.
- **FR-002**: System MUST define canonical target website patterns: `static`, `sitemap_rss_feed`, `listing_detail`, `search`, `non_destructive_forms`, `javascript_pages`, `authenticated_sources`, `api_like_endpoints`, `documents`, `multi_language_pages`, `drifted_sites`, and `high_volume_sites`.
- **FR-003**: System MUST require every target pattern to include source adapter refs, source evidence refs, site model refs, page type refs, output oracle refs, evidence coverage refs, policy refs, artifact oracle refs, command refs, event cursor refs, outbox refs, and replay refs before pass.
- **FR-004**: System MUST include pattern-specific required refs for feeds, listing/detail pagination/canonicalization, bounded search, non-destructive forms, browser artifacts, authenticated credential audit, API payload provenance, document artifacts, language metadata, drift repair/review, and high-volume queue/backpressure.
- **FR-005**: System MUST reject single-site assumptions, scaffold-only manifests, unsupported patterns, missing patterns, missing source adapters, missing site models, missing output/evidence, unsafe interactions, missing pattern-specific refs, and missing replay.
- **FR-006**: System MUST include a success fixture covering all 12 target website patterns.
- **FR-007**: System MUST include no-runtime and negative fixtures for every failure type listed in FR-005.
- **FR-008**: System MUST register website pattern coverage contracts, commands, events, fixtures, and target area coverage.
- **FR-009**: System MUST provide a `veracrawl-website-patterns` fixture runner that validates manifests and writes `run_report.json`.
- **FR-010**: System MUST keep core independent of concrete storage, queues, browser runtimes, HTTP clients, agent frameworks, model SDKs, export targets, and site-specific scraper logic.
- **FR-011**: System MUST document website pattern coverage usage, fixture acceptance, and non-completion boundaries without claiming production browser fleets, production external websites, or production scale completion.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **WebsitePatternCoverageRecord**: Per-pattern proof that source adapter, site model/page type, source evidence, expected output/evidence, policy, oracle, artifact, and replay refs are present.
- **WebsitePatternCoverageReport**: Operator/replay-facing report proving every target website pattern passes or identifying typed coverage failures.
- **WebsitePatternCoverageFixtureManifest**: Deterministic fixture declaration for success, needs-review, and negative website pattern scenarios.

### Non-Goals *(mandatory)*

- This feature does not implement production JavaScript browser fleets, concrete external websites, managed credential vaults, production parser farms, production queue scale, model calls, or agent framework integration.
- This feature does not make a single website, single selector set, or scaffold-only fixture valid target website pattern coverage.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Success fixture emits 12 `WebsitePatternCoverageRecord` refs and a pass report covering all target website patterns.
- **SC-002**: Pattern-specific refs are present for feeds, listing/detail, search, forms, JavaScript, authenticated, API, document, multilingual, drifted, and high-volume patterns.
- **SC-003**: Missing pattern, unsupported pattern, single-site assumption, scaffold-only, missing source adapter, missing site model, missing output/evidence, missing pattern-specific refs, unsafe interaction, and missing replay fixtures fail deterministically.
- **SC-004**: Runtime-unavailable fixture returns `needs_review`.
- **SC-005**: Registry validation includes every website pattern coverage contract, command, event, fixture, and target area coverage.
- **SC-006**: Import-boundary tests prove website pattern runtime and CLI do not import concrete storage, queue, browser, HTTP, model, agent framework, export, or scraper dependencies.
- **SC-007**: Full local website pattern fixture gate completes within 30 seconds.

## Assumptions

- Deterministic fixtures use stable refs from existing source adapter, normalize/extract, evidence/publication, browser/security, scheduler, graph, memory, and ops slices instead of external websites.
- Browser, auth, search, form, drift, and high-volume behavior is validated by contracts and fixture refs in this slice; production runtimes remain adapter- and infrastructure-owned gates.
