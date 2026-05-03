# Implementation Plan: Expanded Real-World Public Corpus Benchmark

**Branch**: `058-expanded-real-world-corpus-benchmark` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/058-expanded-real-world-corpus-benchmark/spec.md`

## Summary

Implement the row 058 quality corpus gate by composing the existing row 055 live
HTTP public corpus runner and adding quality-tier contracts for expanded corpus
thresholds, pattern coverage, policy/drift accounting, fixture oracles, replay
checks, and a dedicated CLI entry point. The implementation remains
manifest-driven and does not add site-specific scraper code.

## Technical Context

**Language/Version**: Python 3.12 for validation; package supports Python >= 3.11
**Primary Dependencies**: Pydantic, stdlib HTTP through existing row 055 CLI adapter
**Storage**: Reference persistence store for fixture and live benchmark runs
**Testing**: pytest, ruff, mypy, registry validation, Docker-backed pytest
**Target Platform**: CLI/library runtime
**Project Type**: Python package with contracts, benchmark runtime, CLI, fixtures, tests
**Performance Goals**: quality fixture execution stays bounded by one target fetch per declared site; live public validation uses conservative per-origin request counts and timeout budgets
**Constraints**: no single-site scraper logic; no direct adapter coupling in core; no private-network targets; no robots/terms bypass; no fake pass on drift
**Scale/Scope**: at least 40 public targets, 15 origins, 10 website/source pattern families in quality profile
**VeraCrawl Owner Services**: ops, tests, fetch, runtime_events, review_replay
**Canonical Contracts**: `RealWorldQualityCorpusManifest`, `RealWorldQualityTargetSpec`, `RealWorldQualitySiteObservation`, `RealWorldQualityPatternCoverageRecord`, `RealWorldQualityCorpusReport`, existing row 055 real-world benchmark contracts
**Replay/Artifact Impact**: quality report links to row 055 run report, site observations, artifacts, content hashes, canonical URLs, command/event/outbox refs, and replay bundles
**Security/Policy Impact**: origin allowlist, robots preflight, private-network denial, rate budget refs, drift diagnostics, retention/redaction by stable refs

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; this spec does not add agent framework coupling.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime, CLI, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for source observations; no publication output is produced.
- [x] Security, policy, prompt-injection, privacy lifecycle, retention, and source gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/058-expanded-real-world-corpus-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── expanded-real-world-corpus-benchmark.md
└── tasks.md

src/veracrawl/
├── benchmarks/
│   └── real_world_quality.py
├── cli/
│   └── real_quality_corpus.py
├── contracts/
│   ├── enums.py
│   ├── real_world_quality.py
│   ├── registry.py
│   └── __init__.py
└── review_replay/
    └── real_world_quality.py

tests/
├── contract/
│   ├── test_real_world_quality_contracts.py
│   ├── test_real_world_quality_contract_registry.py
│   └── test_real_world_quality_import_boundaries.py
├── unit/
│   ├── test_real_world_quality_runtime.py
│   └── test_real_world_quality_replay.py
├── integration/
│   └── test_real_world_quality_fixtures.py
└── fixtures/
    ├── real-world-quality-corpus/
    ├── real-world-quality-insufficient-targets/
    ├── real-world-quality-insufficient-origins/
    ├── real-world-quality-insufficient-patterns/
    ├── real-world-quality-target-drift/
    └── real-world-quality-missing-replay/
```

**Structure Decision**: Add a dedicated quality benchmark layer that composes row
055 instead of changing the existing real-world smoke corpus semantics.

## Complexity Tracking

No constitution violations.
