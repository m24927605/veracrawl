# Implementation Plan: Precision Recall Quality Benchmark

**Branch**: `062-precision-recall-quality-benchmark` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/062-precision-recall-quality-benchmark/spec.md`

## Summary

Implement row 062 as a metrics-only quality gate over field-level oracle
records. The benchmark generates or consumes field confusion records, computes
corpus and slice precision/recall/F1/error rates, enforces fixed thresholds, and
links metric components to field evaluation, evidence, publication gate,
command/event/outbox, policy, and replay refs. It does not run crawling,
extraction, or repair.

## Technical Context

**Language/Version**: Python 3.12 for validation; package supports Python >= 3.11  
**Primary Dependencies**: Pydantic and existing VeraCrawl persistence/runtime contracts  
**Storage**: Reference persistence store for command/event/outbox/canonical refs  
**Testing**: pytest, ruff, mypy, registry validation, focused/full/Docker-backed pytest, CLI validation  
**Target Platform**: CLI/library runtime  
**Project Type**: Python package with contracts, metric runtime, replay helpers, CLI, fixtures, tests  
**Performance Goals**: quality fixture computes deterministic corpus and slice metrics in local test budget  
**Constraints**: no one-site parsing assumptions; metrics cannot drop hard cases; LLM-only evidence, publication bypass, missing evidence, and missing replay cannot count as true positives  
**Scale/Scope**: corpus-level plus schema/pattern/source/rendering/confidence slices, threshold and negative fixtures  
**VeraCrawl Owner Services**: verify, evidence, publish, ops, policy, runtime_events, review_replay, tests  
**Canonical Contracts**: `QualityMetricThresholds`, `FieldConfusionRecord`, `PrecisionRecallSliceMetric`, `PrecisionRecallQualityReport`, `QualityMetricManifest`  
**Replay/Artifact Impact**: all metric inputs and report decisions require evidence/publication/command/event/outbox/replay refs  
**Security/Policy Impact**: policy bypass, model-only evidence, missing evidence, unsafe publication, and hidden false positives fail

## Constitution Check

- [x] General-purpose crawler capability is preserved; metrics are schema/pattern/source-driven, not site-specific.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; model refs cannot count as evidence.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime, replay helpers, CLI, and registry wiring.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for metric inputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and publication gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, negative tests, replay tests, and import-boundary tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/062-precision-recall-quality-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── precision-recall-quality-benchmark.md
└── tasks.md

src/veracrawl/
├── benchmarks/
│   └── quality_metrics.py
├── cli/
│   └── quality_metrics.py
├── contracts/
│   ├── quality_metrics.py
│   ├── enums.py
│   ├── registry.py
│   └── __init__.py
└── review_replay/
    └── quality_metrics.py

tests/
├── contract/
├── unit/
├── integration/
└── fixtures/
```

**Structure Decision**: Keep metric contracts, runtime math, replay checks, and
CLI separated. Core metric modules import no crawler adapters, model SDKs, agent
frameworks, browser engines, HTTP clients, or site-specific scraper modules.

## Complexity Tracking

No constitution violations.
