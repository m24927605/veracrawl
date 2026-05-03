# Implementation Plan: Graph And Memory Production Runtime

**Branch**: `051-graph-memory-production-runtime` | **Date**: 2026-05-03 | **Spec**: `specs/051-graph-memory-production-runtime/spec.md`
**Input**: Feature specification from `/specs/051-graph-memory-production-runtime/spec.md`

## Summary

Implement roadmap row 051 by adding a deterministic production runtime aggregate
that composes live normalization, live evidence, multi-agent repair, advanced
graph projection, graph frontier/review, temporal KG, and memory kernel refs.
The aggregate proves graph and memory can influence frontier and repair
decisions while source evidence, verification, policy, command/event/outbox, and
replay remain mandatory for publication eligibility.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl contracts/runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, framework-neutral core, graph/memory never source evidence  
**Scale/Scope**: target-architecture graph and memory production runtime slice for crawl planning, frontier prioritization, repair, and operator explanation  
**VeraCrawl Owner Services**: graph, memory, scheduler, agents, evidence, verify, review_replay, policy, tests  
**Canonical Contracts**: GraphMemoryProductionRuntimeReport, GraphMemoryProductionFixtureManifest, AdvancedGraphProjectionReport, GraphFrontierReviewRuntimeReport, TemporalKGRuntimeReport, MemoryKernelReport, MultiAgentRepairReport, LiveEvidenceVerificationRuntimeReport, LiveNormalizationRuntimeReport  
**Replay/Artifact Impact**: graph projection watermarks, memory freshness/invalidation refs, frontier decisions, repair explanations, command/event/outbox refs, replay bundle refs  
**Security/Policy Impact**: graph/memory signal policy, prompt context policy, memory taint/freshness policy, graph/memory-as-evidence denial, replay and operator auditability

## Constitution Check

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
specs/051-graph-memory-production-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/graph-memory-production-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{enums.py,graph_memory.py,registry.py,__init__.py}
src/veracrawl/graph_memory/{__init__.py,runtime.py}
src/veracrawl/review_replay/graph_memory.py
src/veracrawl/cli/graph_memory_runtime.py
tests/contract/test_graph_memory_production_*.py
tests/unit/test_graph_memory_production_*.py
tests/integration/test_graph_memory_production_fixtures.py
tests/helpers/graph_memory_production_fixture_assertions.py
tests/fixtures/graph-memory-*/...
```

**Structure Decision**: create a `graph_memory` owner package because row 051 is
an integration aggregate spanning graph, memory, scheduler, agents, evidence,
and review/replay. Existing graph and memory contracts remain authoritative for
their own owner services; the new package owns only the production runtime
completion report and fixture gate.

## Complexity Tracking

No constitution violations.
