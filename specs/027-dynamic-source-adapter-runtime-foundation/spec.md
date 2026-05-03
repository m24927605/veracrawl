# Feature Specification: VeraCrawl Dynamic Source Adapter Runtime Foundation

**Feature Branch**: `027-dynamic-source-adapter-runtime-foundation`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Dynamic Source Adapter Runtime Foundation：實作 browser snapshot、document source、authorized session、API-like source、file import、manual seed、prior snapshot 的 runtime foundation，透過 ports/adapters 動態載入 deterministic/local adapters，產生 SourceAdapterResult、BrowserInteractionStep、CredentialUseAudit、DocumentArtifact、CommandResult、policy、observability、security/privacy、event/outbox、replay refs；core 不得直接耦合 browser library、HTTP client、document parser、credential vault SDK、API client、storage/queue/model/provider/agent framework SDK；缺少 live runtime/credential/parser/browser/API endpoint 時必須 needs_review，不得假裝 operational pass；不得實作成單站 scraper。"

## Constitution Alignment

- **General-purpose crawler impact**: This feature adds broad source runtime foundation without hard-coding a website, source shape, credential mode, parser, browser, API, or vertical schema.
- **Target/V1 boundary**: This is target architecture work for item 4 in `docs/10-target-implementation-design.md`: browser, document, authorized session, and API-like source adapters.
- **Evidence and replay impact**: Runtime records must tie `SourceAdapterResult`, natural output refs, browser/document/session/API/file/seed/prior refs, command refs, policy refs, event cursor refs, outbox refs, observability refs, security/privacy refs, and replay refs.
- **Safety and policy impact**: Missing live runtimes are `needs_review`; raw secrets, adapter-native canonical state, unsafe browser side effects, unsupported adapters, and missing adapter-specific refs fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`.

## User Scenarios & Testing

### User Story 1 - Dynamic Target Source Runtime Pass (Priority: P1)

An operator can run one deterministic dynamic source runtime fixture and prove HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot produce canonical runtime refs.

**Independent Test**: Run `dynamic-source-runtime-success`; it passes only when all required source adapter families produce adapter-specific runtime refs and replay refs.

**Acceptance Scenarios**:

1. **Given** adapter-owned deterministic/local runtime adapters, **When** the dynamic source runtime gate runs, **Then** the report is `pass` with all required target adapter families verified.
2. **Given** manual seed and prior snapshot adapters, **When** runtime records are validated, **Then** they emit seed/prior refs and do not fake fetch/page snapshot refs.

### User Story 2 - Missing Runtime Needs Review (Priority: P2)

An operator can distinguish deterministic contract/runtime shape from real browser/parser/session/API/source runtime availability.

**Independent Test**: Run `dynamic-source-runtime-runtime-unavailable`; it returns `needs_review` with missing runtime refs.

**Acceptance Scenarios**:

1. **Given** no live source/browser/parser/session/API runtime refs, **When** live operational pass is requested, **Then** the report is `needs_review`.
2. **Given** contract-only refs, **When** runtime completeness is evaluated, **Then** the report cannot claim pass.

### User Story 3 - Unsafe Or Incomplete Runtime Fails (Priority: P3)

The gate fails when dynamic source runtime records leak raw secrets, canonicalize adapter-native state, omit required browser/session/document/API/replay refs, report unsafe browser side effects, or use unsupported adapters.

**Independent Test**: Run negative fixtures for raw secret leak, adapter-native canonical state, missing credential audit, missing document artifact, missing API payload, missing replay, unsafe browser side effect, and unsupported adapter.

**Acceptance Scenarios**:

1. **Given** an authorized session runtime exposes raw secret material, **When** the gate validates it, **Then** the report fails.
2. **Given** browser runtime emits unsafe side effects, **When** the gate validates it, **Then** the report fails.
3. **Given** document/API runtime omits adapter-specific refs, **When** the gate validates it, **Then** the report fails.

### Edge Cases

- Non-fetch adapters must produce native refs and must not be accepted through fake `FetchAttempt` or `PageSnapshot` refs.
- Browser snapshot runtime must include a `BrowserInteractionStep` ref and a page snapshot/artifact ref.
- Authorized session runtime must include `CredentialUseAudit` and redacted replay refs, never raw secrets.
- API-like runtime must include API payload refs.
- Missing live runtime refs produce `needs_review`; unsafe or incomplete records produce `fail`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define dynamic source runtime adapter record and report contracts.
- **FR-002**: System MUST expose a repeatable `veracrawl-source-runtime` fixture runner.
- **FR-003**: System MUST verify HTTP, sitemap, RSS/feed, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot through one runtime report.
- **FR-004**: System MUST keep core independent of concrete browser libraries, HTTP clients, document parsers, credential vault SDKs, API clients, storage/queue SDKs, model/provider SDKs, agent frameworks, and site-specific scraper modules.
- **FR-005**: Passing reports MUST include source result, natural output, adapter-specific refs, command, policy, observability, security/privacy, event cursor, outbox, and replay refs.
- **FR-006**: Missing live runtime/credential/parser/browser/API endpoint refs MUST return `needs_review`.
- **FR-007**: Raw secrets, adapter-native state, unsafe browser side effects, and source-specific hacks MUST NOT be canonical state.
- **FR-008**: Negative dynamic source runtime scenarios MUST fail deterministically for raw secret leak, adapter-native canonical state, missing credential audit, missing document artifact, missing API payload, missing replay, unsafe browser side effect, and unsupported adapter.
- **FR-009**: CLI dynamic source runtime loading MUST be dynamic and adapter-owned.

### Key Entities

- **DynamicSourceRuntimeAdapterRecord**: Per-adapter runtime record tying adapter type, source result, natural output refs, adapter-specific refs, command, policy, observability, security/privacy, runtime/contract adapter, diagnostic state, and replay refs.
- **DynamicSourceRuntimeReport**: Gate-level result aggregating all target source runtime families.
- **DynamicSourceRuntimeFixtureManifest**: Fixture manifest describing expected completion result and failure type.

### Non-Goals

- This feature does not implement production JavaScript rendering, production credential vaulting, production parser farms, external API crawling, or production browser fleets.
- This feature does not implement CAPTCHA solving, paywall bypass, login-wall circumvention, WAF evasion, stealth automation, credential theft, or authorization bypass.
- This feature does not claim production scale, export delivery, managed storage, managed queues, or production operations readiness.

## Success Criteria

- **SC-001**: `dynamic-source-runtime-success` produces `pass` with all required source runtime refs.
- **SC-002**: `dynamic-source-runtime-runtime-unavailable` produces `needs_review`.
- **SC-003**: Negative dynamic source runtime fixtures produce `fail` with expected failure types.
- **SC-004**: Import-boundary tests prove core packages do not statically import concrete source/browser/parser/vault/API SDKs.
- **SC-005**: Contract registry validation includes dynamic source runtime contracts, command types, event types, fixture registrations, and target area coverage.

## Assumptions

- Deterministic/local adapters are sufficient to prove runtime shape and replay lineage without external websites, credentials, parsers, or API endpoints.
- Future concrete browser/parser/vault/API implementations will plug into the same contracts through adapters.
