# Feature Specification: Production Benchmark And Release Gate

**Feature Branch**: `054-production-benchmark-release-gate`
**Created**: 2026-05-03
**Status**: Active implementation spec
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Define and run the final authorized benchmark suite that proves VeraCrawl's
target production runtime readiness across source coverage, target crawl
runtime, product acceptance, safety/privacy, publication/export, worker scale,
ops/replay/observability, and release audit gates.

This is the final row 054 aggregate. It must not implement a single-site
scraper, bypass existing target gates, or relabel incomplete lower-level
reports as production-ready. A release pass is allowed only when the existing
039-053 runtime gates contribute canonical refs and the release report has no
blockers, false-ready claims, missing gate refs, or replay gaps.

## User Stories

### US1 - Release Reviewer Gets One Auditable Decision (P1)

As a release reviewer, I need one release report that references the target
runtime, source coverage, product acceptance, security/privacy, publication,
worker orchestration, and ops runtime reports so production readiness can be
approved or blocked from canonical refs.

Acceptance:

- Passing reports include refs to `TargetRuntimeReport`,
  `SourceCoverageAdapterReport`, `ProductAcceptanceGateReport`,
  `SecurityPrivacyReport`, `ResultPublicationExportRuntimeReport`,
  `WorkerOrchestrationRuntimeReport`, and
  `OpsReplayObservabilityRuntimeReport`.
- Passing reports include authorized benchmark corpus refs, scenario refs,
  source, processing, evidence, verification, publication, export, replay, ops,
  scale, safety, policy, command/event/outbox, artifact, redaction, SLO metric,
  release decision, and audit refs.

### US2 - Benchmark Blockers Cannot Be Hidden (P1)

As an operator, I need missing runtime gates, SLO violations, safety blockers,
false release-ready status, and replay mismatch to fail deterministically so
VeraCrawl cannot claim production readiness from partial or degraded behavior.

Acceptance:

- Missing target runtime, source coverage, product acceptance, security/privacy,
  publication, worker orchestration, or ops runtime fails with typed diagnostics.
- SLO violations, release blockers, false-ready status, and replay mismatch fail
  with typed diagnostics and replay-visible refs.

### US3 - Core Remains Framework And Adapter Neutral (P2)

As a maintainer, I need the release gate to aggregate canonical reports without
importing concrete UI frameworks, telemetry backends, storage clients, queue
clients, browser engines, model SDKs, agent frameworks, cloud services, or
site-specific scraper code into core.

Acceptance:

- Import-boundary tests cover the release runtime.
- Fixture execution uses deterministic local contract/runtime data and explicit
  refs; it does not contact unauthorized public targets.

## Functional Requirements

- **FR-001**: The release gate MUST emit a
  `ProductionBenchmarkReleaseReport` with refs to target runtime, source
  coverage, product acceptance, security/privacy, result publication/export,
  worker orchestration, and ops replay/observability reports.
- **FR-002**: Passing reports MUST include authorized benchmark manifest/corpus
  refs and scenario refs.
- **FR-003**: Passing reports MUST include source, processing, evidence,
  verification, publication, export, replay, ops, scale, safety, policy,
  command, event cursor, outbox, artifact, redaction, SLO metric, release
  decision, and audit refs.
- **FR-004**: Missing lower-level gate refs, SLO violations, release blockers,
  false-ready status, and replay mismatch MUST fail with typed
  `ProductionBenchmarkReleaseFailureType` diagnostics.
- **FR-005**: The release gate MUST expose a deterministic CLI fixture runner
  `veracrawl-release-gate`.
- **FR-006**: The gate MUST not weaken lower-level acceptance criteria or use
  dashboard-only, contract-only, framework-native, or adapter-native state as
  canonical release evidence.
- **FR-007**: Core code MUST avoid concrete UI framework, telemetry backend,
  storage client, queue client, browser, model SDK, agent framework, cloud SDK,
  or site-specific scraper imports.

## Dependencies

- Requires completed specs 039-053.
- Uses target runtime, source coverage, product acceptance, security/privacy,
  result publication/export, worker orchestration, and ops runtime reports.

## Completion Gate

The deterministic release benchmark fixtures pass, negative fixtures fail with
typed diagnostics, the release report is replayable, full non-Docker and
Docker-backed test gates pass, and no false complete/verified/operational or
release-ready claim is possible from missing refs.

## Non-Goals

- Does not use unauthorized public websites or policy-bypassing tactics.
- Does not implement managed cloud deployment, paging, autoscaling control,
  production UI, or external benchmark services.
- Does not replace lower-level 039-053 acceptance; it composes and audits them.
