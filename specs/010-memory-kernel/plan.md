# Implementation Plan: VeraCrawl Memory Kernel

**Branch**: `010-memory-kernel` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/010-memory-kernel/spec.md`

## Summary

Implement replayable memory kernel contracts and deterministic fixture runtime for scoped memory writes, retrieval traces, invalidation exclusion, cross-scope sanitized tunnels, operational temporal memory records, and memory evidence-boundary failures.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard library.  
**Storage**: Stable refs and deterministic fixture reports only. Production memory/vector/search stores remain out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Constraints**: Memory cannot satisfy evidence; no concrete memory/vector/search/browser/network/storage/model/agent/export coupling.  
**Owner Services**: `memory`, `review_replay`, `policy`, `contracts`, and `tests` are directly affected.

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected memory use.
- [x] Security, prompt-injection, privacy lifecycle, and cross-scope policy gates are defined.
- [x] Fixture/oracle and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/010-memory-kernel/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── memory-kernel.md
│   ├── cross-scope-boundary.md
│   └── fixture-oracle.md
└── tasks.md

src/veracrawl/
├── contracts/memory.py
├── memory/kernel.py
├── review_replay/memory.py
└── cli/memory.py
```

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
