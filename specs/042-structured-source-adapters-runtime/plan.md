# Implementation Plan: Structured Source Adapters Runtime

**Branch**: `042-structured-source-adapters-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/042-structured-source-adapters-runtime/spec.md`

## Summary

Add a structured source adapter runtime gate for sitemap, RSS/feed, API-like
JSON, document, and file-import source families. The core runtime aggregates
typed adapter records and remains parser/client/filesystem independent; concrete
fixture parsing lives in adapter-owned code loaded by the CLI.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; Python standard library parsers; pytest/ruff/mypy
**Storage**: Fixture artifacts and reports; no new database coupling
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic fixture parsing with bounded local files
**Constraints**: Core cannot import concrete source adapters, parser-specific runtime, storage clients, browser libraries, model SDKs, or agent frameworks
**Scale/Scope**: Five structured source families per fixture
**VeraCrawl Owner Services**: fetch, ports, runtime_events, review_replay, tests
**Canonical Contracts**: StructuredSourceAdapterRecord, StructuredSourceAdaptersRuntimeReport, StructuredSourceAdaptersFixtureManifest, SourceAdapterResult, FetchAttempt, FetchResult, PageSnapshot, DocumentArtifact
**Replay/Artifact Impact**: source result, raw artifact, natural output, content hash, evidence seed, event cursor, outbox, and replay refs required for pass
**Security/Policy Impact**: policy-denied, malformed, unsupported, and replay-mismatch failures are typed

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through ports and contracts.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Security and policy gates are defined for unsafe structured source cases.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/042-structured-source-adapters-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/structured-source-adapters-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/source_runtime.py
src/veracrawl/fetch/structured_source.py
src/veracrawl/adapters/sources/structured_runtime.py
src/veracrawl/cli/structured_source.py
tests/fixtures/structured-source-adapters-*/
```

## Complexity Tracking

No constitution violations are introduced.
