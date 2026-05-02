# Feature Specification: VeraCrawl Advanced Graph Projection Spine

**Feature Branch**: `009-advanced-graph-projection`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Advanced Graph Projection Spine：在 basic site graph spine 之上，實作 projection spec、projection rebuild job、projection mismatch report、graph delta report、graph signal、graph quality report、graph-driven frontier/review signal contracts、entity/source-evidence/task/temporal graph foundation，以及 fixture/oracle 測試基礎。必須遵守 docs/07、08、09、10、11 與 constitution；graph signal 不得取代 source evidence，不得讓 graph/memory 成為 publication source of truth；不得實作成單站 scraper；core 不得耦合 graph store、agent framework、model SDK、browser、storage、queue、memory store、export target 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature builds generic graph projection contracts and deterministic fixture behavior across URL, entity, task, source/evidence, and temporal graph foundations without site-specific selectors or vertical assumptions.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `008-basic-site-graph-spine`, aligned with `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Graph projections derive from canonical events/artifacts and source evidence refs. Graph signals may influence frontier and review routing but cannot satisfy publication evidence coverage or become source of truth.
- **Safety and policy impact**: Projection rebuilds require policy refs, event cursors, watermarks, deterministic hashes, mismatch reports, and replay-visible failure states.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rebuild Advanced Graph Projection (Priority: P1)

As an operator, I need graph projections to be specified, rebuilt, watermarked, and hash-checked so graph intelligence remains derived, replayable, and auditable.

**Independent Test**: Run `veracrawl-projection run tests/fixtures/projection-rebuild-success --profile target --out .veracrawl-test-runs/projection-rebuild-success`; it emits projection spec, rebuild job, watermark, delta report, quality report, graph signal, temporal record, and replay-complete report.

**Acceptance Scenarios**:

1. **Given** a basic site graph manifest and node/edge refs, **When** advanced graph projection runs, **Then** projection spec, rebuild job, watermark, graph delta, graph quality, graph signals, temporal records, and replay refs are recorded.
2. **Given** projection inputs are replayed, **When** rebuild hash matches, **Then** the report passes with command/event/outbox/policy refs.

---

### User Story 2 - Emit Frontier And Review Graph Signals (Priority: P2)

As crawl planning and review services, I need graph signals to explain frontier priority and review routing while remaining non-authoritative for evidence.

**Independent Test**: `graph-signal-frontier-review` fixture emits `frontier_priority` and `review_route` signals with explanations and source graph refs.

**Acceptance Scenarios**:

1. **Given** projection-derived graph context, **When** signal generation runs, **Then** frontier/review signal refs include source graph refs, explanation refs, policy refs, and bounded scores.
2. **Given** a signal is offered as source evidence, **When** evidence boundary validation runs, **Then** it fails with `graph_signal_as_evidence`.

---

### User Story 3 - Prove Temporal Graph Foundation (Priority: P3)

As a verification and drift workflow, I need temporal graph records to derive only from verified outputs, evidence packet refs, canonical events, and projection watermarks.

**Independent Test**: `temporal-graph-foundation` fixture emits temporal graph records with valid-time refs, entity identity refs, source output refs, evidence packet refs, and projection watermark refs.

**Acceptance Scenarios**:

1. **Given** accepted output and evidence refs, **When** temporal projection runs, **Then** temporal records include valid time, entity identity, evidence packet, and projection watermark refs.
2. **Given** projection inputs cannot be watermarked or rebuilt deterministically, **When** replay validation runs, **Then** a typed failure or mismatch report is emitted instead of a pass claim.

### Edge Cases

- Projection watermark is missing.
- Rebuild hash differs from expected hash.
- Graph signal is used as source evidence.
- Source graph refs, node refs, edge refs, policy refs, command refs, event cursors, or outbox refs are missing.
- Temporal record lacks verified output refs, evidence packet refs, valid-time refs, entity identity refs, or watermark refs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define projection spec, projection rebuild job, projection mismatch report, graph delta report, graph signal, graph quality report, temporal graph projection record, advanced graph projection report, and advanced graph fixture manifest contracts.
- **FR-002**: System MUST rebuild advanced graph projections from basic graph manifest/node/edge refs and deterministic source/evidence refs.
- **FR-003**: System MUST record projection watermarks with input manifest refs, event cursor refs, rebuild hash, and freshness refs.
- **FR-004**: System MUST emit projection mismatch reports when expected and actual rebuild hashes differ.
- **FR-005**: System MUST emit graph delta reports and graph quality reports for projection rebuilds.
- **FR-006**: System MUST emit graph signals with subject refs, source graph refs, explanation refs, scores, policy refs, and explicit evidence-disallowed semantics.
- **FR-007**: System MUST provide graph-driven frontier/review signal contracts without implementing concrete scheduling behavior in this slice.
- **FR-008**: System MUST provide entity/source-evidence/task/temporal graph foundation fields without claiming production graph intelligence completion.
- **FR-009**: System MUST reject graph-signal-as-evidence attempts and prevent graph signals from satisfying publication source evidence coverage.
- **FR-010**: System MUST include success fixtures for projection rebuild, frontier/review graph signals, and temporal graph foundation.
- **FR-011**: System MUST include negative fixtures for missing projection watermark, projection mismatch, and graph-signal-as-evidence boundary violation.
- **FR-012**: System MUST register contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-013**: System MUST keep core independent of concrete graph stores, browser, HTTP client, storage, queue, model SDK, agent framework, memory store, export target, and site-specific scraper dependencies.
- **FR-014**: System MUST document implemented advanced graph projection capability and explicitly avoid claiming memory, export, distributed persistence, production browser rendering, production graph store operations, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when graph signals or temporal graph refs are present.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **ProjectionSpec**: Projection definition, input manifests, graph version, owner, rebuild policy, and policy refs.
- **ProjectionRebuildJob**: Deterministic rebuild job with expected/actual hash, status, watermark, and policy refs.
- **ProjectionMismatchReport**: Typed report when rebuild output does not match expected deterministic hash.
- **GraphSignal**: Frontier/review/drift/dedup/quality signal derived from graph refs and explicitly disallowed as source evidence.
- **GraphDeltaReport**: Projection delta from previous to current graph manifest.
- **GraphQualityReport**: Projection quality metrics, score refs, warning refs, and policy refs.
- **TemporalGraphProjectionRecord**: Temporal record derived from verified outputs, evidence packet refs, identity refs, valid-time refs, and projection watermark.
- **AdvancedGraphProjectionReport**: Operator/replay-facing result tying projection refs, graph refs, temporal refs, policy refs, command/event/outbox refs, and failure refs.

### Non-Goals *(mandatory)*

- This feature does not implement a production graph store adapter, production graph query API, graph explorer UI, memory system, export delivery, distributed persistence, production browser rendering, or production scale graph operations.
- This feature does not implement concrete graph-driven scheduling behavior; it defines replayable signal contracts consumed by later scheduler/frontier work.
- This feature does not let graph signals satisfy evidence or publication requirements.
- This feature does not use LLM/model calls or external agent frameworks.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Projection rebuild success fixture emits deterministic projection spec, rebuild job, watermark, delta report, quality report, graph signal, temporal record, and pass report.
- **SC-002**: Frontier/review signal fixture emits `frontier_priority` and `review_route` signals with source graph refs and explanations.
- **SC-003**: Temporal graph foundation fixture emits temporal records with output refs, evidence packet refs, valid-time refs, identity refs, and watermark refs.
- **SC-004**: Missing watermark, projection mismatch, and graph-signal-as-evidence fixtures produce typed non-success reports.
- **SC-005**: Registry validation includes every advanced graph projection contract, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core graph/projection packages do not import concrete graph store, browser, HTTP client, storage, queue, model SDK, agent framework, memory store, export target, or site-specific scraper dependencies.
- **SC-007**: Full local advanced graph projection gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- Advanced graph fixtures use stable refs from prior basic graph, evidence/publication, acquisition, normalization, and durable runtime slices instead of production graph storage.
- Projection rebuilds are deterministic from canonical refs and fixtures in this slice.
- Later specs may connect these contracts to production graph stores, frontier scheduling, memory, export, and operations without changing core evidence boundaries.
