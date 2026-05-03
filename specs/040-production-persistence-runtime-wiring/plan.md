# Implementation Plan: Production Persistence Runtime Wiring

**Branch**: `040-production-persistence-runtime-wiring` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/040-production-persistence-runtime-wiring/spec.md`

## Summary

Wire the spec 039 production run-control API through production-shaped
persistence, artifact index, event log, outbox, idempotency, and queue ports.
The implementation adds a core runtime wiring module that accepts port-shaped
stores, a deterministic reference CLI fixture runner, contracts and target-area
registry coverage, and tests proving restart/replay, duplicate idempotency, and
queue recovery without importing concrete infrastructure clients into core.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; pytest/ruff/mypy for validation
**Storage**: Port-shaped persistence stores; deterministic reference filesystem in CLI fixtures; existing SQLite/Postgres adapter surfaces remain adapter-owned
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full non-Docker and Docker-backed gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic fixture execution and stable replay counts; no production throughput SLO in this spec
**Constraints**: Core must not import psycopg, redis, boto3/botocore, browser libraries, model SDKs, or agent frameworks
**Scale/Scope**: One run-control execution per fixture, with adapter reopen and queue recovery semantics
**VeraCrawl Owner Services**: control, persistence, scheduler, fetch, runtime_events, artifact_lifecycle, review_replay, tests
**Canonical Contracts**: ProductionRunControlReport, ProductionPersistenceRuntimeReport, ProductionPersistenceFixtureManifest, PersistenceTransactionRecord, IdempotencyPersistenceRecord, PersistentQueueOperationRecord, CrawlRunEvent, EventCursorRecord, OutboxRecord, ReplayBundleManifest
**Replay/Artifact Impact**: Run-control events, event cursor, outbox, artifact index, queue, policy, and replay refs are required for pass
**Security/Policy Impact**: Policy refs are mandatory; missing policy/replay cannot pass

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; persistence wiring is website/source/domain agnostic.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; no model SDK or agent framework is introduced.
- [x] Low coupling/high cohesion boundaries are explicit through ports, contracts, commands, events, typed reports, and CLI adapter selection.
- [x] Evidence, verification, publication, replay, and artifact lineage remain downstream gates; this spec preserves replay/artifact refs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export gates are not weakened; missing policy/replay refs fail.
- [x] Command/event schema refs, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/040-production-persistence-runtime-wiring/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/production-persistence-runtime-wiring.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/objective.py
src/veracrawl/contracts/registry.py
src/veracrawl/ports/persistence.py
src/veracrawl/runtime_support/persistence_store.py
src/veracrawl/adapters/persistence/json_document.py
src/veracrawl/adapters/persistence/sqlite.py
src/veracrawl/control/run_control.py
src/veracrawl/control/production_persistence.py
src/veracrawl/cli/production_persistence.py
tests/fixtures/production-persistence-*/
```

## Implementation Notes

- Add the production persistence report contracts to `contracts/objective.py`
  because the runtime wires control-owned run state into durable persistence.
- Extend existing persistence ports with canonical document save/load methods
  instead of letting core modules touch adapter internals.
- Keep the deterministic reference fixture runner separate from live Postgres,
  Redis, and S3 adapter conformance. The adapter-owned gates from specs 017-020
  remain the proof for concrete clients.
- Reuse the spec 039 run-control execution path through a detailed result API so
  040 persists actual canonical records, not synthetic refs only.

## Complexity Tracking

No constitution violations are introduced.
