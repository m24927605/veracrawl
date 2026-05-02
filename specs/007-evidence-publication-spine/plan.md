# Implementation Plan: VeraCrawl Evidence and Publication Spine

**Branch**: `007-evidence-publication-spine` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/007-evidence-publication-spine/spec.md`

## Summary

Implement deterministic evidence coverage, evidence packet manifesting, verification,
review, and publication gates on top of extraction candidates. The implementation
keeps candidates separate from published outputs and proves source-backed evidence,
verification, publication policy, privacy refs, and replay refs before output
manifest creation.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard library.  
**Storage**: Stable refs and deterministic fixture reports only. Production metadata/object storage remains out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and deterministic CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local evidence/publication gate completes within 30 seconds; success fixtures report zero missing publication replay refs.  
**Constraints**: No direct candidate publication; no graph/memory refs as source evidence; no model SDK or agent framework coupling.  
**Scale/Scope**: Field evidence coverage, evidence packet manifest, verification/review decisions, publication report, output manifest gate, and negative fixtures.  
**VeraCrawl Owner Services**: `evidence`, `verify`, `publish`, `review_replay`, `policy`, `contracts`, and `tests` are directly affected.  
**Canonical Contracts**: EvidenceCoverageResult, EvidencePacket, EvidenceAnchor, EvidencePacketManifest, VerificationDecision, ReviewDecision, PublishedOutput, OutputManifest, PublicationReport, EvidencePublicationFixtureManifest.  
**Replay/Artifact Impact**: Replay requires candidate refs, evidence anchor refs, evidence packet refs, evidence manifest refs, coverage refs, verification refs, review refs, published output refs, output manifest refs, policy refs, privacy lifecycle refs, command/event/outbox refs, artifact refs, and replay bundle refs.  
**Security/Policy Impact**: Publication policy and privacy lifecycle refs are mandatory for pass; source evidence cannot be replaced by graph, memory, agent reasoning, or unverified candidate refs.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-check after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/007-evidence-publication-spine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── evidence-coverage.md
│   ├── verification-review.md
│   ├── publication-gates.md
│   └── fixture-oracle.md
└── tasks.md

src/veracrawl/
├── contracts/evidence.py
├── contracts/verification.py
├── contracts/publication.py
├── evidence/coverage.py
├── verify/review.py
├── publish/gates.py
├── review_replay/publication.py
└── cli/evidence.py

tests/
├── contract/test_evidence_publication_contract_registry.py
├── contract/test_evidence_publication_contracts.py
├── contract/test_evidence_publication_import_boundaries.py
├── unit/test_evidence_coverage.py
├── unit/test_verification_review.py
├── unit/test_publication_gates.py
├── unit/test_publication_replay.py
└── integration/test_evidence_publication_fixtures.py
```

**Structure Decision**: Extend existing evidence, verification, and publication
contracts with spine-specific contracts, add cohesive owner-service modules, and
add a deterministic CLI runner. The feature consumes generic extraction candidates
through contracts rather than coupling to a concrete crawler, browser, storage,
model, graph, memory, or export implementation.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design And Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

- [x] Evidence and publication gates are schema-generic and do not encode a site.
- [x] Candidates remain intermediate records and cannot create output manifests directly.
- [x] Replay refs are required for evidence, verification, review, publication, policy, privacy, command, event, and outbox records.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
