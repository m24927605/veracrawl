# Feature Specification: VeraCrawl Graph-Driven Frontier And Review Runtime Gate

**Feature Branch**: `028-graph-frontier-review-runtime-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Graph-Driven Frontier and Review Runtime Gate：將 GraphSignal 接入 frontier priority、review routing、retry/retire/expand decision contracts、command/event/replay 基礎、policy gates、fixture/oracle 測試基礎；GraphSignal 可影響 frontier/review 但不得成為 source evidence 或 publication source of truth；core 不得耦合 graph store、agent framework、model SDK、browser、storage、queue 或具體 HTTP client；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper。"

## Constitution Alignment

- **General-purpose crawler impact**: This feature adds generic graph-driven decision contracts for any authorized crawl objective; it does not encode a website, schema, vertical, source shape, or scraper-specific rule.
- **Target/V1 boundary**: This is target architecture work for item 5 in `docs/10-target-implementation-design.md`: graph projections and graph-driven frontier/review workflows.
- **Evidence and replay impact**: Graph signals may influence frontier and review routing only through command/event/replay-backed decision records. They cannot satisfy source evidence, verification, publication, or output manifest requirements.
- **Safety and policy impact**: Every graph-driven frontier/review decision must carry policy refs, explanations, bounded graph signals, command refs, event cursor refs, outbox refs, and replay refs. Unauthorized frontier mutation and graph-as-evidence attempts fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`.

## User Scenarios & Testing

### User Story 1 - Apply Graph Signals To Frontier And Review (Priority: P1)

An operator can run a deterministic graph-driven runtime fixture and prove graph signals produce replayable frontier priority, retry, retire, expand, and review route decisions.

**Independent Test**: Run `graph-frontier-review-success`; it passes only when all decision families include graph signal refs, source graph refs, explanations, policy, command, event/outbox, and replay refs.

**Acceptance Scenarios**:

1. **Given** frontier/review graph signals, **When** the runtime gate runs, **Then** it emits pass records for priority, retry, retire, expand, and review routing.
2. **Given** a graph signal, **When** it influences a frontier item, **Then** the decision is explainable, policy-backed, replayable, and cannot mutate frontier state without command/event refs.

### User Story 2 - Missing Runtime Requires Review (Priority: P2)

An operator can distinguish graph signal contracts from operational graph-driven frontier/review runtime availability.

**Independent Test**: Run `graph-frontier-review-runtime-unavailable`; it returns `needs_review` with missing runtime refs.

**Acceptance Scenarios**:

1. **Given** only contract descriptors, **When** runtime pass is requested, **Then** the report is `needs_review`.
2. **Given** missing scheduler/review runtime refs, **When** the gate evaluates completion, **Then** it cannot claim pass.

### User Story 3 - Unsafe Or Incomplete Graph Use Fails (Priority: P3)

The gate fails when graph signals are used as source evidence, omit source graph refs or explanations, mutate frontier without authorization, omit review routes or replay refs, or use unsupported signal types.

**Independent Test**: Run negative fixtures for graph-as-evidence, missing source graph refs, missing explanation, unauthorized frontier mutation, missing review route, missing replay, and unsupported signal.

**Acceptance Scenarios**:

1. **Given** a graph signal is used as publication evidence, **When** the gate validates it, **Then** the report fails.
2. **Given** a frontier mutation lacks command/event/policy refs, **When** the gate validates it, **Then** the report fails.
3. **Given** review routing lacks a review item route, **When** the gate validates it, **Then** the report fails.

### Edge Cases

- Graph signal score must remain bounded and explainable.
- Graph signals must not satisfy `source_evidence_refs`, evidence packets, verification decisions, publication pass, or output manifests.
- Frontier expand can create new frontier refs only through a graph-driven decision record with policy and replay refs.
- Retry/retire decisions must preserve reason refs and cannot silently bypass source policy, budget, or review gates.
- Missing graph store/runtime/scheduler/review integration refs produce `needs_review`; unsafe or incomplete records produce `fail`.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define graph-driven frontier decision, review route decision, report, and fixture manifest contracts.
- **FR-002**: System MUST expose a repeatable `veracrawl-graph-frontier-review` fixture runner.
- **FR-003**: System MUST prove priority, retry, retire, expand, and review route decisions from graph signals in one success report.
- **FR-004**: System MUST keep core independent of graph stores, agent frameworks, model SDKs, browser libraries, storage clients, queue clients, and concrete HTTP clients.
- **FR-005**: Passing reports MUST include graph signal, source graph, frontier item, review item, explanation, policy, command, event cursor, outbox, and replay refs.
- **FR-006**: Missing live graph/scheduler/review runtime refs MUST return `needs_review`.
- **FR-007**: Graph signals MUST NOT become source evidence, verification authority, publication source of truth, or output manifest evidence.
- **FR-008**: Negative scenarios MUST fail deterministically for graph signal as evidence, missing source graph refs, missing explanation, unauthorized frontier mutation, missing review route, missing replay, and unsupported signal.
- **FR-009**: CLI/runtime loading MUST remain dependency-neutral and must not require production graph stores or queue clients.

### Key Entities

- **GraphFrontierDecisionRecord**: Per-decision record tying a graph signal to a frontier priority, retry, retire, or expand action with policy, command, event/outbox, and replay refs.
- **GraphReviewRouteDecisionRecord**: Per-decision record tying a graph signal to a review route with review item, priority, policy, command, event/outbox, and replay refs.
- **GraphFrontierReviewRuntimeReport**: Gate-level result aggregating graph-driven frontier/review decisions.
- **GraphFrontierReviewFixtureManifest**: Fixture manifest describing expected completion result and failure type.

### Non-Goals

- This feature does not implement a production graph store, production scheduler backend, review UI, queue broker, managed persistence, memory store, export delivery, browser rendering, model SDK integration, or agent framework integration.
- This feature does not make graph signals authoritative evidence or publication truth.
- This feature does not implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

- **SC-001**: `graph-frontier-review-success` produces `pass` with priority, retry, retire, expand, and review route decisions.
- **SC-002**: `graph-frontier-review-runtime-unavailable` produces `needs_review`.
- **SC-003**: Negative graph frontier/review fixtures produce `fail` with expected failure types.
- **SC-004**: Import-boundary tests prove core does not statically import graph stores, agent frameworks, model SDKs, browser libraries, storage clients, queue clients, or concrete HTTP clients.
- **SC-005**: Contract registry validation includes graph frontier/review contracts, command types, event types, fixture registrations, and target area coverage.

## Assumptions

- Existing `GraphSignal`, `FrontierItem`, and `ReviewItem` contracts are the canonical upstream/downstream records.
- Deterministic fixtures are sufficient to prove runtime shape, safety boundaries, and replay lineage without a production graph store or queue backend.
- Future concrete graph-store and scheduler integrations will plug into the same contracts.
