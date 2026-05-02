# Feature Specification: VeraCrawl Source Adapter and Fetch Runtime

**Feature Branch**: `004-source-adapter-fetch-runtime`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Source Adapter and Fetch Runtime：在 durable runtime scheduler foundation 上實作通用 source acquisition layer，包含 SourceAdapterPort runtime execution、HTTP/sitemap/RSS/API-like/document-source deterministic adapters、source policy gates、fetch attempt/result/page snapshot/document artifact contracts、rate limit/retry/blocked-source/adapter-mismatch/malformed-response handling、raw artifact preservation、scheduler frontier item 到 source adapter command/result/artifact refs 的流程、fixture/oracle 與 replay recovery 驗收。必須遵守 docs/07、09、10、11、constitution 與 AGENTS.md；不得實作成單站 scraper；core 不得耦合 concrete browser、storage、queue、model SDK 或 agent framework。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature adds a generic source acquisition layer for multiple source families and does not encode one website, one schema, or one scraper flow.
- **Target/V1 boundary**: This is target architecture dependency sequencing after durable runtime and scheduler foundations. It is governed by `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: The feature affects source adapter commands/results, fetch attempts, fetch results, page snapshots, document artifacts, raw artifact refs, scheduler leases, durable command/event/outbox refs, and replay recovery reports.
- **Safety and policy impact**: Source scope, robots/terms/customer authorization, rate limits, retry budgets, blocked sources, malformed responses, raw artifact retention, and credential isolation must be explicit and operator-visible.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Generic Source Adapters (Priority: P1)

As a crawler runtime, I need source adapter commands to execute through a generic runtime boundary so HTTP, sitemap, RSS, API-like, and document-source inputs produce typed source results and raw artifacts without site-specific code.

**Why this priority**: Source acquisition is the next required target capability after durable scheduling. Without it, the runtime cannot crawl real source families through a general-purpose interface.

**Independent Test**: Run a deterministic source success fixture that leases a scheduler frontier item, executes a source adapter command, persists source result and artifact refs, and validates durable replay recovery.

**Acceptance Scenarios**:

1. **Given** a queued frontier item and allowed source policy, **When** the fetch runtime executes an HTTP adapter, **Then** it records a fetch attempt, fetch result, page snapshot, source adapter result, raw artifact ref, event cursor, outbox ref, and durable recovery report.
2. **Given** sitemap, RSS, API-like, and document-source fixture inputs, **When** each adapter executes, **Then** each emits its natural result type and does not fake incompatible fetch semantics.

---

### User Story 2 - Enforce Source Policy And Retry Gates (Priority: P2)

As an operator, I need blocked sources, rate limits, malformed responses, adapter mismatches, and retry exhaustion to produce typed non-success outcomes so unsafe or incomplete source acquisition cannot silently continue.

**Why this priority**: Source acquisition touches external websites and must fail visibly when policy or adapter semantics are unsafe.

**Independent Test**: Negative fixtures for blocked source, rate limited, adapter mismatch, malformed response, and retry exhausted all produce typed diagnostics and no successful source artifact publication.

**Acceptance Scenarios**:

1. **Given** a source policy denial, **When** the source adapter command executes, **Then** the result is blocked, no raw artifact is accepted, and diagnostics identify the policy decision.
2. **Given** rate-limited or malformed source input, **When** retry budget remains, **Then** retry metadata is recorded; when budget is exhausted, **Then** a retry-exhausted report blocks completion.
3. **Given** an adapter emits a result type outside its natural mapping, **When** validation runs, **Then** the command is rejected and replay recovery fails visibly.

---

### User Story 3 - Preserve Raw Artifacts And Replay Lineage (Priority: P3)

As a reviewer, I need every source result to point back to raw artifact hashes, fetch metadata, scheduler lease refs, command results, event cursors, outbox records, and policy decisions so source acquisition can be replayed and audited.

**Why this priority**: VeraCrawl cannot trust extracted data unless raw source lineage is preserved before normalization, extraction, evidence, and publication.

**Independent Test**: Replay unit and integration tests prove every successful source result has raw artifact refs, content hashes, policy refs, command result refs, event cursor refs, and scheduler lease refs.

**Acceptance Scenarios**:

1. **Given** a successful source result, **When** replay recovery validates the run, **Then** no source, artifact, command, event, outbox, lease, or policy refs are missing.
2. **Given** a missing raw artifact, **When** replay recovery validates source acquisition, **Then** the report fails and identifies the missing artifact ref.

---

### User Story 4 - Keep Adapter Runtime Replaceable (Priority: P4)

As a developer, I need deterministic source adapters to remain behind `SourceAdapterPort` so future production HTTP/browser/storage/model adapters can be swapped without changing core contracts.

**Why this priority**: The source layer must not become a concrete browser, storage, queue, SDK, or single-site scraper implementation.

**Independent Test**: Import-boundary and adapter contract tests prove core packages do not import concrete browser/storage/queue/model/agent dependencies and do not contain site-specific scraper modules.

**Acceptance Scenarios**:

1. **Given** source adapter runtime modules, **When** import-boundary tests inspect core packages, **Then** no forbidden concrete dependencies or site-specific modules are present.
2. **Given** deterministic adapters for multiple source families, **When** conformance tests run, **Then** all adapters satisfy the same source adapter port and result contract.

### Edge Cases

- Source policy can deny, require review, or allow; deny and review paths must not produce successful source acquisition.
- Rate-limited sources must record retry-after refs and scheduler retry behavior.
- Malformed responses must preserve diagnostic refs without treating invalid content as accepted raw artifacts.
- Adapter result type mismatches must be rejected before source results become canonical.
- Missing raw artifacts or missing content hashes must fail replay recovery.
- Scheduler leases must be valid before source adapter commands can mutate source acquisition state.
- Deterministic source adapters must not include website-specific selectors, credentials, or crawler logic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define fetch attempt, fetch result, page snapshot, document artifact, source acquisition report, rate limit, retry, and source failure contracts.
- **FR-002**: System MUST execute source adapter commands through `SourceAdapterPort` and persist results through durable command/event/outbox/artifact refs.
- **FR-003**: System MUST implement deterministic adapter fixtures for HTTP, sitemap, RSS, API-like, and document-source families.
- **FR-004**: System MUST preserve each raw source artifact with content digest, size, lifecycle, retention, and privacy refs.
- **FR-005**: System MUST validate adapter natural result type mappings and reject adapter mismatch results.
- **FR-006**: System MUST enforce source policy decisions for source scope, robots/terms/customer authorization, rate limits, credential scope, and blocked-source behavior.
- **FR-007**: System MUST connect scheduler frontier item and queue lease refs to source adapter command execution.
- **FR-008**: System MUST record retry metadata, retry-after refs, attempt counts, and retry-exhausted diagnostics.
- **FR-009**: System MUST handle malformed source responses as typed failures with operator-visible diagnostics.
- **FR-010**: System MUST build source replay recovery reports that validate source adapter result refs, fetch attempt/result refs, raw artifact refs, command refs, event cursors, outbox refs, policy refs, and lease refs.
- **FR-011**: System MUST register source acquisition contracts, command types, event types, adapter fixtures, and acceptance tests in the executable registry.
- **FR-012**: System MUST include deterministic success fixtures for HTTP, sitemap, RSS, API-like, and document-source adapters.
- **FR-013**: System MUST include negative fixtures for blocked source, rate limited, adapter mismatch, malformed response, retry exhausted, and missing raw artifact.
- **FR-014**: System MUST keep core source acquisition independent of concrete browser, storage, queue, model SDK, agent framework, and site-specific scraper dependencies.
- **FR-015**: System MUST document implemented source acquisition capability and explicitly avoid claiming full browser crawling, graph/memory intelligence, production persistence, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **FetchAttempt**: A policy-checked attempt to acquire a source using an adapter.
- **FetchResult**: A typed result of an acquisition attempt with status, metadata, and artifact refs.
- **PageSnapshot**: A raw page snapshot ref for HTTP-like and browser-compatible future sources.
- **DocumentArtifact**: A raw document-source artifact ref and metadata record.
- **RateLimitDecision**: A typed rate-limit and retry-after decision.
- **SourceFailureReport**: Operator-visible diagnostics for blocked, malformed, mismatch, missing artifact, and retry-exhausted scenarios.
- **SourceAcquisitionReport**: Replay-facing summary of command, event, outbox, artifact, policy, source result, and lease refs.

### Non-Goals *(mandatory)*

- This feature does not add production HTTP clients, browser engines, storage clients, queue clients, model SDKs, agent frameworks, or distributed crawler workers.
- This feature does not implement JavaScript rendering, login flows, CAPTCHA handling, stealth automation, graph intelligence, memory intelligence, export connectors, or production-scale crawl throughput.
- This feature does not implement site-specific selectors, one-off scraper logic, or vertical extraction rules.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: HTTP success fixture produces source result, fetch attempt, fetch result, page snapshot, raw artifact, command, event cursor, outbox, policy, lease, and replay recovery refs with zero missing required refs.
- **SC-002**: Sitemap, RSS, API-like, and document-source fixtures each emit their natural source result type and pass adapter conformance tests.
- **SC-003**: Blocked source, rate-limited, adapter mismatch, malformed response, retry-exhausted, and missing raw artifact fixtures produce typed non-success reports.
- **SC-004**: Adapter mismatch tests prove incompatible result types are rejected before canonical source result acceptance.
- **SC-005**: Missing raw artifact replay tests fail and identify the missing artifact ref.
- **SC-006**: Registry validation includes every source acquisition contract, command, event, fixture, and test ref.
- **SC-007**: Import-boundary tests prove core source acquisition packages do not import concrete browser, storage, queue, model SDK, agent framework, or site-specific scraper dependencies.
- **SC-008**: Full local source-adapter gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- Deterministic source adapters can use local fixture payloads to prove adapter semantics before production network adapters are introduced.
- The durable scheduler foundation provides valid frontier item and lease contracts for source acquisition.
- Production HTTP/browser/storage adapters will be introduced in later specs after source contracts, policy gates, retry behavior, and replay lineage are stable.
