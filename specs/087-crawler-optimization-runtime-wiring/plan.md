# Implementation Plan: Crawler Optimization Runtime Wiring

**Branch**: `087-crawler-optimization-runtime-wiring` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/087-crawler-optimization-runtime-wiring/spec.md`

## Summary

Wire the spec 080-086 optimization contracts into a runtime-safe service layer
that scheduler, normalization/extraction, projection, and ops flows can consume
without importing benchmark code or concrete adapters. The implementation adds
runtime decision contracts, deterministic fixture services, replay helpers, and
tests that prove policy blocking, DOM/extractor context, dedupe/ranking, and
metric aggregation can run through explicit owner-service boundaries.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Pydantic contracts, existing VeraCrawl runtime
contracts, deterministic helper utilities, pytest  
**Storage**: Existing production persistence ports where command/event/outbox
recording is required; runtime service outputs remain typed contracts and refs  
**Testing**: pytest contract, unit, replay, and import-boundary tests  
**Target Platform**: VeraCrawl Python crawler runtime and CLI/fixture surfaces  
**Project Type**: Python package with runtime service modules and contracts  
**Performance Goals**: Runtime fixtures must keep score/context/ranking
computation deterministic and bounded; DOM context must reduce raw HTML context
bytes by at least 50% in fixtures  
**Constraints**: No benchmark imports from runtime service; no concrete adapter,
model SDK, queue client, storage client, browser engine, or agent framework
dependency in core runtime wiring  
**Scale/Scope**: Scheduler/frontier scoring, DOM/extractor context, dedupe and
ranking, and ops aggregation for deterministic runtime fixtures  
**VeraCrawl Owner Services**: scheduler, normalize, extract, evidence, verify,
projection, graph, agents, ops, review_replay, runtime_events, policy  
**Canonical Contracts**: `FrontierScoreBreakdown`, `DomContextBundle`,
`ExtractorFallbackPlan`, `ExtractorAttemptRecord`, `FieldConfidenceScore`,
`CanonicalizationDecision`, `ContentFingerprintRecord`,
`IdentityResolutionDecision`, `DuplicateSuppressionRecord`,
`RankingScoreBreakdown`, `RankedOutputSet`, `OptimizationMetricSlice`,
`CrawlerOptimizationReport`, plus runtime wiring decision contracts  
**Replay/Artifact Impact**: Runtime decisions must carry policy refs,
command/event/outbox refs, artifact/hash/source-anchor refs, lower decision refs,
and replay bundle refs  
**Security/Policy Impact**: Policy/robots/source-scope/private-network/browser
approval gates remain hard filters before optimization signals enqueue, extract,
publish, rank, or aggregate

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/087-crawler-optimization-runtime-wiring/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── runtime-wiring.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code

```text
src/veracrawl/contracts/crawler_optimization.py
src/veracrawl/contracts/registry.py
src/veracrawl/optimization/
├── __init__.py
└── runtime.py
src/veracrawl/review_replay/crawler_optimization_runtime.py
tests/contract/
tests/unit/
```

**Structure Decision**: Add a new `veracrawl.optimization` package for
framework-neutral runtime services. Existing benchmark code remains an
acceptance gate; runtime service modules must not import benchmark modules.

## Complexity Tracking

No constitution violations are introduced by this plan.
