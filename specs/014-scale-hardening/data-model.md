# Data Model: VeraCrawl Scale Hardening

## QueueTopologySpec

Queue topology, shard key parts, queue names, fairness scopes, and concurrency limits.

## QueueItem

Replay-visible queue item carrying run, aggregate, command, priority, retry, lease, deadline, status, and idempotency refs.

## ShardLease

Worker lease with queue, shard key, worker id, token, heartbeat, expiry, status, and policy refs.

## RetryDeadLetterRecord

Dead-letter record tying queue item, retry class, final reason, failure record, and recovery actions together.

## BackpressureSignal

Policy-visible queue or resource pressure signal with measured value, threshold, severity, and policy refs.

## AutoscalingDecision

Throughput-only scaling decision for worker pools based on backpressure signal refs and policy refs.

## ScaleRecoveryReport

Replayable report proving scale topology, queue, lease, backpressure, autoscaling, dead-letter, failure/recovery, DR restore, policy, command/event/outbox, and replay refs.

## ScaleFixtureManifest

Fixture manifest declaring scenario, target profile support, expected completion result, expected operator status, and negative-case status.
