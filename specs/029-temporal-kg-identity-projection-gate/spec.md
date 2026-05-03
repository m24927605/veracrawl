# Feature Specification: VeraCrawl Temporal KG Identity Projection Gate

**Feature Branch**: `029-temporal-kg-identity-projection-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Temporal KG Identity Projection Gate：實作 TemporalKGEntityIdentity、TemporalKGProjectionRecord、identity conflict/adjudication/supersession/invalidation records、bitemporal projection runtime gate、false-merge/false-split fixture/oracle 測試基礎；temporal KG 只能由 verified facts、published outputs、canonical events、evidence packets 與 projection watermarks 派生，不得取代 source evidence，不得讓 provisional entity clustering 進入 authoritative temporal KG；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper，core 不得耦合 graph store、agent framework、model SDK、storage、queue、browser 或 export target。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature makes temporal entity/fact projection generic across domains, sites, entity types, predicates, and output schemas. It must not encode vertical-specific entity rules or selector logic.
- **Target/V1 boundary**: This is target architecture graph intelligence work after `009-advanced-graph-projection` and `028-graph-frontier-review-runtime-gate`. It closes the executable gap between the narrow `TemporalGraphProjectionRecord` foundation and the target `TemporalKGEntityIdentity` / `TemporalKGProjectionRecord` contracts in `docs/07-data-contracts.md`.
- **Evidence and replay impact**: Temporal KG identities and records derive from verified facts, published outputs, canonical events, evidence packet refs, and projection watermarks. They may influence planning, review, contradiction detection, and repair, but cannot satisfy source evidence, verification, publication, or output manifest evidence requirements.
- **Safety and policy impact**: Provisional entity clustering, graph signals, memories, or model reasoning must not enter authoritative temporal KG state. False-merge and false-split handling must produce conflict/adjudication/supersession/invalidation refs and replay-visible operator status.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project Verified Temporal Facts (Priority: P1)

As a verifier or graph consumer, I need verified outputs and canonical events to produce bitemporal KG identities and projection records with evidence and watermark lineage.

**Why this priority**: Without verified temporal projection, the graph profile cannot distinguish authoritative KG facts from exploratory graph clusters.

**Independent Test**: Run `veracrawl-temporal-kg run tests/fixtures/temporal-kg-projection-success --profile target --out .veracrawl-test-runs/temporal-kg-projection-success`; it emits current identity, current temporal projection, canonical source refs, evidence refs, watermark refs, command/event/outbox refs, replay refs, and a pass report.

**Acceptance Scenarios**:

1. **Given** verified fact refs, published output refs, canonical event refs, evidence packet refs, and a projection watermark, **When** temporal KG projection runs, **Then** current `TemporalKGEntityIdentity` and `TemporalKGProjectionRecord` records are produced with valid time, transaction time, source refs, policy refs, and replay refs.
2. **Given** a temporal KG projection is supplied as source evidence, **When** evidence-boundary validation runs, **Then** the gate fails with `temporal_kg_projection_as_evidence`.

---

### User Story 2 - Adjudicate False Merges (Priority: P2)

As an operator, I need false-merged entity identities to produce explicit conflict, adjudication, and invalidation or supersession refs before authoritative KG state changes.

**Why this priority**: Temporal KG identity errors can corrupt downstream planning and review unless identity changes are explicit, replayable, and adjudicated.

**Independent Test**: Run `veracrawl-temporal-kg run tests/fixtures/temporal-kg-false-merge-adjudicated --profile target --out .veracrawl-test-runs/temporal-kg-false-merge-adjudicated`; it emits conflict/adjudication refs, invalidated identity refs, and a pass report.

**Acceptance Scenarios**:

1. **Given** two entity identities were incorrectly merged, **When** adjudication accepts the false-merge finding, **Then** conflict, adjudication, invalidation/supersession, source, policy, event, outbox, and replay refs are recorded.
2. **Given** a false-merge state lacks adjudication refs, **When** the runtime gate evaluates it, **Then** the fixture fails with `temporal_kg_false_merge_without_adjudication`.

---

### User Story 3 - Resolve False Splits (Priority: P3)

As a graph repair workflow, I need false-split entities and projections to create supersession refs and resulting authoritative identities without silently rewriting history.

**Why this priority**: False splits create duplicate identities and contradictory facts; repair must preserve prior state and bitemporal lineage.

**Independent Test**: Run `veracrawl-temporal-kg run tests/fixtures/temporal-kg-false-split-superseded --profile target --out .veracrawl-test-runs/temporal-kg-false-split-superseded`; it emits superseded identity/projection refs, resulting identity refs, adjudication refs, and a pass report.

**Acceptance Scenarios**:

1. **Given** an entity was split into duplicate identities, **When** adjudication resolves the split, **Then** resulting identity refs, superseded identity/projection refs, source refs, event refs, and replay refs are recorded.
2. **Given** false-split resolution lacks supersession refs, **When** the runtime gate evaluates it, **Then** the fixture fails with `temporal_kg_false_split_without_supersession`.

### Edge Cases

- Live temporal KG runtime refs are unavailable; the report must return `needs_review` with contract-only refs, not a pass claim.
- Identity derives only from provisional graph clustering; the gate must fail with `temporal_kg_provisional_identity`.
- Identity or projection lacks verified facts, published outputs, canonical event refs, or evidence packet refs.
- Projection lacks valid-time or transaction-time refs.
- Projection or identity is used as publication evidence.
- Replay-critical command, event cursor, outbox, policy, or replay bundle refs are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `TemporalKGEntityIdentity`, `TemporalKGProjectionRecord`, `TemporalKGIdentityAdjudicationRecord`, `TemporalKGRuntimeReport`, and `TemporalKGFixtureManifest` contracts.
- **FR-002**: System MUST require temporal KG identities to derive from identity evidence refs and at least one canonical verified fact, published output, or canonical event ref.
- **FR-003**: System MUST require temporal KG projection records to include entity identity ref, subject key, predicate, object value ref, value type, valid-time refs, transaction-time refs, source verified fact refs or published output refs, source event refs, evidence packet refs, and projection watermark refs.
- **FR-004**: System MUST reject temporal KG records or identities derived only from provisional graph clustering, graph signals, memory, or model reasoning.
- **FR-005**: System MUST reject temporal KG projection refs when they are presented as source evidence for publication.
- **FR-006**: System MUST model false-merge and false-split handling through conflict/adjudication/supersession/invalidation refs.
- **FR-007**: System MUST include deterministic success fixtures for ordinary projection, false-merge adjudication, and false-split supersession.
- **FR-008**: System MUST include deterministic negative fixtures for provisional identity, projection-as-evidence, missing canonical sources, missing bitemporal refs, false merge without adjudication, false split without supersession, and missing replay refs.
- **FR-009**: System MUST include a no-runtime fixture that returns `needs_review` and cannot be labeled operational pass.
- **FR-010**: System MUST register temporal KG contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-011**: System MUST provide a `veracrawl-temporal-kg` fixture runner that validates manifests and writes `run_report.json`.
- **FR-012**: System MUST keep core independent of concrete graph stores, agent frameworks, model SDKs, storage, queue, browser runtimes, export targets, and site-specific scraper dependencies.
- **FR-013**: System MUST document temporal KG usage, evidence boundaries, tests, and non-completion boundaries without claiming production graph store or graph explorer completion.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when temporal KG identities or projections are present.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **TemporalKGEntityIdentity**: Authoritative bitemporal identity derived from verified facts, accepted published outputs, canonical events, and identity evidence refs.
- **TemporalKGProjectionRecord**: Bitemporal fact projection with valid time, transaction time, source refs, evidence refs, conflict refs, status, and watermark.
- **TemporalKGIdentityAdjudicationRecord**: Replayable decision record for identity false merge, false split, invalidation, dispute, or supersession.
- **TemporalKGRuntimeReport**: Operator/replay-facing gate report tying identities, projections, adjudications, source refs, policy refs, command/event/outbox refs, runtime refs, and failures.
- **TemporalKGFixtureManifest**: Deterministic fixture declaration for success, needs-review, and negative temporal KG scenarios.

### Non-Goals *(mandatory)*

- This feature does not implement a production graph store, graph query API, graph explorer UI, vector search, memory store, export delivery, browser runtime, distributed persistence, or production graph scale operations.
- This feature does not make temporal KG authoritative source evidence for publication.
- This feature does not use external LLM/model calls or agent frameworks.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `temporal-kg-projection-success` emits identity refs, projection refs, verified/published/event/evidence/watermark refs, command/event/outbox/replay refs, and a pass report.
- **SC-002**: False-merge and false-split fixtures emit adjudication plus invalidation or supersession refs and pass declared oracles.
- **SC-003**: Provisional identity, projection-as-evidence, missing canonical source, missing bitemporal refs, missing replay, false-merge-without-adjudication, and false-split-without-supersession fixtures fail deterministically with typed operator status.
- **SC-004**: Runtime-unavailable fixture returns `needs_review` with contract-only and missing-runtime refs.
- **SC-005**: Registry validation includes every temporal KG contract, command, event, fixture, and target area coverage.
- **SC-006**: Import-boundary tests prove temporal KG runtime and CLI do not import concrete graph store, agent framework, model SDK, storage, queue, browser, export target, or site-specific scraper modules.
- **SC-007**: Full local temporal KG fixture gate completes within 30 seconds in deterministic fixture profile.

## Assumptions

- Deterministic fixtures use stable refs from existing graph, evidence/publication, verification, and event slices instead of live graph storage.
- Identity adjudication authority is represented by refs in this slice; later review UI and graph explorer work can materialize those refs without changing core contracts.
- Temporal KG reads may inform planning, review, contradiction detection, and repair only after policy and replay gates preserve source evidence boundaries.
