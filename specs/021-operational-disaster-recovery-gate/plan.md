# Implementation Plan: VeraCrawl Operational Disaster Recovery Gate

**Branch**: `021-operational-disaster-recovery-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/021-operational-disaster-recovery-gate/spec.md`

## Summary

Implement a target architecture operational disaster recovery gate that proves a DR restore plan can execute ordered phases and produce a replay-complete report using the live operational infrastructure substrate. The gate remains adapter-owned and framework-neutral: core DR validation depends on VeraCrawl contracts and conformance result types, while CLI/integration code dynamically loads operational Postgres, Redis/Valkey, and S3-compatible adapters.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing project dependencies plus optional `postgres`, `queue-redis`, and `object-s3` extras for live adapter-backed gates
**Storage**: live Postgres JSONB adapter, live Redis/Valkey broker, live S3-compatible/MinIO artifact store when operational gates run
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, Docker-backed live integration
**Target Platform**: local/CI Python runtime with optional Docker for live gates
**Project Type**: Python package and CLI
**Performance Goals**: deterministic fixture completion; restore validation under the fixture runner should complete inside normal integration test timeouts
**Constraints**: core imports no concrete adapter modules or infrastructure SDKs; operational pass requires all live infrastructure families and all DR phase validation refs; deterministic fixture-only and single-adapter paths cannot claim pass
**Scale/Scope**: one operational DR gate slice with success, no-runtime, and negative fixtures for missing phase refs, unresolved refs, data loss, and unsafe recovery
**VeraCrawl Owner Services**: `ops`, `review_replay`, `runtime_support`, `artifact_lifecycle`, `scheduler`, `export`, `projection`, `tests`
**Canonical Contracts**: `DRRestorePlan`, `DRRestoreRun`, `DRRestoreReport`, `DRRestoreFixtureManifest`, `FailureRecord`, `RecoveryAction`, `RuntimeInfrastructureReport`
**Replay/Artifact Impact**: passing reports require restore point, backup manifest, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, command, event cursor, outbox, queue recovery, policy, and replay refs
**Security/Policy Impact**: policy refs are mandatory; side-effecting recovery requires approval refs; DSNs, queue URLs, object-store credentials, artifact content, and incident details are redacted by reference

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
specs/021-operational-disaster-recovery-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md

src/veracrawl/
├── cli/dr.py
├── contracts/ops.py
├── contracts/enums.py
├── contracts/registry.py
└── runtime_support/disaster_recovery.py

tests/
├── contract/
├── fixtures/
├── helpers/
├── integration/
└── unit/
```

**Structure Decision**: Extend the existing `ops` contracts with executable DR plan/run/fixture manifest models, add a cohesive `runtime_support` DR gate module, and add a CLI wrapper that dynamically loads operational adapters. Concrete infrastructure packages remain adapter-owned.

## Complexity Tracking

No constitution violations.
