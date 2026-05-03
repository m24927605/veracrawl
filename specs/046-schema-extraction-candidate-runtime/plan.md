# Implementation Plan: Schema Extraction Candidate Runtime

**Branch**: `046-schema-extraction-candidate-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/046-schema-extraction-candidate-runtime/spec.md`

## Summary

Add a schema extraction runtime aggregate that consumes row 045 live
normalization results and materializes extraction strategies, anchored
candidates, schema validation refs, framework-neutral model/tool trace refs,
candidate rejection/drift/repair diagnostics, command/event/outbox refs, and
replay refs without allowing candidates to become published outputs.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; existing normalization and extraction helpers; pytest/ruff/mypy
**Storage**: Fixture output reports; no new database coupling
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic local candidate generation over bounded fixture HTML
**Constraints**: Core cannot import concrete source/network/browser adapters, storage clients, model SDKs, agent frameworks, or site-specific scrapers
**Scale/Scope**: Three pass patterns plus seven negative/needs-review fixtures
**VeraCrawl Owner Services**: extract, normalize, runtime_events, review_replay, tests
**Canonical Contracts**: SchemaExtractionRuntimeReport, SchemaExtractionFixtureManifest, ExtractionStrategy, ExtractionCandidate, NormalizedDocument, TextAnchor
**Replay/Artifact Impact**: live normalization report refs, normalized refs, field anchor refs, schema validation refs, trace refs, event/outbox refs, and replay refs required for pass
**Security/Policy Impact**: candidates are intermediate; no publication/export refs may be emitted by this slice

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through contracts and runtime input boundaries.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Candidates are not source evidence or published output.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/046-schema-extraction-candidate-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/schema-extraction-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/processing.py
src/veracrawl/extract/schema_runtime.py
src/veracrawl/cli/schema_extraction.py
tests/fixtures/schema-extraction-*/
```

## Complexity Tracking

No constitution violations are introduced.
