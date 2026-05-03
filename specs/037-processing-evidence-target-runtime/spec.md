# Feature Specification: VeraCrawl Processing/Evidence Target Runtime Gate

**Feature Branch**: `037-processing-evidence-target-runtime`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Build VeraCrawl Processing/Evidence Target Runtime Gate: extend adapter-backed target runtime so declared adapter-backed sources must produce processing/evidence/publication lineage records: normalized document refs, extraction candidate refs, evidence packet refs, evidence anchor refs, publication report refs, policy refs, and replay refs. Core must remain framework-neutral and adapter-neutral; CLI/adapters may materialize deterministic local processing/evidence records outside core. Negative fixtures must fail on missing normalization, missing candidate anchors, missing evidence packet, graph-only/derived-context-as-evidence, and publication bypass. Do not implement a single-site scraper."

## Hard Constraints

- **General-purpose crawler**: The implementation models canonical processing/evidence gates across website patterns, not a single-site scraper.
- **Adapter/core boundary**: Target runtime core accepts canonical records only. Deterministic processing/evidence materialization belongs outside core.
- **Evidence integrity**: Graph, memory, AI reasoning, or derived context refs cannot satisfy source evidence requirements.
- **Non-deceptive completion**: A complete report requires processing/evidence/publication lineage when a processing evidence manifest is declared.

## User Stories & Testing

### User Story 1 - Complete Processing/Evidence Lineage (Priority: P1)

As a crawler platform engineer, I need adapter-backed sources to produce normalized documents, extraction candidates, evidence packets, evidence anchors, and publication report refs before target runtime can complete.

**Independent Test**: Run `veracrawl-target-runtime run tests/fixtures/processing-evidence-target-success --profile target --out .veracrawl-test-runs/processing-evidence-target-success`; the report passes only with seven processing/evidence records.

### User Story 2 - Block False Evidence (Priority: P2)

As a Staff reviewer, I need the runtime to fail when processing/evidence lineage is missing, graph-only, or bypassed.

**Independent Test**: Negative processing/evidence fixtures fail with typed target runtime failures and cannot produce `complete`.

### User Story 3 - Preserve Core Neutrality (Priority: P3)

As a maintainer, I need processing/evidence materialization to stay outside target runtime core.

**Independent Test**: Import-boundary tests prove `veracrawl.target_runtime` imports no concrete adapters, processing materializers, agent frameworks, or SDKs.

## Edge Cases

- Processing manifest references an adapter-backed source that does not exist.
- Normalized document ref is missing.
- Extraction candidate exists without candidate anchor refs.
- Evidence packet exists but evidence anchor refs are missing.
- Graph-only refs attempt to satisfy source evidence.
- Publication report claims output without evidence lineage.

## Requirements

- **FR-001**: System MUST define processing/evidence target runtime contracts for entries, manifests, and records.
- **FR-002**: System MUST allow `TargetRuntimeFixtureManifest` to reference a processing/evidence manifest.
- **FR-003**: System MUST aggregate normalized document, extraction candidate, evidence packet, evidence anchor, and publication report refs on `TargetRuntimeReport`.
- **FR-004**: System MUST fail missing normalization, missing candidate anchors, missing evidence packet, graph-only evidence, and publication bypass fixtures.
- **FR-005**: System MUST preserve existing 034, 035, and 036 target runtime fixture behavior.
- **FR-006**: System MUST register contracts, commands/events, fixtures, and target area coverage.

## Key Entities

- **TargetProcessingEvidenceEntry**: Declares required processing/evidence lineage for one adapter-backed source.
- **TargetProcessingEvidenceManifest**: Declares processing/evidence requirements for a target runtime fixture.
- **TargetProcessingEvidenceRecord**: Canonical proof record tying adapter-backed source refs to normalized documents, extraction candidates, evidence packets, anchors, publication reports, policy, and replay refs.

## Success Criteria

- **SC-001**: Processing/evidence success completes with seven records.
- **SC-002**: Every processing/evidence accepted output includes normalized document, extraction candidate, evidence packet, evidence anchor, publication report, policy, and replay refs.
- **SC-003**: Negative fixtures fail deterministically with typed target runtime failures.
- **SC-004**: Full non-Docker and Docker-backed gates pass.
