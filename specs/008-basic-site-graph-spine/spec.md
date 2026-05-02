# Feature Specification: VeraCrawl Basic Site Graph Spine

**Feature Branch**: `008-basic-site-graph-spine`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Basic Site Graph Spine：在 network/browser、normalize/extract、evidence/publication spine 之上，實作 URL graph、hyperlink graph、redirect/canonical graph、page-structure graph、graph build manifest、graph edge provenance、projection watermark、graph replay validation、fixture/oracle 測試基礎。必須遵守 docs/07、08、09、10、11 與 constitution；graph signal 不得取代 source evidence，不得讓 graph/memory 成為 publication source of truth；不得實作成單站 scraper；core 不得耦合 agent framework、model SDK、browser、storage、queue、graph store 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature builds generic site graph records from URL, hyperlink, canonical, redirect, page type, and evidence refs without website-specific selectors or vertical graph assumptions.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `007-evidence-publication-spine`, aligned with `docs/08-build-roadmap.md` Phase 3 Basic Site Graph and `docs/10-target-implementation-design.md` graph projection rules.
- **Evidence and replay impact**: Graph nodes and edges preserve provenance refs and replay manifests, but graph signals cannot satisfy publication evidence or become canonical output truth.
- **Safety and policy impact**: Graph-derived priority or relationship signals are diagnostic/planning aids only. Publication still requires source evidence, verification, review, policy, privacy, and replay gates.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build URL And Hyperlink Graph (Priority: P1)

As a crawler planner, I need discovered URLs and links to become replayable graph nodes and edges so future frontier logic can reason about site structure without losing provenance.

**Why this priority**: URL and hyperlink graph records are the foundation for graph-driven crawling and deduplication.

**Independent Test**: Run `veracrawl-graph run tests/fixtures/graph-url-hyperlink --profile target --out .veracrawl-test-runs/graph-url-hyperlink`; it emits URL nodes, hyperlink edges, provenance refs, graph manifest, watermark, and replay-complete graph report.

**Acceptance Scenarios**:

1. **Given** link provenance records, **When** graph build runs, **Then** every source and target URL becomes a node and every discovered link becomes a provenance-backed edge.
2. **Given** duplicate links, **When** graph build runs, **Then** duplicate edges are deduplicated with deterministic IDs and provenance refs retained.

---

### User Story 2 - Build Canonical, Redirect, And Page Structure Edges (Priority: P2)

As a site understanding service, I need canonical, redirect, page type, and template relationships to be replayable graph edges so crawl planning can identify duplicate, listing, detail, and hub structures.

**Why this priority**: General-purpose crawling needs structural site context before advanced graph intelligence.

**Independent Test**: Canonical and page-structure fixtures verify redirect/canonical edges, page type nodes, and structure edges with input refs and deterministic rebuild hashes.

**Acceptance Scenarios**:

1. **Given** redirect and canonical refs, **When** graph build runs, **Then** redirect/canonical edges are recorded with source acquisition provenance.
2. **Given** page type and site model refs, **When** graph build runs, **Then** page structure nodes and edges are recorded without replacing source evidence.

---

### User Story 3 - Validate Graph Replay And Evidence Boundary (Priority: P3)

As an operator, I need graph builds to be replayable and unable to satisfy publication evidence so graph-derived decisions remain auditable and safe.

**Why this priority**: Graph intelligence is powerful but must not undermine evidence-backed publication.

**Independent Test**: Negative fixtures fail missing input refs, graph rebuild mismatch, and graph-as-evidence attempts.

**Acceptance Scenarios**:

1. **Given** missing graph input refs, **When** replay validation runs, **Then** graph report is non-pass with typed missing refs.
2. **Given** graph signal refs are used as publication evidence, **When** graph boundary validation runs, **Then** the attempt fails and no publication evidence claim is accepted.

### Edge Cases

- Link provenance refs are missing or duplicated.
- Redirect/canonical refs conflict.
- Page type refs are absent or unknown.
- Graph build inputs change but rebuild hash does not match.
- Graph signal is used as publication evidence.
- Graph projection watermark is missing.
- Replay-critical graph manifest, node, edge, provenance, input, watermark, command, event, outbox, or policy refs are unavailable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define graph node, graph edge, graph edge provenance, graph build manifest, projection watermark, graph build report, and graph fixture manifest contracts.
- **FR-002**: System MUST build deterministic URL nodes and hyperlink edges from generic link provenance refs.
- **FR-003**: System MUST deduplicate graph nodes and edges by stable graph keys while preserving provenance refs.
- **FR-004**: System MUST build redirect and canonical edges from acquisition/canonical refs when provided.
- **FR-005**: System MUST build page type and page structure nodes/edges from page classification and site model refs.
- **FR-006**: System MUST create graph build manifests with input refs, graph version, rebuild hash, projection watermark refs, and policy refs.
- **FR-007**: System MUST create graph build reports with node refs, edge refs, provenance refs, manifest refs, watermark refs, command/event/outbox refs, and completion result.
- **FR-008**: System MUST reject graph-as-evidence attempts and prevent graph refs from satisfying publication source evidence coverage.
- **FR-009**: System MUST include success fixtures for URL/hyperlink graph, canonical/redirect graph, and page-structure graph.
- **FR-010**: System MUST include negative fixtures for missing graph input, graph rebuild mismatch, and graph-as-evidence boundary violation.
- **FR-011**: System MUST register contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-012**: System MUST keep core independent of concrete graph stores, browser, HTTP client, storage, queue, model SDK, agent framework, memory store, export target, and site-specific scraper dependencies.
- **FR-013**: System MUST document implemented graph capability and explicitly avoid claiming advanced graph intelligence, memory, export, distributed persistence, production browser rendering, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **GraphNode**: Stable graph node for URL, page type, template, canonical, or source evidence reference.
- **GraphEdge**: Stable relationship edge for hyperlink, redirect, canonical, page structure, or evidence relationship.
- **GraphEdgeProvenance**: Input refs and policy refs explaining why an edge exists.
- **GraphBuildManifest**: Deterministic graph build inputs, version, rebuild hash, watermark, and policy refs.
- **ProjectionWatermark**: Replayable graph projection cursor and freshness marker.
- **GraphBuildReport**: Operator/replay-facing graph build result.

### Non-Goals *(mandatory)*

- This feature does not implement entity graph, temporal knowledge graph, graph store adapters, graph-driven frontier scheduling, memory, export delivery, distributed persistence, production browser rendering, or production scale graph operations.
- This feature does not let graph signals satisfy evidence or publication requirements.
- This feature does not use LLM/model calls or external agent frameworks.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: URL/hyperlink fixture emits deterministic URL nodes, hyperlink edges, provenance refs, graph manifest, watermark, and pass graph report.
- **SC-002**: Canonical/redirect fixture emits redirect/canonical edges with acquisition/canonical provenance refs.
- **SC-003**: Page-structure fixture emits page type and page structure nodes/edges with site model refs.
- **SC-004**: Missing input, graph rebuild mismatch, and graph-as-evidence fixtures produce typed non-success reports.
- **SC-005**: Registry validation includes every graph contract, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core graph packages do not import concrete graph store, browser, HTTP client, storage, queue, model SDK, agent framework, memory store, export target, or site-specific scraper dependencies.
- **SC-007**: Full local graph gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- Graph fixtures use stable refs from prior acquisition, normalization, and evidence slices instead of production graph storage.
- Basic graph means URL, hyperlink, redirect/canonical, and page-structure graph only.
- Advanced graph profiles remain later specs.
