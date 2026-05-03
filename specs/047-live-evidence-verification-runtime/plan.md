# Implementation Plan: Live Evidence And Verification Runtime

**Branch**: `047-live-evidence-verification-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/047-live-evidence-verification-runtime/spec.md`

## Summary

Add a live evidence and verification runtime aggregate that consumes row 046
schema extraction candidates and materializes source-backed evidence coverage,
evidence packets, evidence anchors, evidence manifests, verification decisions,
review decisions, conflict/contradiction diagnostics, command/event/outbox refs,
privacy refs, policy refs, and replay refs without publication refs.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; existing evidence coverage and verification helpers
**Storage**: Fixture output reports; no new database coupling
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic local evidence/verification over bounded fixture candidates
**Constraints**: Core cannot import concrete source/network/browser adapters, storage clients, model SDKs, agent frameworks, export destinations, or site-specific scrapers
**Scale/Scope**: One pass fixture plus typed missing/stale/contradictory/non-source/replay/publication-bypass fixtures
**VeraCrawl Owner Services**: evidence, verify, review_replay, runtime_events, tests
**Canonical Contracts**: LiveEvidenceVerificationRuntimeReport, LiveEvidenceVerificationFixtureManifest, EvidenceCoverageResult, EvidencePacket, EvidenceAnchor, EvidencePacketManifest, VerificationDecision, ReviewDecision
**Replay/Artifact Impact**: candidate refs, source anchors, evidence anchors, manifests, verification/review refs, command/event/outbox refs, and replay refs required for pass
**Security/Policy Impact**: graph/memory/agent reasoning are diagnostic only; no publication refs may be emitted

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through contracts and runtime input boundaries.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Graph, memory, and AI reasoning are not source evidence.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/047-live-evidence-verification-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/live-evidence-verification-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/evidence.py
src/veracrawl/evidence/live_verification.py
src/veracrawl/cli/live_evidence.py
tests/fixtures/live-evidence-verification-*/
```

## Complexity Tracking

No constitution violations are introduced.
