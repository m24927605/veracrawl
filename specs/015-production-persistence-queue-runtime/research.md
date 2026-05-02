# Research: VeraCrawl Production Persistence And Queue Runtime

## Decision: Contracts First, Vendor Adapters Later

Persistence semantics are modeled as contracts and ports before concrete infrastructure. This keeps VeraCrawl compatible with Postgres, SQLite, object stores, Kafka, SQS, Redis, or future systems without importing any of them into core.

## Decision: Reference Filesystem Store For Executable Proof

A standard-library filesystem reference store provides reopen, atomic write, idempotency, event ordering, outbox, artifact index, and queue transition tests. It proves the adapter contract without claiming that filesystem storage is the only production backend.

## Decision: Idempotency Is Durable State

Idempotency records must be persisted with command result, event, and outbox refs. Duplicate commands after reopen return the original refs and cannot emit duplicate side effects.

## Decision: Queue Transitions Are Replay-Critical

Queue enqueue, lease, heartbeat, ack, nack, and dead-letter operations are persisted as explicit records with lease/fencing refs. Recovery and replay can fail on missing heartbeat, dead-letter, failure, or recovery refs.

## Decision: Non-Completion Boundary

This spec materializes production-facing semantics and adapter contracts. It does not complete concrete cloud/database/queue adapters, production deployments, production observability, or backup operations.
