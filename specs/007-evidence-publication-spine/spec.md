# Feature Specification: VeraCrawl Evidence and Publication Spine

**Feature Branch**: `007-evidence-publication-spine`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Evidence and Publication Spine：在 normalize/extract plane 之上，實作 evidence anchor coverage、evidence packet、verification decision、review decision、published output、output manifest、publication policy gates、candidate-not-output boundary、replay completeness、fixture/oracle 測試基礎。必須遵守 docs/07、08、09、10、11 與 constitution；不得讓 extraction candidate 直接成為 published output；不得實作成單站 scraper；core 不得耦合 agent framework、model SDK、browser、storage、queue 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature implements generic field-level evidence, verification, review, and publication gates for arbitrary schemas and websites. It does not encode one site, selector, or vertical output shape.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `006-normalize-extract-plane`, aligned with `docs/08-build-roadmap.md` Phase 3 Evidence Spine and Basic Site Graph for the evidence/publication portion only.
- **Evidence and replay impact**: The feature affects evidence anchors, evidence coverage, evidence packets, evidence packet manifests, verification decisions, review decisions, published outputs, output manifests, publication reports, policy decisions, command/event/outbox refs, and replay completeness checks.
- **Safety and policy impact**: Extraction candidates remain unpublished until evidence coverage, accepted verification, review, publication policy, privacy lifecycle refs, and replay refs pass. Graph, memory, agent reasoning, and candidates cannot satisfy source evidence by themselves.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build Field Evidence Coverage (Priority: P1)

As the publication pipeline, I need every candidate field to map to source-backed evidence anchors so no candidate can be treated as an output without auditable provenance.

**Why this priority**: Evidence coverage is the core safety boundary between extraction candidates and published outputs.

**Independent Test**: Run `veracrawl-evidence run tests/fixtures/evidence-field-coverage --profile target --out .veracrawl-test-runs/evidence-field-coverage`; the fixture creates a generic candidate, evidence anchors, coverage result, packet, manifest, and replay-complete evidence report without publishing.

**Acceptance Scenarios**:

1. **Given** a candidate with anchored fields, **When** evidence coverage runs, **Then** it emits evidence anchors, source evidence refs, coverage result, evidence packet, evidence manifest, and replay refs for every required field.
2. **Given** a candidate field with no usable evidence anchor, **When** evidence coverage runs, **Then** coverage is non-pass and no publication output is created.

---

### User Story 2 - Verify And Review Evidence Before Publication (Priority: P2)

As a reviewer or verification service, I need evidence packets to produce explicit accept, reject, review, or conflict decisions so publication can block ambiguous or contradictory outputs.

**Why this priority**: Evidence is not sufficient by itself; verification and review decisions are required to prevent silent bad data.

**Independent Test**: Verification fixtures emit accepted decisions for complete evidence and typed non-publication reports for conflicts.

**Acceptance Scenarios**:

1. **Given** a complete evidence packet and allow policy, **When** verification and review run, **Then** accepted verification and review decisions are recorded with evidence and policy refs.
2. **Given** contradictory evidence or conflict flag, **When** verification runs, **Then** conflict refs are recorded and publication is blocked.

---

### User Story 3 - Publish Only After Gates Pass (Priority: P3)

As a data consumer, I need published outputs and manifests to exist only after evidence, verification, review, policy, privacy, and replay gates pass.

**Why this priority**: Published outputs are the user-visible contract and must be immutable, evidence-backed, and replayable.

**Independent Test**: Publication fixtures prove success publication and negative gates for policy denial, replay gap, and direct candidate publication.

**Acceptance Scenarios**:

1. **Given** coverage pass, accepted verification, accepted review, allow publication policy, privacy refs, and replay refs, **When** publication runs, **Then** it emits a published output, output manifest, manifest hash, and pass publication report.
2. **Given** a candidate attempts direct publication without evidence or verification, **When** publication runs, **Then** the attempt fails with typed diagnostics and no output manifest.

### Edge Cases

- Candidate field lacks a usable field anchor ref.
- Evidence packet includes only graph, memory, or agent reasoning refs without source evidence or approved prior output.
- Evidence coverage is incomplete.
- Verification decision is reject, review, or conflict.
- Review decision is reject, review, or conflict.
- Publication policy denies or requires review.
- Privacy lifecycle refs are absent.
- Replay-critical evidence, verification, review, output, command, event, outbox, policy, artifact, or manifest refs are missing.
- Candidate is marked or treated as published before evidence and verification pass.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define evidence anchor, evidence packet manifest, review decision, publication report, and evidence publication fixture manifest contracts.
- **FR-002**: System MUST build field-level evidence coverage from extraction candidate fields and source-backed anchor refs.
- **FR-003**: System MUST reject or mark needs-review when required fields lack source evidence anchors.
- **FR-004**: System MUST build evidence packets that distinguish source evidence refs from graph, memory, agent reasoning, and prior verified output refs.
- **FR-005**: System MUST prevent graph, memory, agent reasoning, or unverified candidates from satisfying source evidence coverage.
- **FR-006**: System MUST create verification decisions with accepted, rejected, review, or conflict outcomes and policy refs.
- **FR-007**: System MUST create review decisions that point to verification, evidence packet, reviewer/authority refs, and policy refs.
- **FR-008**: System MUST publish output manifests only when evidence coverage passes, verification accepts, review accepts, publication policy allows, privacy lifecycle refs exist, and replay refs are complete.
- **FR-009**: System MUST reject direct candidate publication attempts before a `PublishedOutput` or `OutputManifest` is created.
- **FR-010**: System MUST build publication replay reports that validate evidence, verification, review, publication, policy, artifact, command, event, outbox, and replay refs.
- **FR-011**: System MUST include success fixtures for field coverage, verification/review, and publication.
- **FR-012**: System MUST include negative fixtures for missing evidence anchor, verification conflict, publication policy denial, replay gap, and direct candidate publication.
- **FR-013**: System MUST register contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-014**: System MUST keep core independent of concrete browser, HTTP client, storage, queue, model SDK, agent framework, graph store, memory store, export target, and site-specific scraper dependencies.
- **FR-015**: System MUST document implemented evidence/publication capability and explicitly avoid claiming graph, memory, export, distributed persistence, production browser rendering, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **EvidenceAnchor**: Field-level evidence mapping from a candidate field to normalized document, raw artifact, text anchor, text digest, and privacy/policy refs.
- **EvidencePacketManifest**: Replayable evidence bundle manifest for packet, coverage, anchors, source artifacts, normalized documents, privacy lifecycle, and policy refs.
- **ReviewDecision**: Review/authority decision that gates publication after verification.
- **PublicationReport**: Replay-facing report of publication success or typed gate failure.
- **EvidencePublicationFixtureManifest**: Deterministic fixture manifest for success and negative evidence/publication scenarios.

### Non-Goals *(mandatory)*

- This feature does not implement graph projections, memory kernel, export connectors, export withdrawal, distributed persistence, production browser rendering, production queue workers, UI review console, or production scale crawling.
- This feature does not use LLM/model calls or external agent frameworks for verification.
- This feature does not implement site-specific selectors, one-off scraper logic, or vertical publication rules.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Field coverage fixture emits evidence anchors for 100% of required candidate fields and a pass evidence coverage result.
- **SC-002**: Verification/review fixture emits accepted verification and review decisions with evidence and policy refs.
- **SC-003**: Publication fixture emits `PublishedOutput`, `OutputManifest`, manifest hash, and pass publication report only after all gates pass.
- **SC-004**: Missing evidence, verification conflict, publication policy denial, replay gap, and direct candidate publication fixtures produce typed non-success reports with no output manifest.
- **SC-005**: Registry validation includes every evidence/publication contract, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core evidence/verification/publication packages do not import concrete browser, HTTP client, storage, queue, model SDK, agent framework, graph store, memory store, export target, or site-specific scraper dependencies.
- **SC-007**: Full local evidence/publication gate completes within 30 seconds in the deterministic fixture profile.

## Assumptions

- The input candidate shape is the generic `ExtractionCandidate` produced by the normalize/extract plane.
- Fixture evidence anchors use deterministic text hashes and stable refs instead of object storage.
- Review decisions are deterministic fixture records in this slice; a UI review console is a later spec.
- Output materialization remains an immutable manifest and fixture report; export delivery is a later spec.
