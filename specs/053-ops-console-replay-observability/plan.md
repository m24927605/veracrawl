# Implementation Plan: Ops Console, Replay, And Observability Runtime

**Branch**: `053-ops-console-replay-observability` | **Date**: 2026-05-03 | **Spec**: `specs/053-ops-console-replay-observability/spec.md`
**Input**: Feature specification from `/specs/053-ops-console-replay-observability/spec.md`

## Summary

Implement roadmap row 053 by adding an ops replay/observability runtime
aggregate that composes the row 048 publication/export runtime, row 052 worker
orchestration runtime, existing ops console data surface, and existing
operational observability gate. The aggregate creates one operator-facing,
replayable report that proves inspection, recovery, alerting, cost, dashboard,
runbook, redaction, command/event/outbox, and replay refs are connected.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl deterministic runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, dependency-neutral core, no dashboard-only canonical state, no weakened evidence/scale/replay requirements  
**Scale/Scope**: target operator runtime spanning result publication/export, worker orchestration, ops console, replay audit, dashboards, observability, alerts, runbooks, cost, recovery, and DR refs  
**VeraCrawl Owner Services**: ops, review_replay, publish, export, scheduler, runtime_events, policy, tests  
**Canonical Contracts**: OpsReplayObservabilityRuntimeReport, OpsReplayObservabilityFixtureManifest, ResultPublicationExportRuntimeReport, WorkerOrchestrationRuntimeReport, OpsConsoleReport, ObservabilityReport, ReviewItem, ReplayAuditView, FailureRecord, RecoveryAction, DRRestoreReport, QualityReport, OpsDashboardSnapshot  
**Replay/Artifact Impact**: replay audit refs, replay bundle refs, event cursor refs, command/outbox refs, redaction map refs, graph/debug refs, dashboard watermarks  
**Security/Policy Impact**: operator recovery actions, runbook approvals, redaction, alerting, replay, publication/export and worker recovery visibility

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
specs/053-ops-console-replay-observability/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/ops-replay-observability-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{enums.py,ops.py,registry.py,__init__.py}
src/veracrawl/ops/replay_observability_runtime.py
src/veracrawl/review_replay/ops_runtime.py
src/veracrawl/cli/ops_runtime.py
tests/contract/test_ops_replay_observability_*.py
tests/unit/test_ops_replay_observability_*.py
tests/integration/test_ops_replay_observability_fixtures.py
tests/helpers/ops_replay_observability_fixture_assertions.py
tests/fixtures/ops-runtime-*/...
```

**Structure Decision**: extend the ops owner package because row 053 is an
operator-runtime aggregate over existing ops and observability contracts. Lower
level publication/export and worker orchestration contracts remain owned by
their existing modules and are referenced by stable report refs.

## Complexity Tracking

No constitution violations.
