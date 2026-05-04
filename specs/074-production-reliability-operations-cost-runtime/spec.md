# Feature Specification: Production Reliability Operations And Cost Runtime

**Feature Branch**: `074-production-reliability-operations-cost-runtime`  
**Created**: 2026-05-04  
**Status**: Planned  
**Roadmap Row**: 074  
**Input**: Production-grade closure requirement: crawler readiness must include long-running reliability, operations, cost, and SLO gates.

## Summary

Prove VeraCrawl can run production-like crawl workloads over durable workers,
queues, persistence, object storage, retries, recovery, observability, alerts,
cost controls, and operator workflows. This spec turns operational behavior into
release-blocking validation.

## User Scenarios

1. Given a production crawl with many targets and pages, VeraCrawl runs through
   worker pools with durable leases, retries, dead letters, backpressure,
   idempotency, and duplicate suppression.
2. Given worker crashes, queue delays, network failures, API quota limits, or
   object store retries, VeraCrawl recovers or escalates with typed diagnostics
   and replayable recovery records.
3. Given operator review needs, VeraCrawl exposes run status, evidence review,
   blocked sources, cost, latency, retry, queue depth, and replay views.

## Functional Requirements

- **FR-001**: System MUST define `ProductionWorkloadRun`,
  `ReliabilitySLOReport`, `CostUsageReport`, `LatencyThroughputReport`,
  `RecoveryExerciseReport`, and `OperatorReadinessReport` contracts.
- **FR-002**: System MUST run against production persistence, queue, and object
  storage ports with Docker-backed and configurable live infrastructure gates.
- **FR-003**: System MUST record p50/p95/p99 latency, throughput, queue depth,
  retry rate, error rate, token/call usage, browser runtime cost, storage cost,
  and source-limited rates.
- **FR-004**: System MUST enforce workload budgets, per-site rate limits,
  retry/dead-letter policies, backpressure, and autoscaling decisions.
- **FR-005**: System MUST provide operator-visible refs for run review,
  evidence review, replay, recovery, alerts, dashboards, and runbooks.
- **FR-006**: System MUST fail release when SLOs, cost budgets, replay,
  recovery, or operator visibility are missing.

## Required Tests

- Docker-backed Postgres, Redis/Valkey, and S3-compatible object store gates.
- Failure injection for worker crash, stale lease, duplicate enqueue, network
  flake, browser timeout, object store retry, outbox lag, and queue recovery.
- Multi-run stability validation with at least three production-like runs.
- Import-boundary tests for infrastructure clients and adapter ownership.

## Completion Gate

Production-like workloads pass reliability, cost, latency, recovery,
observability, and replay gates without silent loss, duplicate pollution, or
false-ready status.
