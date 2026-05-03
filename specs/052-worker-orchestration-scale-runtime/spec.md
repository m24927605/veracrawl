# Feature Specification: Worker Orchestration And Scale Runtime

**Feature Branch**: `052-worker-orchestration-scale-runtime`
**Created**: 2026-05-03
**Status**: Active implementation spec
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Run production worker pools, queues, leases, retries, dead-letter handling,
sharding, backpressure, autoscaling, and recovery for long-running crawls
without state corruption, silent item loss, duplicate pollution, or untracked
replay gaps.

This spec turns the existing scale and queue foundations into a production
worker orchestration aggregate that later ops and benchmark specs can inspect.

## User Stories

### US1 - Long-Running Crawls Survive Worker Failure (P1)

As the runtime control plane, I need frontier, fetch, browser, processing,
verification/review, export, projection, and recovery worker pools to lease work
through fenced queue items, heartbeat leases, retry records, dead-letter records,
and recovery refs so worker crashes do not lose or duplicate work.

Acceptance:

- Passing reports include production persistence, queue broker, live HTTP, live
  normalization, live evidence, worker pool, queue topology, queue item, shard
  lease, heartbeat, fencing token, retry, dead-letter, failure, recovery, policy,
  command/event/outbox, and replay refs.
- Worker crash and stale lease scenarios pass only when retry, dead-letter, and
  recovery refs are visible.

### US2 - Load And Backpressure Are Controlled (P1)

As the scheduler, I need backpressure and autoscaling decisions for fetch,
browser, processing, export, projection, and recovery pools so long-running
crawls can reduce load or add capacity without bypassing policy.

Acceptance:

- Passing reports include backpressure signals, autoscaling decisions, worker
  pool capacity refs, fairness scope refs, and policy refs.
- Backpressure/autoscale without policy fails with typed diagnostics.

### US3 - Operators Can Audit Queue And Replay Health (P2)

As an operator, I need dead-letter visibility, duplicate prevention, event gaps,
pending outbox, stale lease recovery, and replay completeness summarized in one
report.

Acceptance:

- Hidden dead-letter, duplicate pollution, missing heartbeat, missing queue
  broker, missing persistence, and replay mismatch fail deterministically.
- Failed items remain operator-visible and replay-critical refs are complete.

## Functional Requirements

- **FR-001**: The runtime MUST emit a
  `WorkerOrchestrationRuntimeReport` with production persistence, queue broker,
  live HTTP, live normalization, and live evidence refs before pass.
- **FR-002**: The runtime MUST cover frontier, fetch, browser, processing,
  verification/review, export, projection, and recovery worker pools.
- **FR-003**: Passing reports MUST include queue topology, queue item, shard
  lease, heartbeat, fencing token, retry, dead-letter, failure, recovery,
  backpressure, autoscaling, fairness, command/event/outbox, and replay refs.
- **FR-004**: The runtime MUST prove worker crash recovery, stale lease recovery,
  retry/dead-letter visibility, duplicate suppression, and pending outbox/event
  gap replay coverage.
- **FR-005**: Missing persistence, missing queue broker, missing heartbeat,
  unrecovered stale lease, hidden dead-letter, duplicate pollution,
  backpressure/autoscale without policy, and replay mismatch MUST fail with
  typed `WorkerOrchestrationFailureType` diagnostics.
- **FR-006**: The runtime MUST expose a deterministic CLI fixture runner
  `veracrawl-worker-orchestration`.
- **FR-007**: The runtime MUST not weaken source, evidence, graph, memory,
  publication, export, policy, privacy, or replay requirements for scale.
- **FR-008**: Core code MUST stay dependency-neutral and avoid concrete queue,
  database, storage, browser, model SDK, agent framework, UI, or site-specific
  scraper imports.

## Dependencies

- **Requires**: 040 Production Persistence Runtime Wiring, 041 Live HTTP
  Acquisition Runtime, 045 Live Normalization And Site Understanding, 047 Live
  Evidence And Verification Runtime.
- **Uses existing target foundation**: scale hardening, queue broker
  conformance, scheduler leases, durable command/event/outbox, recovery reports.
- **Blocks**: 053 Ops Console, Replay, And Observability Runtime and 054
  Production Benchmark And Release Gate.

## Completion Gate

Long-running crawls tolerate worker failure, retries, load, and partial outages
without state corruption, silent item loss, duplicate pollution, or untracked
replay gaps. Failed or dead-lettered work remains operator-visible.

## Non-Goals

- Does not reduce source/evidence requirements for scale.
- Does not hide failed items from operators.
- Does not introduce concrete queue, database, object store, browser, model SDK,
  agent framework, UI, or site-specific scraper dependencies in core.
