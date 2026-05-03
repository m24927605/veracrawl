# Feature Specification: VeraCrawl Target Output Type Coverage Gate

**Feature Branch**: `030-output-type-coverage-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Target Output Type Coverage Gate：實作 record、table、document_metadata、document、file、dataset、fact 這 7 種 target output type 的 evidence coverage、verification、publication、output manifest、privacy lifecycle、replay 與 fixture/oracle gate；必須證明每種 output type 都不能由 candidate、graph、memory、agent reasoning 或 temporal KG 直接取代 source evidence；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper，core 不得耦合 storage、queue、export target、agent framework、model SDK、browser 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature proves VeraCrawl can publish all target output families across many schemas and sites without hard-coded domain assumptions.
- **Target/V1 boundary**: This is target architecture coverage work for the Source Adapter, Website Pattern, And Output Coverage Profile in `docs/09-target-capability-model.md` and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Every output type must carry source evidence refs, evidence coverage refs, verification refs, publication manifest refs, privacy lifecycle refs, command/event/outbox refs, and replay refs.
- **Safety and policy impact**: Candidate, graph, memory, agent reasoning, and temporal KG refs may inform decisions but cannot replace source evidence for publication.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove All Target Output Types (Priority: P1)

As a data pipeline owner, I need record, table, document metadata, document, file, dataset, and fact outputs to pass the same evidence-backed publication gate.

**Why this priority**: VeraCrawl cannot claim general-purpose output coverage if only one output shape has evidence and publication acceptance.

**Independent Test**: Run `veracrawl-output-coverage run tests/fixtures/output-type-coverage-success --profile target --out .veracrawl-test-runs/output-type-coverage-success`; it emits coverage records for all seven target output types and a pass report.

**Acceptance Scenarios**:

1. **Given** seven output type candidates with source-backed evidence, **When** the output coverage gate runs, **Then** each output type has evidence coverage, verification, publication, manifest, lifecycle, command/event/outbox, and replay refs.
2. **Given** the report lacks any target output type, **When** the gate evaluates coverage, **Then** it fails instead of claiming target output coverage.

---

### User Story 2 - Enforce Source Evidence Boundary (Priority: P2)

As a reviewer, I need publication to reject outputs whose evidence is only candidate, graph, memory, agent reasoning, or temporal KG-derived context.

**Why this priority**: Output coverage is unsafe if derived planning context can masquerade as source evidence.

**Independent Test**: Negative fixtures for output-type-coverage-candidate-as-evidence, output-type-coverage-graph-as-evidence, output-type-coverage-memory-as-evidence, output-type-coverage-agent-reasoning-as-evidence, and output-type-coverage-temporal-kg-as-evidence fail with typed operator status.

**Acceptance Scenarios**:

1. **Given** an output type has only derived context refs, **When** publication coverage is checked, **Then** the output is rejected with a typed failure.
2. **Given** a temporal KG projection is attached, **When** source evidence refs are missing, **Then** the gate fails even if temporal KG lineage exists.

---

### User Story 3 - Validate Type-Specific Evidence Requirements (Priority: P3)

As an operator, I need table rows/cells, document sections, file hashes, dataset items, and fact verification to have type-specific oracle checks.

**Why this priority**: A generic "has evidence" flag is too weak for the target output profile.

**Independent Test**: Negative fixtures for missing table cell anchors, missing file lifecycle/hash refs, missing dataset item evidence, missing fact verification, unsupported output type, and missing replay fail deterministically.

**Acceptance Scenarios**:

1. **Given** a table output lacks row/cell evidence refs, **When** coverage runs, **Then** it fails with a table-specific missing-ref field.
2. **Given** a file output lacks hash or lifecycle refs, **When** coverage runs, **Then** it fails with file lifecycle/hash missing refs.
3. **Given** a dataset output lacks item-level evidence refs, **When** coverage runs, **Then** it fails with dataset evidence missing refs.

### Edge Cases

- Live publication/runtime refs are unavailable; report must return `needs_review`.
- One or more target output types are omitted.
- Unsupported output type is supplied.
- Published output or output manifest refs are present without evidence/verification refs.
- Replay-critical command, event cursor, outbox, policy, lifecycle, or replay refs are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define `OutputTypeCoverageRecord`, `OutputTypePublicationGateReport`, and `OutputTypeCoverageFixtureManifest` executable contracts.
- **FR-002**: System MUST define canonical target output types: `record`, `table`, `document_metadata`, `document`, `file`, `dataset`, and `fact`.
- **FR-003**: System MUST require every target output type to include source evidence refs, evidence coverage refs, verification refs, published output refs, output manifest refs, privacy lifecycle refs, policy refs, command refs, event cursor refs, outbox refs, and replay refs before pass.
- **FR-004**: System MUST include type-specific required refs for tables, document metadata, documents, files, datasets, and facts.
- **FR-005**: System MUST reject candidate-only, graph-only, memory-only, agent-reasoning-only, and temporal-KG-only source evidence attempts.
- **FR-006**: System MUST include a success fixture covering all seven target output types.
- **FR-007**: System MUST include no-runtime and negative fixtures for missing output type, unsupported output type, aggregate derived-context evidence, candidate-as-evidence, graph-as-evidence, memory-as-evidence, agent-reasoning-as-evidence, temporal-KG-as-evidence, missing table cell evidence, missing file lifecycle/hash refs, missing dataset item evidence, missing fact verification, and missing replay.
- **FR-008**: System MUST register output coverage contracts, commands, events, fixtures, and target area coverage.
- **FR-009**: System MUST provide a `veracrawl-output-coverage` fixture runner that validates manifests and writes `run_report.json`.
- **FR-010**: System MUST keep core independent of concrete storage, queues, export targets, agent frameworks, model SDKs, browser runtimes, HTTP clients, and site-specific scrapers.
- **FR-011**: System MUST document output coverage usage, fixture acceptance, and non-completion boundaries without claiming external export delivery or production storage completion.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **OutputTypeCoverageRecord**: Per-output-type proof that source evidence, verification, publication, manifest, lifecycle, and replay refs are present.
- **OutputTypePublicationGateReport**: Operator/replay-facing report proving every target output type passes or identifying typed coverage failures.
- **OutputTypeCoverageFixtureManifest**: Deterministic fixture declaration for success, needs-review, and negative output coverage scenarios.

### Non-Goals *(mandatory)*

- This feature does not implement external export delivery, warehouse/database/object-store writes, production persistence, browser rendering, model calls, or agent framework integration.
- This feature does not make graph, memory, agent reasoning, temporal KG, or candidates valid source evidence for publication.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Success fixture emits seven `OutputTypeCoverageRecord` refs and a pass report covering all target output types.
- **SC-002**: Type-specific refs are present for table rows/cells, document metadata fields, document sections, file hash/lifecycle, dataset items, and fact verification.
- **SC-003**: Derived-context evidence, candidate-as-evidence, graph-as-evidence, memory-as-evidence, agent-reasoning-as-evidence, temporal-KG-as-evidence, missing output type, unsupported output type, missing table cell evidence, missing file lifecycle/hash refs, missing dataset evidence, missing fact verification, and missing replay fixtures fail deterministically.
- **SC-004**: Runtime-unavailable fixture returns `needs_review`.
- **SC-005**: Registry validation includes every output coverage contract, command, event, fixture, and target area coverage.
- **SC-006**: Import-boundary tests prove output coverage runtime and CLI do not import concrete storage, queue, export, browser, model, agent framework, HTTP, or scraper dependencies.
- **SC-007**: Full local output coverage fixture gate completes within 30 seconds.

## Assumptions

- Deterministic fixtures use stable refs from existing evidence/publication and lifecycle slices instead of external storage.
- Export delivery and withdrawal are validated by export specs; this slice validates publication readiness for output types before export.
