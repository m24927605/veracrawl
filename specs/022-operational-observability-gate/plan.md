# Implementation Plan: VeraCrawl Operational Observability Gate

**Branch**: `022-operational-observability-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/022-operational-observability-gate/spec.md`

## Summary

Implement a target architecture operational observability gate that proves VeraCrawl can explain operational failures through canonical metrics, traces, alerts, runbook actions, dashboard watermarks, cost/quality signals, DR refs, policy, command/event/outbox refs, redaction refs, and replay completeness. The gate remains backend-neutral: core validation owns VeraCrawl observability contracts and pass/fail semantics, while concrete Prometheus, OpenTelemetry, Grafana, cloud monitoring, paging, and on-call systems remain adapter-owned future work.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing project dependencies; no telemetry vendor SDK dependency in core
**Storage**: deterministic fixture reports and existing `.veracrawl-test-runs/` output for this slice; concrete telemetry storage remains adapter-owned future work
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, import-boundary tests, full pytest
**Target Platform**: local/CI Python runtime
**Project Type**: Python package and CLI
**Performance Goals**: deterministic fixture evaluation should complete inside normal integration test timeouts; observability validation is linear in fixture report refs
**Constraints**: core imports no telemetry vendor SDKs, cloud monitoring SDKs, infrastructure SDKs, browser libraries, model SDKs, agent frameworks, or site-specific scraper modules; an operational pass requires canonical signals and backend/collector handoff refs; ops-console-only data cannot claim pass
**Scale/Scope**: one operational observability gate slice with success, no-runtime, data-surface-only, redaction, unsafe-runbook, and missing-ref fixtures
**VeraCrawl Owner Services**: `ops`, `review_replay`, `runtime_support`, `runtime_events`, `contracts`, `tests`
**Canonical Contracts**: `ObservabilitySignal`, `MetricSample`, `TraceSpan`, `AlertRecord`, `RunbookAction`, `ObservabilityReport`, `ObservabilityFixtureManifest`, `FailureRecord`, `RecoveryAction`, `OpsConsoleReport`, `DRRestoreReport`
**Replay/Artifact Impact**: passing reports require metric, trace, alert, runbook, dashboard watermark, cost/quality, failure/recovery, DR, policy, command, event cursor, outbox, redaction, collector handoff, backend, and replay refs
**Security/Policy Impact**: redaction refs are mandatory; secret-like incident details fail validation; side-effecting runbook actions require approval refs; raw secrets, raw prompts, raw artifacts, DSNs, queue URLs, object-store credentials, cloud credentials, and framework-native state must not appear in reports

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
specs/022-operational-observability-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── checklists/
└── tasks.md

src/veracrawl/
├── cli/observability.py
├── contracts/ops.py
├── contracts/enums.py
├── contracts/registry.py
└── runtime_support/observability.py

tests/
├── contract/
├── fixtures/
├── helpers/
├── integration/
└── unit/
```

**Structure Decision**: Extend existing ops contracts with observability models, add a cohesive `runtime_support.observability` gate module, and add a CLI fixture runner. The core gate validates canonical VeraCrawl refs only; concrete telemetry backends remain behind future adapter-owned contracts.

## Complexity Tracking

No constitution violations.
