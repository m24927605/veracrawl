# Implementation Plan: VeraCrawl Source-Backed Target Runtime

**Branch**: `035-source-backed-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/035-source-backed-runtime/spec.md`

## Summary

Extend the target runtime from deterministic reference generation into source-backed local corpus execution. The implementation adds source corpus contracts, reads local fixture files, derives stable output/evidence/graph/export/replay refs from content hashes, records framework-neutral repair recommendations for drift aliases, and preserves existing 034 deterministic fixture behavior.

## Technical Context

**Language/Version**: Python 3.11+; validation uses Python 3.12
**Primary Dependencies**: Existing Pydantic contracts plus Python standard library `json`, `html.parser`, `hashlib`, `pathlib`, and `re`
**Storage**: Local fixture files and generated run reports only
**Testing**: pytest, ruff, mypy, registry validation, CLI fixture loops, full non-Docker and Docker-backed suites
**Target Platform**: Python library and CLI
**Project Type**: Single Python package
**Performance Goals**: Source-backed fixture loop completes within 60 seconds
**Constraints**: No live Internet, no concrete agent framework, no site-specific scraper modules, no unsafe completion claims
**VeraCrawl Owner Services**: control, fetch, extract, evidence, verify, graph, agents, publish, export, review_replay, policy, ops, tests
**Canonical Contracts**: Existing target runtime contracts plus new source corpus contracts
**Replay/Artifact Impact**: Content hashes become artifact/replay refs; replay mismatch fixture must fail
**Security/Policy Impact**: Policy denied and prompt injection corpus entries block before completion

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; source corpus is multi-pattern and descriptor-driven.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries remain explicit through target runtime contracts and runner helpers.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for source-backed outputs.
- [x] Security, policy, prompt-injection, privacy lifecycle, and export gates are defined.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to schedule or delivery speed.

## Project Structure

```text
specs/035-source-backed-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/source-backed-runtime.md
└── tasks.md

src/veracrawl/
├── contracts/target_runtime.py
├── target_runtime/runner.py
└── cli/target_runtime.py

tests/
├── contract/test_source_backed_target_runtime_contracts.py
├── fixtures/source-backed-target-*/
├── integration/test_source_backed_target_runtime_fixtures.py
└── unit/test_source_backed_target_runtime_runner.py
```

**Structure Decision**: Extend `veracrawl.contracts.target_runtime` and `veracrawl.target_runtime.runner` rather than adding a parallel runtime package. Source-backed execution is a mode of target runtime, and the CLI remains `veracrawl-target-runtime`.

## Phase 0: Research

See [research.md](./research.md).

## Phase 1: Design And Contracts

See [data-model.md](./data-model.md), [contracts/source-backed-runtime.md](./contracts/source-backed-runtime.md), and [quickstart.md](./quickstart.md).

## Complexity Tracking

No constitution violations. No complexity waiver required.
