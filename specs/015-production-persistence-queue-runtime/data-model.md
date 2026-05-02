# Data Model: VeraCrawl Production Persistence And Queue Runtime

## PersistenceAdapterSpec

Declares adapter identity, backend family, supported capabilities, port refs, transaction/idempotency/lease support, and policy refs.

## PersistenceTransactionRecord

Replayable unit-of-work transaction record tying command, event, outbox, artifact, idempotency, queue operation, policy, commit, rollback, and failure refs.

## IdempotencyPersistenceRecord

Durable idempotency record tying a command identity and idempotency key to original command result, event, outbox, duplicate, or rejection refs.

## PersistentQueueOperationRecord

Replay-critical queue operation record for enqueue, lease, heartbeat, ack, nack, and dead-letter transitions with queue item, lease, token, result, failure, and recovery refs.

## PersistenceRuntimeReport

Fixture/runtime report proving transaction, durable command, idempotency, event cursor, outbox, artifact, queue operation, lease, policy, failure/recovery, and replay refs.

## PersistenceFixtureManifest

Fixture manifest declaring scenario, target profile support, expected completion result, expected operator status, and negative-case status.
