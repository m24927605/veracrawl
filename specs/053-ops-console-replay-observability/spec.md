# Feature Specification: Ops Console, Replay, And Observability Runtime

**Feature Branch**: `053-ops-console-replay-observability`
**Created**: 2026-05-03
**Status**: Active implementation spec
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Expose the operator runtime that composes publication/export, worker
orchestration, review/replay ops data, and operational observability into one
replayable report. Operators must be able to inspect, pause/resume, replay,
recover, explain bad outputs, inspect graph/debug context, review incidents,
observe alerts/cost, and verify recovery through canonical refs without direct
database mutation or dashboard-only state.

This spec does not replace the existing `veracrawl-ops` data-surface runner or
`veracrawl-observability` operational observability gate. It creates the row 053
target aggregate that proves those lower-level gates are connected to rows 048
and 052.

## User Stories

### US1 - Operator Runtime Integrates Results And Workers (P1)

As an operator, I need one runtime report tying result publication/export and
worker orchestration to review, replay, dashboard, and observability refs so I
can inspect a production run without joining hidden state manually.

Acceptance:

- Passing reports include `ResultPublicationExportRuntimeReport`,
  `WorkerOrchestrationRuntimeReport`, `OpsConsoleReport`, and
  `ObservabilityReport` refs.
- Passing reports include run-control action refs, review/evidence review refs,
  replay audit refs, graph/debug refs, export/withdrawal status refs,
  failure/recovery/DR refs, dashboard refs, policy refs, command/event/outbox
  refs, redaction refs, and replay bundle refs.

### US2 - Incidents Are Recoverable And Explainable (P1)

As an on-call operator, I need alerts, runbooks, recovery actions, failure
records, DR restore refs, dashboard watermarks, and replay refs connected so
incident recovery is auditable and not an untracked manual fix.

Acceptance:

- Incident and cost/alert success fixtures pass only when alert, runbook,
  metric, trace, quality, cost, dashboard, failure/recovery, DR, redaction, and
  replay refs are present.
- Unresolved recovery, unsafe operator action, stale dashboard, and replay
  mismatch fail with typed diagnostics.

### US3 - Missing Dependencies Cannot Be Labeled Operational (P2)

As a reviewer, I need missing publication/export, worker orchestration, ops
console, or observability refs to fail deterministically so VeraCrawl cannot
claim an operational target runtime from partial data surfaces.

Acceptance:

- Missing row 048, row 052, ops console, or observability refs fail with typed
  `OpsReplayObservabilityFailureType` diagnostics.
- Core imports remain dependency-neutral and do not bind to UI, telemetry,
  browser, model, agent framework, storage, queue, or site-specific scraper
  implementations.

## Functional Requirements

- **FR-001**: The runtime MUST emit an
  `OpsReplayObservabilityRuntimeReport` that references row 048 result
  publication/export and row 052 worker orchestration reports before pass.
- **FR-002**: Passing reports MUST include ops console and operational
  observability report refs.
- **FR-003**: Passing reports MUST include run-control action, review item,
  evidence review, replay audit, graph/debug, export status, withdrawal status,
  recovery, failure, DR restore, dashboard, alert, runbook, cost, metric, trace,
  policy, command, event cursor, outbox, redaction, and replay refs.
- **FR-004**: Missing publication, missing worker orchestration, missing ops
  console, missing observability, stale dashboard, unresolved recovery, unsafe
  operator action, and replay mismatch MUST fail with typed diagnostics.
- **FR-005**: The runtime MUST expose a deterministic CLI fixture runner
  `veracrawl-ops-runtime`.
- **FR-006**: The runtime MUST not persist dashboard-only state as canonical
  state and MUST not weaken source, evidence, publication, scale, security,
  privacy, or replay requirements.
- **FR-007**: Core code MUST avoid concrete UI framework, telemetry backend,
  storage client, queue client, browser, model SDK, agent framework, or
  site-specific scraper imports.

## Dependencies

- **Requires**: 048 Result Publication And Export Runtime and 052 Worker
  Orchestration And Scale Runtime.
- **Uses existing target foundation**: ops console contracts/runtime,
  operational observability contracts/runtime, DR restore contracts,
  command/event/outbox/replay contracts, quality dashboard contracts.
- **Blocks**: 054 Production Benchmark And Release Gate.

## Completion Gate

Operators can inspect, pause/resume, replay, recover, and explain bad outputs or
failed runs through canonical refs, and operational observability is connected
to those refs without direct database mutation or hidden tooling.

## Non-Goals

- Does not implement a production dashboard frontend.
- Does not claim managed telemetry storage, alert delivery, paging integrations,
  or on-call automation.
- Does not replace canonical replay with dashboard-only state.
- Does not require a specific UI, telemetry, queue, storage, browser, model, or
  agent framework in core.
