# Implementation Plan: Live Normalization And Site Understanding

**Branch**: `045-live-normalization-site-understanding` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/045-live-normalization-site-understanding/spec.md`

## Summary

Add a live normalization runtime aggregate that consumes acquired content plus
041/042/043 refs and materializes normalized document, normalization manifest,
anchor map/source anchor, link provenance, page type, site model, policy,
command/event/outbox, artifact, and replay refs.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; existing normalization pipeline; pytest/ruff/mypy
**Storage**: Fixture output reports; no new database coupling
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic local normalization over bounded fixture HTML
**Constraints**: Core cannot import concrete source/network/browser adapters, storage clients, model SDKs, or agent frameworks
**Scale/Scope**: Three success patterns plus five negative fixtures
**VeraCrawl Owner Services**: normalize, fetch, runtime_events, review_replay, tests
**Canonical Contracts**: LiveNormalizationRuntimeReport, LiveNormalizationFixtureManifest, NormalizedDocument, NormalizationManifest, AnchorMap, TextAnchor, LinkProvenance, PageTypeClassification, SiteModel
**Replay/Artifact Impact**: source/raw artifact, normalized artifact, anchors, site model, event/outbox, upstream report, and replay refs required for pass
**Security/Policy Impact**: derived site understanding cannot be source evidence; policy refs required

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through ports and contracts.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Security and derived-context boundaries are defined.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/045-live-normalization-site-understanding/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/live-normalization-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/processing.py
src/veracrawl/normalize/live_runtime.py
src/veracrawl/cli/live_normalization.py
tests/fixtures/live-normalization-*/
```

## Complexity Tracking

No constitution violations are introduced.
