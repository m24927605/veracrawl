# Feature Specification: Worker Orchestration And Scale Runtime

**Feature Branch**: `052-worker-orchestration-scale-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Run production worker pools, queues, leases, retries, dead-letter handling,
sharding, backpressure, autoscaling, and recovery for long-running crawls.

## Scope

- Frontier, fetch, browser, processing, verification/review, export, projection,
  and recovery worker orchestration.
- Queue lease lifecycle, heartbeat, fencing, retry, and dead-letter records.
- Backpressure and autoscaling decisions.
- Recovery from worker crash, event gap, pending outbox, and stale lease.

## Dependencies

- Blocks: 053, 054.
- Requires: 040, 041, 045, 047.

## Completion Gate

Long-running crawls tolerate worker failure, retries, load, and partial outages
without state corruption, silent item loss, duplicate pollution, or untracked
replay gaps.

## Non-Goals

- Does not reduce source/evidence requirements for scale.
- Does not hide failed items from operators.
