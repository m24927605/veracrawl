# Feature Specification: Production Persistence Runtime Wiring

**Feature Branch**: `040-production-persistence-runtime-wiring`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Wire the target runtime through production persistence, artifact, event, outbox,
idempotency, and queue ports without coupling core packages to concrete storage
or queue clients.

## Scope

- Postgres-backed canonical metadata through persistence ports.
- Object artifact storage through artifact/object ports.
- Queue leases and durable frontier through queue ports.
- Event cursor, outbox, idempotency, migration, and replay validation.

## Dependencies

- Blocks: 041, 052, 054.
- Requires: 039.

## Completion Gate

Canonical run state, artifacts, events, outbox records, idempotency decisions,
and queue leases survive process restart and can be replayed without core
importing Postgres, object-store, or queue clients.

## Non-Goals

- Does not add live source acquisition.
- Does not add worker autoscaling.
