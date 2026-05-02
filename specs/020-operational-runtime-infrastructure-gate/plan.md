# Implementation Plan: VeraCrawl Operational Runtime Infrastructure Gate

**Branch**: `020-operational-runtime-infrastructure-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-operational-runtime-infrastructure-gate/spec.md`

## Summary

Implement a target architecture infrastructure gate that proves operational Postgres, Redis/Valkey, and S3-compatible object store adapters can contribute one replayable runtime infrastructure report. The gate remains framework-neutral and loads concrete adapters only in CLI/integration code.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing project dependencies plus optional `postgres`, `queue-redis`, and `object-s3` extras for live adapters
**Storage**: live Postgres JSONB adapter, live Redis/Valkey broker, live S3-compatible/MinIO artifact store when live gates run
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, Docker-backed live integration
**Target Platform**: local/CI Python runtime with optional Docker for live gates
**Project Type**: Python package and CLI
**Performance Goals**: deterministic fixture completion; no load benchmark in this feature
**Constraints**: core imports no concrete adapter modules or infrastructure SDKs; integrated pass requires all three live adapter families; no single adapter conformance can stand in for integrated pass
**Scale/Scope**: one infrastructure gate slice with success, idempotency, no-runtime, and negative fixtures
**VeraCrawl Owner Services**: `ports`, `runtime_events`, `scheduler`, `artifact_lifecycle`, `review_replay`, `ops`, `tests`
**Canonical Contracts**: `RuntimeInfrastructureSpec`, `RuntimeInfrastructureReport`, `RuntimeInfrastructureFixtureManifest`, plus existing persistence, queue broker, object store conformance reports
**Replay/Artifact Impact**: passing reports require replay bundle refs and content digest/lifecycle refs from object storage
**Security/Policy Impact**: policy refs are required; source credentials, browser, prompt context, export, and publication are not expanded

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
specs/020-operational-runtime-infrastructure-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md

src/veracrawl/
├── cli/infrastructure.py
├── contracts/infrastructure.py
└── runtime_support/infrastructure_gate.py

tests/
├── contract/
├── fixtures/
├── helpers/
├── integration/
└── unit/
```

**Structure Decision**: Add cohesive infrastructure gate contracts/runtime/CLI without modifying concrete adapters except through dynamic loading in the CLI and live tests.

## Complexity Tracking

No constitution violations.
