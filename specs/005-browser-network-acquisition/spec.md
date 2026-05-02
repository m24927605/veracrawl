# Feature Specification: VeraCrawl Browser and Network Acquisition Runtime

**Feature Branch**: `005-browser-network-acquisition`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Browser and Network Acquisition Runtime：實作真正 HTTP source adapter、local deterministic benchmark server、browser observation contracts、browser sandbox policy gates、raw HTML/DOM/screenshot/network artifact preservation、redirect/robots/rate/budget handling、SSRF/private-network/egress/size/runtime/cost negative fixtures，必須遵守 docs/07、09、10、11 與 constitution；core 只能依賴 ports/contracts，不得耦合 Playwright、HTTP client、storage、queue、model SDK 或 agent framework；不得實作成單站 scraper。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature moves VeraCrawl from deterministic source-family fixtures to governed network and browser-observation acquisition without encoding one website, one selector set, or one domain.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `004-source-adapter-fetch-runtime`. It implements real local HTTP acquisition and browser observation contracts while keeping production browser engines and storage adapters outside core.
- **Evidence and replay impact**: The feature affects network request/response metadata, redirect chains, raw HTML artifact refs, DOM artifact refs, screenshot artifact refs, network log refs, browser interaction steps, source acquisition reports, durable command/outbox/event refs, and replay validation.
- **Safety and policy impact**: Source scope, robots policy, egress allowlist, private-network deny, rate budget, response size budget, runtime budget, browser side-effect class, sandbox profile, and prompt-injection taint boundaries must block unsafe acquisition visibly.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acquire Real HTTP Sources Through Port (Priority: P1)

As a crawler runtime, I need an HTTP source adapter that performs real network acquisition against an authorized deterministic local benchmark server so raw HTML, status, headers, redirect metadata, and replay refs are preserved through the generic source adapter boundary.

**Why this priority**: VeraCrawl cannot become a powerful web crawler if source acquisition remains only synthetic. The first real network adapter must still prove low coupling and policy-controlled behavior.

**Independent Test**: Run a local benchmark server fixture and `veracrawl-network run tests/fixtures/network-http-success --profile target --out .veracrawl-test-runs/network-http-success`; the run must perform an actual local HTTP request and emit a source acquisition report with raw HTML and network metadata refs.

**Acceptance Scenarios**:

1. **Given** an allowlisted local benchmark origin, **When** the HTTP adapter fetches `/static/basic`, **Then** the run records request metadata, response metadata, raw HTML artifact ref, page snapshot ref, source adapter result ref, command/event/outbox refs, and replay-complete acquisition report.
2. **Given** a benchmark redirect route, **When** the HTTP adapter follows the redirect within policy, **Then** redirect chain refs and canonical target refs are recorded without losing the original request lineage.

---

### User Story 2 - Enforce Network Policy Gates (Priority: P2)

As an operator, I need blocked network acquisition attempts to produce typed operator-visible reports so SSRF, private-network, egress, robots, rate, response-size, redirect, and runtime violations cannot silently continue.

**Why this priority**: Real network access is a safety boundary. Policy failures must be visible before browser or extraction layers depend on acquired artifacts.

**Independent Test**: Negative fixtures for `network-robots-blocked`, `network-private-denied`, `network-egress-denied`, `network-rate-budget`, `network-size-budget`, `network-redirect-denied`, and `network-timeout` all exit successfully as accepted negative tests while reporting typed non-success outcomes.

**Acceptance Scenarios**:

1. **Given** a URL outside the egress allowlist, **When** acquisition is requested, **Then** the adapter is not called and the source acquisition report fails with `egress_denied`.
2. **Given** a private-network host denied by policy, **When** acquisition is requested, **Then** the system emits a blocked-source result and no raw artifact ref is accepted.
3. **Given** robots, rate, response-size, redirect, or runtime budget violations, **When** the network runtime evaluates the request, **Then** the run records the specific failure type and replay refs needed for audit.

---

### User Story 3 - Record Browser Observation Contracts And Sandbox Gates (Priority: P3)

As a crawler runtime, I need browser observation contracts and sandbox gates so future Playwright or other browser adapters can capture DOM, screenshot, and network metadata without coupling VeraCrawl core to a browser framework.

**Why this priority**: Browser capability is target architecture, but it must enter through contracts and ports first to avoid a browser automation demo or unsafe shortcut.

**Independent Test**: Run browser observation contract and fixture tests that validate `BrowserSandboxPolicy`, `BrowserInteractionStep`, DOM/screenshot/network artifact refs, sandbox budget decisions, and blocked unsafe side-effect classes without importing Playwright or any browser framework into core.

**Acceptance Scenarios**:

1. **Given** a read-only browser observation fixture, **When** the browser port adapter records DOM and screenshot refs, **Then** `BrowserInteractionStep` is executed with sandbox refs, budget refs, and replay-visible artifact refs.
2. **Given** a destructive, account-changing, purchase/cart, message-send, or unknown browser side effect, **When** the browser policy gate evaluates the step, **Then** the step is blocked and no DOM/screenshot artifact is accepted.

---

### User Story 4 - Preserve Replaceable Adapter Boundaries (Priority: P4)

As a developer, I need real HTTP and browser-observation adapters to remain outside core packages so future HTTP clients, Playwright, browser engines, storage clients, queues, model SDKs, or agent frameworks can be swapped through ports.

**Why this priority**: The acquisition layer must stay general-purpose and framework-neutral while adding real network capability.

**Independent Test**: Import-boundary tests scan core packages and prove they do not import concrete HTTP client packages, Playwright, browser engines, storage clients, queue clients, model SDKs, agent frameworks, or site-specific scraper modules.

**Acceptance Scenarios**:

1. **Given** network and browser acquisition modules, **When** import-boundary tests inspect core packages, **Then** only contracts, ports, policy, scheduler, durable, and replay dependencies are allowed.
2. **Given** a concrete HTTP adapter, **When** conformance tests run, **Then** it satisfies `SourceAdapterPort` and emits canonical `SourceAdapterResult` records.

### Edge Cases

- URL host is not allowlisted by source policy.
- URL resolves to loopback, link-local, private, multicast, unspecified, or otherwise denied private network space when not explicitly allowed for local deterministic fixtures.
- Robots policy denies a route.
- Redirect chain exceeds budget or redirects to a denied host.
- Response body exceeds configured byte budget.
- Runtime budget expires before response completion.
- Rate budget is exhausted before request execution.
- Browser side-effect class is destructive, account-changing, purchase/cart, message-send, or unknown.
- Browser DOM, screenshot, or network metadata artifact refs are missing.
- Replay-critical command, event cursor, outbox, policy, source adapter, acquisition, network, browser, or artifact refs are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define network request, network response, redirect hop, network acquisition report, browser sandbox policy, and browser interaction step contracts.
- **FR-002**: System MUST define a `NetworkClientPort` and `BrowserObservationPort` so core acquisition does not import concrete HTTP or browser frameworks.
- **FR-003**: System MUST implement a concrete standard-library HTTP source adapter outside core that performs actual HTTP requests against deterministic local benchmark servers through `SourceAdapterPort`.
- **FR-004**: System MUST implement deterministic local benchmark server fixtures for static HTML, redirect, robots denial, oversized response, slow response, and browser observation scenarios.
- **FR-005**: System MUST preserve raw HTML, response metadata, redirect chain metadata, DOM artifact refs, screenshot artifact refs, network metadata refs, content digest refs, privacy refs, and retention refs.
- **FR-006**: System MUST enforce egress allowlist and private-network deny policy before network execution.
- **FR-007**: System MUST enforce robots, rate, redirect, response-size, runtime, and browser sandbox budget gates with typed non-success reports.
- **FR-008**: System MUST reject unsafe browser side-effect classes before any browser observation artifact is accepted.
- **FR-009**: System MUST build replay validation for network and browser acquisition refs.
- **FR-010**: System MUST register network/browser acquisition contracts, command types, event types, fixture oracles, and target area coverage in the executable registry.
- **FR-011**: System MUST include success fixtures for HTTP static, HTTP redirect, and browser read-only observation.
- **FR-012**: System MUST include negative fixtures for robots blocked, private network denied, egress denied, rate budget, size budget, redirect denied, timeout, and unsafe browser side effect.
- **FR-013**: System MUST keep core independent of Playwright, browser engines, concrete HTTP client packages, storage clients, queue clients, model SDKs, agent frameworks, and site-specific scraper dependencies.
- **FR-014**: System MUST document implemented network/browser acquisition capability and explicitly avoid claiming full browser crawling, authenticated crawling, graph/memory intelligence, export, distributed persistence, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **NetworkRequest**: Canonical request metadata, target URL, method, headers ref, policy refs, timeout budget, size budget, and idempotency key.
- **NetworkResponse**: Canonical response metadata, status, headers ref, raw artifact ref, content digest, size, redirect refs, and timing refs.
- **RedirectHop**: One redirect transition with from/to URL refs, status, policy decision refs, and sequence number.
- **NetworkAcquisitionReport**: Replay-facing report that connects request, response, redirect, source acquisition, policy, event, outbox, and artifact refs.
- **BrowserSandboxPolicy**: Allowed origins, denied networks, runtime/size/context budgets, side-effect policy, and artifact capture settings.
- **BrowserInteractionStep**: Browser observation step with side-effect class, sandbox refs, policy refs, DOM/screenshot/network artifact refs, and status.

### Non-Goals *(mandatory)*

- This feature does not add production distributed workers, production storage, production queueing, authenticated session handling, credential vaulting, extraction, graph intelligence, memory intelligence, export connectors, or production scale crawling.
- This feature does not claim full JavaScript browser rendering. It adds browser contracts, sandbox gates, and deterministic observation fixtures; concrete Playwright or browser-engine execution remains adapter-owned future work unless separately implemented and tested.
- This feature does not implement site-specific selectors, one-off scraper logic, or vertical extraction rules.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: HTTP static fixture performs an actual local HTTP request and produces source result, fetch attempt, fetch result, page snapshot, network request/response, raw artifact, policy, command, event cursor, outbox, lease, and replay refs with zero missing required refs.
- **SC-002**: HTTP redirect fixture records every redirect hop and produces a replay-complete network acquisition report.
- **SC-003**: Browser read-only fixture records executed browser interaction step, sandbox policy, DOM artifact ref, screenshot artifact ref, network metadata ref, policy refs, and replay refs.
- **SC-004**: Robots, private-network, egress, rate, size, redirect, timeout, and unsafe-browser fixtures each produce typed non-success reports with no accepted forbidden artifact refs.
- **SC-005**: Import-boundary tests prove core packages do not import Playwright, concrete HTTP client packages, browser engines, storage clients, queue clients, model SDKs, agent frameworks, or site-specific scraper modules.
- **SC-006**: Registry validation includes every network/browser acquisition contract, command, event, fixture, and test ref.
- **SC-007**: Full local network/browser acquisition gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- Real network testing is limited to deterministic local benchmark servers controlled by tests and CLI fixtures.
- The first concrete HTTP adapter may use Python standard-library networking outside core to avoid adding a concrete third-party HTTP dependency.
- Browser engine execution remains adapter-owned. This feature creates browser contracts, sandbox policy, deterministic observation fixtures, and import boundaries without coupling core to Playwright.
- Local benchmark loopback access is allowed only when the fixture policy explicitly permits the local deterministic origin.
