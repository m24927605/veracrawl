# Feature Specification: VeraCrawl Source-Backed Target Runtime

**Feature Branch**: `035-source-backed-runtime`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Build VeraCrawl Source-Backed Target Runtime: extend target crawl runtime so success and negative fixtures can read local multi-pattern source corpus files, derive output/evidence/graph/export/replay refs from actual fixture content, detect missing evidence, prompt injection, policy-denied sources, partial exports, and replay mismatches, while preserving framework-neutral AI and avoiding single-site scraper logic."

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature moves target runtime execution from synthetic refs to source-backed local corpus processing across many website patterns. It must use generic fixture descriptors and parsers, not one-site scraper logic.
- **Target/V1 boundary**: This is target architecture runtime work governed by `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`. It extends 034 without weakening target scope.
- **Evidence and replay impact**: Accepted outputs must be derived from actual local source files and linked to content hash, evidence, graph, export, command/event/outbox, policy, and replay refs.
- **Safety and policy impact**: Source corpus entries can be policy-denied, prompt-injection-tainted, missing evidence, partial export, or replay-mismatched. These conditions must block or fail with typed diagnostics instead of producing false completion.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, `AGENTS.md`, and `specs/034-target-crawl-runtime/`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crawl A Local Multi-Pattern Corpus (Priority: P1)

As an operator, I need a target runtime fixture to read actual local source files and produce verified outputs, evidence, graph, export, and replay refs from their content.

**Why this priority**: VeraCrawl must become an executable crawler, not only a deterministic ref generator.

**Independent Test**: Run `veracrawl-target-runtime run tests/fixtures/source-backed-target-success --profile target --out .veracrawl-test-runs/source-backed-target-success`; the report passes only if at least seven source-backed pattern records are derived from local files.

**Acceptance Scenarios**:

1. **Given** a local corpus containing static HTML, sitemap, listing/detail HTML, API-like JSON, document metadata HTML, drifted HTML, and JavaScript-rendered snapshot HTML, **When** the target runtime runs, **Then** it creates pattern records, output refs, evidence refs, graph refs, export refs, artifact hash refs, and replay refs derived from source file content.
2. **Given** the same source corpus is run twice, **When** replay hashes are compared, **Then** stable content-derived refs remain deterministic.

---

### User Story 2 - Detect Source-Backed Runtime Failures (Priority: P2)

As a Staff reviewer, I need source-backed fixtures to fail when content lacks evidence, contains prompt injection, violates policy, has partial export, or mismatches replay expectations.

**Why this priority**: Real source execution must not turn unsafe or incomplete content into a completion claim.

**Independent Test**: Negative fixtures for policy-denied corpus entries, prompt injection, missing evidence, partial export, and replay mismatch fail or block with typed target runtime failures.

**Acceptance Scenarios**:

1. **Given** a source file is outside approved corpus policy, **When** the runtime evaluates it, **Then** the report is `blocked` with `target_runtime_policy_denied`.
2. **Given** source content contains prompt-injection markers, **When** AI planning/extraction assistance is recorded, **Then** trusted prompt boundaries are protected and the report is `blocked`.
3. **Given** source content lacks required evidence markers, **When** completion is evaluated, **Then** the report is `failed` and no accepted output is published as complete.

---

### User Story 3 - Preserve Framework-Neutral AI And General Parsing (Priority: P3)

As a crawler engineer, I need the source-backed path to use generic parsing and VeraCrawl-owned AI recommendation records without coupling core to any framework or hardcoded website.

**Why this priority**: The implementation must strengthen the general-purpose crawler architecture, not create a hidden scraper.

**Independent Test**: Import-boundary and corpus tests prove the source-backed runner imports no concrete agent frameworks or site-specific scraper modules and extracts fields through generic descriptors.

**Acceptance Scenarios**:

1. **Given** corpus entries declare expected fields and evidence selectors, **When** extraction runs, **Then** outputs are generated by generic descriptor matching.
2. **Given** a repairable drifted page, **When** field aliases recover missing evidence, **Then** the runtime records a framework-neutral AI repair recommendation and passes.

### Edge Cases

- Corpus manifest references a missing source file.
- Source file is present but empty.
- Content hash differs from replay oracle.
- One pattern succeeds while another lacks evidence.
- JSON content contains malformed data.
- HTML source includes prompt-injection text.
- Export expectation requires a ref not produced by source-backed output.
- Drifted source uses alias field names that require repair.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow `TargetRuntimeFixtureManifest` to reference a local source corpus manifest.
- **FR-002**: System MUST define source-backed corpus contracts for corpus entries, expected fields, evidence markers, output refs, policy refs, content hashes, and pattern mapping.
- **FR-003**: System MUST read local corpus files and derive source observation refs, artifact refs, accepted output refs, evidence refs, graph refs, and replay refs from actual content and stable hashes.
- **FR-004**: System MUST support at least seven website patterns in the source-backed success corpus: static, sitemap/feed, listing/detail, API-like endpoints, documents, drifted sites, and JavaScript pages.
- **FR-005**: System MUST record framework-neutral AI recommendation refs when drift repair aliases are used.
- **FR-006**: System MUST block or fail source-backed policy-denied, prompt-injection, missing-evidence, replay-mismatch, partial-export, missing-file, and malformed-source fixtures.
- **FR-007**: System MUST keep target runtime core independent of concrete agent frameworks, model SDKs, HTTP clients, browser runtimes, storage clients, queue clients, export SDKs, UI frameworks, and site-specific scraper modules.
- **FR-008**: System MUST update docs, registry, fixtures, tests, and CLI behavior without breaking the 034 deterministic fixtures.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: Preserve general-purpose crawling and avoid site-specific scraper assumptions.
- **VC-002**: Define owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: Define evidence, verification, publication, and output manifest behavior.
- **VC-004**: Define source scope, prompt-injection, privacy lifecycle, and export behavior.
- **VC-005**: Define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities

- **TargetSourceCorpusManifest**: Local corpus declaration for source-backed target runtime fixtures.
- **TargetSourceCorpusEntry**: One source file, website pattern, expected fields, evidence markers, policy state, and replay expectation.
- **TargetSourceObservationRecord**: Content-derived observation with source path, content hash, artifact refs, evidence refs, and diagnostics.

### Non-Goals

- This feature does not crawl live Internet sites.
- This feature does not implement a concrete browser fleet, credential vault, external model provider, or external agent framework.
- This feature does not add site-specific scraper modules.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Source-backed success fixture completes with at least seven covered patterns and accepted outputs derived from source file content.
- **SC-002**: Every source-backed accepted output includes source observation refs, content-hash artifact refs, evidence refs, graph refs, policy refs, export refs, command/event/outbox refs, and replay refs.
- **SC-003**: Drift repair in source-backed success records at least one framework-neutral AI recommendation when alias evidence is used.
- **SC-004**: Negative source-backed fixtures fail or block deterministically with typed target runtime failures.
- **SC-005**: Existing 034 deterministic fixtures still pass.
- **SC-006**: Full non-Docker and Docker-backed suites pass.

## Assumptions

- Local corpus files are deterministic acceptance fixtures, not proof of live Internet production crawling.
- HTML extraction can use generic marker matching and simple metadata parsing for this phase.
- JSON extraction uses standard-library JSON parsing only.
- Source-backed execution must preserve existing target runtime fixture compatibility.
