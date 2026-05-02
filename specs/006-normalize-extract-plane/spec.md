# Feature Specification: VeraCrawl Normalize and Extract Plane

**Feature Branch**: `006-normalize-extract-plane`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Normalize and Extract Plane：在已完成的 network/browser acquisition runtime 之上，實作 normalized document、normalization manifest、anchor map、link extraction、link provenance、page type classification、site model、extraction strategy、extraction candidate 基礎，必須保留 raw snapshot 到 normalized text/anchor/candidate 的 replay lineage；必須遵守 docs/07、08、09、10、11 與 constitution；不得實作成單站 scraper，不得讓 model-generated candidate 直接成為 published output；core 不得耦合 agent framework、model SDK、browser、storage、queue 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature builds generic HTML normalization, anchor mapping, link provenance, page classification, site model, and extraction candidate records without website-specific selectors or vertical schemas.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `005-browser-network-acquisition`, aligned with `docs/08-build-roadmap.md` Phase 2 Fetch and Normalize Plane.
- **Evidence and replay impact**: The feature affects raw snapshot refs, normalized document refs, normalization manifests, anchor maps, link provenance, page type classification, site model refs, extraction strategies, extraction candidates, and replay reports.
- **Safety and policy impact**: Untrusted HTML remains source input, normalized text cannot become publication evidence by itself, model-generated or heuristic candidates remain unpublished until evidence and verification gates pass.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Normalize Raw HTML Into Replayable Documents (Priority: P1)

As a crawler runtime, I need raw HTML snapshots to become normalized text documents with manifests and anchor maps so later evidence packets can replay from raw source to normalized spans.

**Why this priority**: Extraction and evidence cannot be trusted without deterministic raw-to-normalized lineage.

**Independent Test**: Run `veracrawl-process run tests/fixtures/process-static-basic --profile target --out .veracrawl-test-runs/process-static-basic`; the run performs local HTTP acquisition, normalizes HTML, emits a manifest, anchor map, and replay-complete processing report.

**Acceptance Scenarios**:

1. **Given** a raw HTML artifact from local HTTP acquisition, **When** normalization runs, **Then** it emits normalized document, normalized artifact ref, normalization manifest, anchor map, content digest, and replay refs.
2. **Given** malformed or empty content, **When** normalization runs, **Then** the output is failed or needs-review with typed diagnostics and no accepted extraction candidate.

---

### User Story 2 - Extract Links With Provenance And Classify Page Types (Priority: P2)

As a planner, I need discovered links, canonical refs, and page type classifications to point back to source anchors so future frontier and graph work can use provenance instead of opaque scraped URLs.

**Why this priority**: General-purpose crawling needs page understanding and link provenance before graph intelligence can be reliable.

**Independent Test**: Link provenance fixtures verify every discovered link has normalized document refs, anchor refs, source URL refs, and page classification metadata.

**Acceptance Scenarios**:

1. **Given** a normalized listing-like page, **When** link extraction runs, **Then** every link has `LinkProvenance` with source document, href, anchor text, and anchor ref.
2. **Given** listing/detail/search/document page signals, **When** classification runs, **Then** the page type classification and site model records are replayable and do not satisfy evidence requirements by themselves.

---

### User Story 3 - Create Anchored Extraction Candidates (Priority: P3)

As an extraction runtime, I need extraction strategies and candidates to preserve field anchors and remain separate from published outputs so candidate quality can be reviewed before evidence and publication.

**Why this priority**: Candidates are useful intermediate records, but publishing them without evidence would violate VeraCrawl's core product rule.

**Independent Test**: Candidate fixtures create anchored candidates from normalized documents and negative fixtures fail when candidate fields lack anchors.

**Acceptance Scenarios**:

1. **Given** normalized text and anchors, **When** an extraction strategy runs, **Then** it produces an `ExtractionCandidate` with field values, field anchor refs, confidence refs, and strategy refs.
2. **Given** a candidate field without an anchor, **When** validation runs, **Then** the process report fails and no publication output is produced.

### Edge Cases

- Raw HTML artifact ref is missing.
- Raw HTML body is empty after normalization.
- HTML is malformed enough that required anchors cannot be produced.
- Link href is relative, empty, duplicated, or points outside current source scope.
- Page type signals conflict.
- Extraction candidate has field values without anchors.
- Candidate tries to claim publication status before evidence and verification.
- Replay-critical raw, normalized, anchor, manifest, link, strategy, candidate, command, event, or policy refs are missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define normalization manifest, text anchor, anchor map, link provenance, page type classification, site model, extraction strategy, normalize/extract report, and process fixture manifest contracts.
- **FR-002**: System MUST normalize raw HTML into deterministic normalized text using general HTML parsing rules, not site-specific selectors.
- **FR-003**: System MUST preserve raw artifact refs, normalized artifact refs, anchor map refs, normalization manifest refs, content digests, and replay refs.
- **FR-004**: System MUST extract links with source document refs, href refs, anchor text refs, anchor refs, and provenance status.
- **FR-005**: System MUST classify basic page types from generic signals and record a site model summary.
- **FR-006**: System MUST create extraction strategy records and extraction candidates with field anchors and confidence refs.
- **FR-007**: System MUST reject candidates with missing anchors and prevent candidates from becoming published outputs in this feature.
- **FR-008**: System MUST build normalize/extract replay reports that validate raw, normalized, anchor, manifest, link, classification, site model, strategy, candidate, policy, command, event, outbox, and acquisition refs.
- **FR-009**: System MUST include success fixtures for static normalization, link provenance, and anchored extraction.
- **FR-010**: System MUST include negative fixtures for missing raw artifact, empty normalized content, and missing candidate anchor.
- **FR-011**: System MUST register contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-012**: System MUST keep core independent of concrete browser, HTTP client, storage, queue, model SDK, agent framework, and site-specific scraper dependencies.
- **FR-013**: System MUST document implemented normalize/extract capability and explicitly avoid claiming evidence/publication, graph intelligence, memory intelligence, export, distributed persistence, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **NormalizationManifest**: Transformation version, raw input refs, normalized output refs, anchor map refs, parser refs, and content digests.
- **TextAnchor**: Stable source-to-normalized span mapping.
- **AnchorMap**: Collection of anchors for a normalized document.
- **LinkProvenance**: Discovered link with source document, href, text, anchor, policy, and provenance refs.
- **PageTypeClassification**: Generic page type decision with signal refs and confidence refs.
- **SiteModel**: Run-scoped summary of page types, canonical refs, and discovered link refs.
- **ExtractionStrategy**: Generic strategy record for candidate creation.
- **NormalizeExtractReport**: Replay-facing processing report.

### Non-Goals *(mandatory)*

- This feature does not implement evidence packet building, verification decisions, published outputs, graph projection stores, memory, export, distributed persistence, or production scale crawling.
- This feature does not use LLM/model calls or agent frameworks for extraction.
- This feature does not implement site-specific selectors, one-off scraper logic, or vertical extraction rules.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Static process fixture performs local HTTP acquisition and emits normalized document, manifest, anchor map, process report, and replay refs with zero missing required refs.
- **SC-002**: Link provenance fixture emits at least one link provenance record with source document, href, anchor text, anchor ref, and policy refs.
- **SC-003**: Anchored extraction fixture emits extraction strategy and candidate records where every field value has an anchor ref.
- **SC-004**: Missing raw, empty content, and missing candidate anchor fixtures produce typed non-success reports with no publication refs.
- **SC-005**: Registry validation includes every normalize/extract contract, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core normalize/extract packages do not import concrete browser, HTTP client, storage, queue, model SDK, agent framework, or site-specific scraper dependencies.
- **SC-007**: Full local normalize/extract gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- Local deterministic HTTP benchmark server from `005` remains the acquisition source for process fixtures.
- HTML parsing uses Python standard-library parsing in core because it is not a concrete network/browser/model dependency.
- Extraction candidates are heuristic fixture records only and cannot be published until later evidence, verification, and publication specs pass.
