# Implementation Plan: VeraCrawl Durable Runtime Persistence and Scheduler Foundation

**Branch**: `003-durable-runtime-scheduler` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-durable-runtime-scheduler/spec.md`

## Summary

Implement durable runtime and scheduler foundations on top of the completed target core runtime spine. The feature adds replaceable ports and deterministic fixture adapters for unit-of-work, durable command idempotency, append-only event cursors, outbox records, artifact ref validation, scheduler frontier items, queue leases, retry/dead-letter behavior, and replay recovery reports.

The first implementation remains deterministic and local. It proves contracts and owner-service behavior without importing concrete databases, queues, object stores, browser libraries, model SDKs, or agent frameworks into core packages.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and standard-library protocols/data structures.  
**Storage**: Deterministic durable fixture store behind VeraCrawl ports. Production Postgres, Redis, Kafka, object storage, and migration engines remain out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and developer CLI/test harness.  
**Project Type**: Python library plus deterministic CLI fixture runner.  
**Performance Goals**: Full local durable-scheduler gate completes within 30 seconds; deterministic replay recovery reports zero missing refs for the success fixture.  
**Constraints**: Core must not import concrete storage, queue, browser, model SDK, agent framework, or site-specific modules. All durable mutations flow through commands, owner services, idempotency records, event append, outbox append, and replay refs.  
**Scale/Scope**: One durable success fixture plus negative fixtures for duplicate command, event gap, pending outbox, stale lease, invalid lease token, and missing artifact. Production distributed workers, real adapters, browser crawling, graph/memory/export intelligence, and production scale are not implemented in this slice.  
**VeraCrawl Owner Services**: `control`, `scheduler`, `runtime_events`, `artifact_lifecycle`, `review_replay`, `ports`, `policy`, `ops`, and `contracts` are directly affected. Existing `fetch`, `normalize`, `extract`, `evidence`, `verify`, `publish`, and `agents` runtime behavior must remain compatible.  
**Canonical Contracts**: UnitOfWorkRecord, DurableCommandRecord, OutboxRecord, EventCursorRecord, FrontierItem, QueueLease, SchedulerRecoveryReport, DurableReplayRecoveryReport, DurableFixtureManifest, CommandEnvelope, CommandResult, CrawlRunEvent, RuntimeArtifactRef, ReplayBundleManifest.  
**Replay/Artifact Impact**: Durable replay requires command records, command result refs, event cursor refs, outbox refs, artifact refs, frontier item refs, lease refs, recovery report refs, deterministic clock refs, and redaction/lifecycle refs.  
**Security/Policy Impact**: Source authorization, credential isolation, prompt context isolation, artifact privacy lifecycle, retention, legal hold, and publication gates remain blocking. Recovery reports must expose blocked, missing, stale, or invalid refs instead of bypassing them.

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

### Documentation (this feature)

```text
specs/003-durable-runtime-scheduler/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── durable-persistence.md
│   ├── scheduler-frontier.md
│   ├── recovery-replay.md
│   └── fixture-oracle.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── veracrawl/
    ├── contracts/
    │   ├── durable.py            # unit-of-work, command record, outbox, event cursor
    │   ├── scheduler.py          # frontier item, queue lease, scheduler recovery
    │   ├── recovery.py           # durable replay recovery report
    │   └── registry.py           # durable/scheduler registrations
    ├── ports/
    │   ├── durable.py            # durable UoW/event/outbox/repository protocols
    │   └── scheduler.py          # frontier and lease repository protocols
    ├── runtime_support/
    │   └── durable_store.py      # deterministic durable fixture profile behind ports
    ├── runtime_events/
    │   └── durable.py            # durable event cursor validation
    ├── scheduler/
    │   └── runtime.py            # frontier, lease, retry, dead-letter owner service
    ├── review_replay/
    │   └── durable.py            # durable replay recovery validation
    └── cli/
        └── durable.py            # deterministic durable fixture runner

tests/
├── contract/
│   ├── test_durable_contract_registry.py
│   ├── test_durable_ports_and_boundaries.py
│   └── test_scheduler_contracts.py
├── unit/
│   ├── test_durable_command_idempotency.py
│   ├── test_durable_event_outbox.py
│   ├── test_scheduler_leases.py
│   └── test_durable_replay_recovery.py
├── integration/
│   ├── test_durable_runtime_persistence.py
│   └── test_durable_negative_fixtures.py
└── fixtures/
    ├── durable-runtime-success/
    ├── durable-duplicate-command/
    ├── durable-event-gap/
    ├── durable-pending-outbox/
    ├── durable-stale-lease/
    ├── durable-invalid-lease/
    └── durable-missing-artifact/
```

**Structure Decision**: Extend the existing single Python package. Durable and scheduler contracts live in `contracts`; protocol boundaries live in `ports`; deterministic fixture state lives in `runtime_support`; owner behavior stays in `scheduler`, `runtime_events`, and `review_replay`. No production infrastructure adapter is added in this feature.

## Phase 0: Research

Phase 0 decisions are captured in [research.md](research.md). The core choices are:

- Use a deterministic durable fixture store, not production infrastructure, for the first durable profile.
- Model idempotency as a durable command record keyed by command type, target aggregate, and idempotency key.
- Model outbox as append-only records linked to command results and events.
- Model scheduler leases as owner-controlled typed contracts with token validation and expiry.
- Model recovery as typed reports that block completion/publication when refs are missing or stale.

## Phase 1: Design And Contracts

Phase 1 design artifacts are:

- [data-model.md](data-model.md): durable entities, scheduler entities, validation rules, and transitions.
- [contracts/durable-persistence.md](contracts/durable-persistence.md): unit-of-work, command idempotency, event cursor, outbox, artifact ref behavior.
- [contracts/scheduler-frontier.md](contracts/scheduler-frontier.md): frontier item, queue lease, retry, dead-letter behavior.
- [contracts/recovery-replay.md](contracts/recovery-replay.md): durable replay recovery and completion blocking.
- [contracts/fixture-oracle.md](contracts/fixture-oracle.md): success and negative fixture/oracle requirements.
- [quickstart.md](quickstart.md): expected validation flow.

## Post-Design Constitution Check

- [x] Durable profile is general-purpose and not tied to a site, storage product, queue product, or agent framework.
- [x] Core depends only on contracts, ports, commands, events, policy, and replay.
- [x] Scheduler and durable state are explicit owner services with typed transitions.
- [x] Replay recovery and negative fixture coverage are defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
