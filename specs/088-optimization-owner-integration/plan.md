# Implementation Plan: Optimization Owner-Service Integration Roadmap

**Branch**: `088-optimization-owner-integration` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/088-optimization-owner-integration/spec.md`

## Summary

Define and implement the finite post-087 optimization owner-service integration
set. Specs 089-096 activate the optimization runtime outputs from specs 080-087
through adapter-free owner-service modules for scheduler, normalize,
extract/verify, dedupe/identity, publish/ranking, ops cost/cache, drift
feedback, and aggregate regression release gating.

The implementation will add typed integration contracts, cohesive service
modules, replay validation, registry entries, and focused tests. It must not
import benchmark runners, external adapters, browser engines, model SDKs, queue
clients, storage clients, or agent frameworks into core integration code.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: Existing VeraCrawl Pydantic contracts, owner-service
packages, runtime optimization services, replay helpers, pytest, ruff, mypy
**Storage**: No new persistence adapter; deterministic refs and existing port
boundaries only
**Testing**: pytest contract, unit, replay, import-boundary, and full regression
suite
**Target Platform**: VeraCrawl Python crawler runtime and owner-service packages
**Project Type**: Python package with Spec Kit artifacts and deterministic tests
**Performance Goals**: Preserve 087 runtime behavior while making owner-service
integration measurable; fail stale cache, budget overrun, duplicate/ranking
regression, unsafe recovery, and replay gaps deterministically
**Constraints**: General-purpose crawler only; Python; framework-neutral;
adapter-free core; source-backed evidence; no unsafe source access; no benchmark
imports in owner-service integration modules
**Scale/Scope**: Integration spans specs 089-096 and owner packages:
`scheduler`, `normalize`, `extract`, `verify`, `graph`, `publish`,
`projection`, `ops`, `review_replay`, and `contracts`
**VeraCrawl Owner Services**: scheduler, normalize, extract, verify, graph,
publish, projection, ops, review_replay, artifact_lifecycle
**Canonical Contracts**: Optimization owner integration roadmap, scheduler
integration, normalize integration, extract/verify integration, dedupe/identity
integration, ranking/publication integration, cost/cache/budget integration,
drift/recovery feedback integration, regression release gate
**Replay/Artifact Impact**: Every integration output must carry policy refs,
command/event/outbox refs, artifact refs where applicable, lower decision refs,
metric refs, and replay refs
**Security/Policy Impact**: Preserve source scope, robots/terms,
private-network denial, credential isolation, browser approval, prompt-taint,
privacy lifecycle, cache freshness, no-bypass rules, and publication gates

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off
  scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution
  amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks
  are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports,
  commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are
  defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle,
  retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions,
  fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint
  pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/088-optimization-owner-integration/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── owner-service-integration.md

specs/089-priority-frontier-scheduler-integration/spec.md
specs/090-dom-intelligence-normalize-integration/spec.md
specs/091-extraction-fallback-verification-integration/spec.md
specs/092-canonical-dedupe-identity-integration/spec.md
specs/093-recommendation-ranking-publication-integration/spec.md
specs/094-optimization-cost-cache-budget-runtime/spec.md
specs/095-drift-recovery-feedback-runtime/spec.md
specs/096-optimization-regression-release-gate/spec.md
```

### Source Code

```text
src/veracrawl/contracts/crawler_optimization.py
src/veracrawl/contracts/registry.py
src/veracrawl/scheduler/optimization_integration.py
src/veracrawl/normalize/optimization_integration.py
src/veracrawl/extract/optimization_integration.py
src/veracrawl/graph/optimization_integration.py
src/veracrawl/publish/optimization_integration.py
src/veracrawl/ops/optimization_integration.py
src/veracrawl/review_replay/crawler_optimization_owner_integration.py
tests/contract/test_crawler_optimization_owner_integration_contracts.py
tests/contract/test_crawler_optimization_owner_integration_registry.py
tests/contract/test_crawler_optimization_owner_integration_import_boundaries.py
tests/unit/test_crawler_optimization_owner_integration.py
tests/unit/test_crawler_optimization_owner_integration_replay.py
```

**Structure Decision**: Add thin owner-service integration modules in their
own owner packages. Shared typed contracts stay in `contracts`; shared replay
gap validation stays in `review_replay`. Integration modules may depend on
`veracrawl.optimization.runtime` and contracts but must not depend on
`veracrawl.benchmarks`, `veracrawl.adapters`, model providers, browser engines,
storage clients, or queue clients.

## Phase 0: Research

Research decisions are captured in [research.md](research.md).

## Phase 1: Design And Contracts

Data entities are captured in [data-model.md](data-model.md). Command/event and
owner-service contracts are captured in
[contracts/owner-service-integration.md](contracts/owner-service-integration.md).
Quickstart validation is captured in [quickstart.md](quickstart.md).

## Complexity Tracking

No constitution violations are introduced by this plan.
