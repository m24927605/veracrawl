# Feature Specification: Structured Source Adapters Runtime

**Feature Branch**: `042-structured-source-adapters-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Constitution Alignment

- **General-purpose crawler impact**: Structured source adapters support sitemap,
  RSS/feed, API-like JSON, document, and file-import source families across
  websites and data domains. They do not encode a single domain, selector set,
  or output schema.
- **Target/V1 boundary**: This activates roadmap row 042 after row 041 live HTTP
  acquisition. It proves non-browser structured source acquisition behind source
  ports before row 043 browser and row 045 normalization/site understanding.
- **Evidence and replay impact**: Passing structured adapter records must expose
  source adapter result refs, raw artifacts, parsed natural output refs, evidence
  seed refs, content hashes, command refs, event cursor refs, outbox refs, and
  replay refs.
- **Safety and policy impact**: Policy denial, malformed structured source,
  unsupported adapter, and replay mismatch fail with typed diagnostics.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## User Stories & Testing

### User Story 1 - Acquire Structured Source Families (Priority: P1)

As a crawl runtime owner, I need sitemap, RSS/feed, API-like JSON, document, and
file-import sources to execute through source adapter boundaries and emit
replayable records.

**Independent Test**: Run `veracrawl-structured-source run tests/fixtures/structured-source-adapters-success --profile target --out .veracrawl-test-runs/structured-source-adapters-success`; it passes only when all five structured adapter types produce adapter result, artifact, evidence seed, policy, command/event/outbox, and replay refs.

### User Story 2 - Preserve Adapter-Native Semantics Without Coupling Core (Priority: P2)

As a reviewer, I need sitemap/RSS discovered URLs, API payload refs, document
artifact refs, and file artifact refs to be visible without making core depend
on parser or filesystem implementation details.

**Independent Test**: The success report exposes discovered URL refs, API payload
refs, document artifact refs, file artifact refs, and content hash refs while
`veracrawl.fetch.structured_source` has no concrete adapter imports.

### User Story 3 - Reject Unsafe Or Fake Structured Acquisition (Priority: P3)

As a Staff reviewer, I need malformed structured inputs, policy-denied source
families, unsupported adapters, and replay mismatches to fail explicitly.

**Independent Test**: Negative fixtures for policy denied, malformed source,
unsupported adapter, and replay mismatch fail with typed
`StructuredSourceAdapterFailureType` values.

## Requirements

- **FR-001**: System MUST define structured source adapter runtime contracts and fixture manifests.
- **FR-002**: System MUST expose `veracrawl-structured-source` CLI fixtures.
- **FR-003**: System MUST support sitemap, RSS/feed, API-like JSON, document, and file-import adapter types.
- **FR-004**: System MUST execute structured source acquisition through source adapter ports; core MUST NOT parse fixture files directly.
- **FR-005**: Passing records MUST include source adapter result refs, natural output refs, artifact refs, evidence seed refs, content hash refs, policy refs, command refs, event cursor refs, outbox refs, and replay refs.
- **FR-006**: Sitemap/RSS records MUST include discovered URL refs.
- **FR-007**: API-like records MUST include API payload refs.
- **FR-008**: Document records MUST include document artifact refs.
- **FR-009**: File-import records MUST include file artifact refs.
- **FR-010**: Policy-denied, malformed, unsupported, and replay-mismatch cases MUST fail with typed diagnostics.
- **FR-011**: System MUST register contracts, commands, events, fixture oracles, and target area coverage for `structured_source_adapters_runtime`.

## Key Entities

- **StructuredSourceAdapterRecord**: Per-adapter proof of structured source
  acquisition and parsed natural output refs.
- **StructuredSourceAdaptersRuntimeReport**: Aggregate report proving all
  required structured source families.
- **StructuredSourceAdaptersFixtureManifest**: Fixture expectation contract.

## Non-Goals

- Does not implement browser rendering.
- Does not implement credentialed sessions.
- Does not normalize/extract/publish structured outputs.
- Does not claim external website benchmark or production worker fleet readiness.

## Success Criteria

- **SC-001**: Success fixture passes with all five structured adapter families.
- **SC-002**: Sitemaps/RSS expose discovered URL refs; API/document/file expose family-specific refs.
- **SC-003**: Negative fixtures fail with typed diagnostics and no false pass.
- **SC-004**: Registry validation passes and `structured_source_adapters_runtime` is materialized.
- **SC-005**: Focused tests, CLI loop, ruff, mypy, full non-Docker, and Docker-backed gates pass.
