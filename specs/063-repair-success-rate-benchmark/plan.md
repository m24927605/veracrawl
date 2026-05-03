# Implementation Plan: Repair Success Rate Benchmark

**Branch**: `063-repair-success-rate-benchmark` | **Date**: 2026-05-04 | **Spec**: `specs/063-repair-success-rate-benchmark/spec.md`
**Input**: Feature specification from `specs/063-repair-success-rate-benchmark/spec.md`

## Summary

Implement a deterministic repair success benchmark that measures whether
AI-assisted repair can recover from seeded crawl planning, fetch/browser,
normalization, extraction, verification, publication, drift, and replay failures
without weakening policy or bypassing owner-service commands. The implementation
adds repair contracts, registry entries, runtime, replay checks, CLI, fixtures,
negative tests, and documentation while preserving framework-neutral agent/model
boundaries.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Pydantic contracts, VeraCrawl command/event runtime, reference persistence store  
**Storage**: Reference persistence store for benchmark state; canonical contracts remain replayable  
**Testing**: ruff, mypy, registry validation, focused pytest, full pytest, Docker-backed pytest  
**Target Platform**: Python package and CLI  
**Project Type**: library/CLI  
**Performance Goals**: deterministic benchmark generation with at least 30 seeded cases  
**Constraints**: core must not import model SDKs, agent frameworks, browser engines, crawler frameworks, or single-site scraper code  
**Scale/Scope**: one materialized production-quality benchmark row, nine fixtures, typed negative diagnostics  
**VeraCrawl Owner Services**: verify, agents, tests, review_replay, policy, runtime_events  
**Canonical Contracts**: `RepairQualityManifest`, `RepairQualityThresholds`, `SeededRepairCase`, `RepairAttemptTrace`, `RepairQualityReport`  
**Replay/Artifact Impact**: seeded cases and attempts carry command/event/outbox, policy, evidence, rollback/escalation, and replay refs  
**Security/Policy Impact**: repairs cannot bypass robots/source scope, credential scope, evidence gates, verification gates, publication gates, owner-service commands, or replay

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/063-repair-success-rate-benchmark/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── repair-success-rate-benchmark.md
└── tasks.md
```

### Source Code

```text
src/veracrawl/contracts/repair_success.py
src/veracrawl/benchmarks/repair_success.py
src/veracrawl/review_replay/repair_success.py
src/veracrawl/cli/repair_success.py
tests/contract/test_repair_success_*.py
tests/unit/test_repair_success_*.py
tests/integration/test_repair_success_fixtures.py
tests/fixtures/repair-success-*/
```

## Complexity Tracking

No constitution violations.
