# Implementation Plan: Worker Orchestration And Scale Runtime

**Branch**: `052-worker-orchestration-scale-runtime` | **Date**: 2026-05-03 | **Spec**: `specs/052-worker-orchestration-scale-runtime/spec.md`
**Input**: Feature specification from `/specs/052-worker-orchestration-scale-runtime/spec.md`

## Summary

Implement roadmap row 052 by adding a deterministic worker orchestration runtime
aggregate on top of the existing scale, queue broker, scheduler, durable, and
recovery contracts. The aggregate proves long-running crawls can lease, fence,
heartbeat, retry, dead-letter, recover, apply backpressure, autoscale, and
replay work across target worker pools without silent item loss or duplicate
pollution.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl contracts/runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, dependency-neutral core, no weakened evidence/replay requirements for scale  
**Scale/Scope**: target worker orchestration for frontier, fetch, browser, processing, verification/review, export, projection, and recovery pools  
**VeraCrawl Owner Services**: scheduler, fetch, browser, normalize, extract, evidence, verify, export, projection, recovery, ops, runtime_events, tests  
**Canonical Contracts**: WorkerOrchestrationRuntimeReport, WorkerOrchestrationFixtureManifest, QueueTopologySpec, QueueItem, ShardLease, RetryDeadLetterRecord, BackpressureSignal, AutoscalingDecision, ScaleRecoveryReport, QueueBrokerConformanceReport  
**Replay/Artifact Impact**: queue item lifecycle refs, lease/heartbeat/fencing refs, retry/dead-letter refs, recovery refs, event cursor/outbox refs, replay bundle refs  
**Security/Policy Impact**: fairness, load, autoscaling, retry/dead-letter visibility, source/evidence preservation, operator-visible failures

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
specs/052-worker-orchestration-scale-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/worker-orchestration-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{enums.py,scale.py,registry.py,__init__.py}
src/veracrawl/scale/worker_orchestration.py
src/veracrawl/review_replay/worker_orchestration.py
src/veracrawl/cli/worker_orchestration.py
tests/contract/test_worker_orchestration_*.py
tests/unit/test_worker_orchestration_*.py
tests/integration/test_worker_orchestration_fixtures.py
tests/helpers/worker_orchestration_fixture_assertions.py
tests/fixtures/worker-orchestration-*/...
```

**Structure Decision**: extend the scale owner package because worker
orchestration is the production composition of scale hardening, queue topology,
leases, retries, dead-letter, backpressure, autoscaling, and replay. The new
report is an aggregate; lower-level queue and recovery contracts stay owned by
their existing modules.

## Complexity Tracking

No constitution violations.
