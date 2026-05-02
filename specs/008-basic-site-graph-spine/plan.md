# Implementation Plan: VeraCrawl Basic Site Graph Spine

**Branch**: `008-basic-site-graph-spine` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/008-basic-site-graph-spine/spec.md`

## Summary

Implement deterministic URL, hyperlink, redirect/canonical, and page-structure
graph records with build manifests, edge provenance, projection watermarks, and
replay reports. Graph signals remain planning diagnostics and cannot satisfy
publication evidence.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard library.  
**Storage**: Stable refs and deterministic fixture reports only. Production graph store remains out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and deterministic CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local graph gate completes within 30 seconds; success fixtures report zero missing graph replay refs.  
**Constraints**: Graph signals cannot satisfy evidence; no concrete graph store/browser/network/storage/model/agent coupling.  
**Scale/Scope**: URL, hyperlink, redirect/canonical, page-structure graph, graph manifest, watermark, replay reports, and negative fixtures.  
**VeraCrawl Owner Services**: `graph`, `projection`, `review_replay`, `policy`, `contracts`, and `tests` are directly affected.  
**Canonical Contracts**: GraphNode, GraphEdge, GraphEdgeProvenance, GraphBuildManifest, ProjectionWatermark, GraphBuildReport, GraphFixtureManifest.  
**Replay/Artifact Impact**: Replay requires input refs, node refs, edge refs, provenance refs, manifest refs, watermark refs, policy refs, command/event/outbox refs, and rebuild hash.  
**Security/Policy Impact**: Graph refs are diagnostics/planning signals only and cannot replace source evidence for publication.

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
specs/008-basic-site-graph-spine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── graph-build.md
│   ├── graph-boundary.md
│   └── fixture-oracle.md
└── tasks.md

src/veracrawl/
├── contracts/graph.py
├── graph/build.py
├── review_replay/graph.py
└── cli/graph.py

tests/
├── contract/test_graph_contract_registry.py
├── contract/test_graph_contracts.py
├── contract/test_graph_import_boundaries.py
├── unit/test_graph_build.py
├── unit/test_graph_replay.py
├── unit/test_graph_evidence_boundary.py
└── integration/test_graph_fixtures.py
```

**Structure Decision**: Add cohesive graph contracts and graph owner-service
runtime behind stable refs. No concrete graph store adapter is introduced in this
slice.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design And Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

- [x] Graph records are generic and do not encode a site.
- [x] Graph refs cannot satisfy evidence or publication requirements.
- [x] Replay refs are required for graph manifests, nodes, edges, provenance, watermarks, commands, events, and outbox records.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
