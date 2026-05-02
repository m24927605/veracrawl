# Implementation Plan: VeraCrawl Advanced Graph Projection Spine

**Branch**: `009-advanced-graph-projection` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/009-advanced-graph-projection/spec.md`

## Summary

Implement replayable advanced graph projection contracts and deterministic fixture runtime on top of the basic site graph spine. The slice adds projection specs, rebuild jobs, mismatch reports, graph deltas, graph quality reports, graph signals, temporal graph projection records, and negative evidence-boundary fixtures.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard library.  
**Storage**: Stable refs and deterministic fixture reports only. Production graph store remains out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and deterministic CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local advanced graph gate completes within 30 seconds; success fixtures report zero missing replay refs.  
**Constraints**: Graph signals cannot satisfy evidence; no concrete graph store/browser/network/storage/model/agent/memory/export coupling.  
**Scale/Scope**: Advanced graph projection contracts, deterministic rebuild/mismatch behavior, signal contracts, temporal graph foundation, and fixtures.  
**VeraCrawl Owner Services**: `graph`, `projection`, `review_replay`, `policy`, `contracts`, and `tests` are directly affected.  
**Canonical Contracts**: ProjectionSpec, ProjectionRebuildJob, ProjectionMismatchReport, GraphDeltaReport, GraphSignal, GraphQualityReport, TemporalGraphProjectionRecord, AdvancedGraphProjectionReport, AdvancedGraphFixtureManifest.  
**Replay/Artifact Impact**: Replay requires projection spec refs, rebuild job refs, delta refs, quality refs, signal refs, temporal record refs, watermark refs, policy refs, command/event/outbox refs, and mismatch/failure refs.  
**Security/Policy Impact**: Graph refs are diagnostics/planning signals only and cannot replace source evidence for publication.

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected graph signals and temporal records.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/009-advanced-graph-projection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── projection-build.md
│   ├── graph-signal-boundary.md
│   └── fixture-oracle.md
└── tasks.md

src/veracrawl/
├── contracts/graph.py
├── graph/projection.py
├── review_replay/graph.py
└── cli/projection.py

tests/
├── contract/test_advanced_graph_projection_contract_registry.py
├── contract/test_advanced_graph_projection_contracts.py
├── contract/test_advanced_graph_projection_import_boundaries.py
├── unit/test_advanced_graph_projection.py
├── unit/test_advanced_graph_replay.py
├── unit/test_graph_signal_evidence_boundary.py
└── integration/test_advanced_graph_projection_fixtures.py
```

**Structure Decision**: Extend cohesive graph/projection contracts and graph owner-service runtime behind stable refs. No concrete graph store adapter is introduced in this slice.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design And Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

- [x] Projection records are generic and do not encode a site.
- [x] Graph signals cannot satisfy evidence or publication requirements.
- [x] Replay refs are required for projection specs, rebuild jobs, deltas, quality reports, signals, temporal records, watermarks, commands, events, and outbox records.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
