# Feature Specification: VeraCrawl Source Coverage Adapter Operational Gate

**Feature Branch**: `026-source-coverage-adapter-operational-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Source Coverage Adapter Operational Gate：在 source acquisition、network/browser acquisition、security/privacy lifecycle 與 operational infrastructure gates 之上，實作 source-adapter-owned operational gate，證明 HTTP、sitemap、RSS/feed、browser snapshot、authorized session、API-like source、document source、file import、manual seed、prior snapshot adapters 都能映射到 VeraCrawl canonical SourceAdapterSpec、SourceAdapterResult、FetchAttempt、PageSnapshot、BrowserInteractionStep、CredentialUseAudit、DocumentArtifact、CommandResult、policy、observability、security/privacy、replay refs；core 不得直接耦合 browser library、HTTP client、document parser、credential vault SDK、API client、storage/queue/model/provider/agent framework SDK；不得把 adapter-native state、raw secrets、untrusted browser side effects 或 source-specific hacks 當 canonical state；缺少 live runtime/credential/parser/browser/API endpoint 時必須 needs_review，不得假裝 operational pass；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper。"

## Constitution Alignment

- **General-purpose crawler impact**: This gate proves broad target source coverage without hard-coding a single website, page shape, credential mode, source pattern, parser, or browser/runtime choice.
- **Target/V1 boundary**: This is target architecture work after `004`, `005`, `023`, `024`, and `025`. It advances the `Browser, document, authorized session, and API-like source adapters` step in `docs/10-target-implementation-design.md`.
- **Evidence and replay impact**: Adds source coverage reports tying `SourceAdapterSpec`, `SourceAdapterResult`, natural result refs, fetch/browser/document/session/API refs, command result, policy, observability, security/privacy, and replay refs into one conformance result.
- **Safety and policy impact**: Raw secrets, adapter-native state, untrusted browser side effects, and source-specific hacks cannot become canonical. Missing live runtime/credential/parser/browser/API endpoint returns `needs_review`.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`.

## User Scenarios & Testing

### User Story 1 - Complete Target Source Adapter Mapping (Priority: P1)

An operator can run a deterministic source coverage gate and prove all target source adapter families map to canonical VeraCrawl contracts.

**Independent Test**: Run `source-coverage-adapter-success`; it passes only when HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot adapters all produce required canonical refs.

**Acceptance Scenarios**:

1. **Given** adapter-owned source coverage descriptors, **When** the gate runs, **Then** the report is `pass` with required refs for every target adapter family.
2. **Given** a non-fetch adapter such as manual seed or prior snapshot, **When** the gate validates it, **Then** it accepts adapter-native result refs but does not require fake `FetchAttempt` refs.

---

### User Story 2 - Missing Live Source Runtime Needs Review (Priority: P2)

An operator can distinguish contract coverage from real runtime availability for browser, document parser, credential/session, API endpoint, or source runtime.

**Independent Test**: Run `source-coverage-adapter-runtime-unavailable`; it returns `needs_review` with contract-only and missing-runtime refs.

**Acceptance Scenarios**:

1. **Given** no live browser/parser/session/API/runtime refs, **When** the gate runs, **Then** it returns `needs_review`.
2. **Given** only deterministic contract descriptors, **When** live operational pass is requested, **Then** the gate does not claim operational pass without runtime refs.

---

### User Story 3 - Unsafe Or Incomplete Source Mapping Fails (Priority: P3)

The gate fails when adapters leak raw secrets, persist adapter-native state as canonical state, omit required browser/document/session/API/replay/security refs, or report unsafe browser side effects.

**Independent Test**: Run negative fixtures for native-state canonicalization, raw secret leak, missing browser refs, missing credential audit, missing document artifact, missing API payload, missing replay refs, unsafe browser side effect, and unsupported adapter.

**Acceptance Scenarios**:

1. **Given** an authorized session adapter exposes raw secret material, **When** the gate validates it, **Then** the report fails.
2. **Given** a browser snapshot adapter reports an unsafe side effect, **When** the gate validates it, **Then** the report fails.
3. **Given** a document or API-like adapter omits natural result refs, **When** the gate validates it, **Then** the report fails.

### Edge Cases

- Manual seed and prior snapshot are non-content adapters; they require `SourceAdapterResult` and natural result refs, not fake fetch/page snapshot refs.
- Browser snapshot adapters require `BrowserInteractionStep` and `PageSnapshot` refs.
- Authorized session adapters require `CredentialUseAudit` refs and must not expose raw secrets.
- API-like adapters require API payload refs.
- Document and file adapters require document artifact refs.
- Missing live runtime refs return `needs_review`; unsafe or incomplete canonical refs fail.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define source coverage execution and gate report contracts.
- **FR-002**: System MUST expose a repeatable `veracrawl-source-coverage` fixture runner.
- **FR-003**: System MUST support HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot through one coverage contract.
- **FR-004**: System MUST keep core independent of browser libraries, HTTP clients, document parsers, credential vault SDKs, API clients, storage/queue/model/provider/agent framework SDKs, and site-specific scraper modules.
- **FR-005**: Passing reports MUST include source adapter spec/result refs, natural result refs, command, policy, observability, security/privacy, replay, event cursor, and outbox refs.
- **FR-006**: Adapter-specific pass requirements MUST require browser refs for browser snapshot, credential audit refs for authorized session, API payload refs for API-like source, and document artifact refs for document/file adapters.
- **FR-007**: Missing live runtime/credential/parser/browser/API endpoint refs MUST return `needs_review` and MUST NOT be coerced to pass.
- **FR-008**: Raw secrets, adapter-native state, untrusted browser side effects, and source-specific hacks MUST NOT be canonical state.
- **FR-009**: Negative source coverage scenarios MUST fail deterministically for native-state canonicalization, raw secret leak, missing browser refs, missing credential audit, missing document artifact, missing API payload, missing replay refs, unsafe browser side effect, and unsupported adapter.
- **FR-010**: CLI source coverage loading MUST be dynamic and adapter-owned.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid source-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST register affected contracts, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST preserve evidence/publication boundaries; source adapter output is not a published output by itself.
- **VC-004**: System MUST preserve credential, browser, prompt-injection, privacy lifecycle, observability, and replay boundaries.
- **VC-005**: System MUST define fixture/oracle, negative, replay, import-boundary, and acceptance tests before implementation.

### Key Entities

- **SourceCoverageAdapterExecutionRecord**: Per-adapter execution record tying adapter type, natural result type, source result, fetch/browser/session/document/API refs, command, policy, observability, security/privacy, runtime/contract adapter, diagnostic native state, and replay refs.
- **SourceCoverageAdapterReport**: Gate-level result aggregating all target source adapter families and determining pass/fail/needs-review.
- **SourceCoverageAdapterFixtureManifest**: Fixture manifest describing expected completion result and failure type for source coverage tests.

### Non-Goals

- This feature does not implement production JavaScript rendering, production credential vaulting, production document parsing, or external API crawling.
- This feature does not implement CAPTCHA solving, paywall bypass, login-wall circumvention, WAF evasion, stealth automation, credential theft, or source authorization bypass.
- This feature does not claim managed browser fleet, managed vault, parser farm, production source runtime, production export, or production scale readiness.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `source-coverage-adapter-success` produces `pass` with all required adapter refs.
- **SC-002**: `source-coverage-adapter-runtime-unavailable` produces `needs_review`.
- **SC-003**: Negative source coverage fixtures produce `fail` with expected failure types.
- **SC-004**: Import-boundary tests prove core packages do not statically import concrete source/browser/parser/vault/API SDKs.
- **SC-005**: Contract registry validation includes source coverage contracts, command types, event types, fixture registrations, and target area coverage.
- **SC-006**: Full test suite and Docker-backed live operational gates remain passing after implementation.

## Assumptions

- Deterministic adapter-owned contract adapters are sufficient to prove canonical mapping without external websites, browsers, credentials, parsers, or API endpoints.
- Live runtime integration remains `needs_review` unless explicit live runtime refs are supplied by future adapter specs.
