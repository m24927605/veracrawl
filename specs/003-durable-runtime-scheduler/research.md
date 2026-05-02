# Research: Durable Runtime Persistence and Scheduler Foundation

## Decision: Deterministic durable fixture store behind ports

**Rationale**: The feature must prove durable semantics without coupling core to a concrete database, queue, object store, or migration engine. A deterministic fixture store can persist state across repository instances in the same test run while exercising the same ports production adapters will implement later.

**Alternatives considered**:

- Production database adapter now: rejected because this slice defines contracts and owner semantics before production migrations.
- Reusing in-memory runtime repositories only: rejected because it cannot prove reload, outbox, idempotency, or recovery semantics.

## Decision: Durable command records own idempotency

**Rationale**: Idempotency must be stable across retries and restarts. Command records keyed by command type, target aggregate, and idempotency key prevent duplicate event/outbox append while preserving the original `CommandResult`.

**Alternatives considered**:

- Event deduplication only: rejected because duplicate commands can occur before event append.
- Caller-managed deduplication: rejected because owner services must enforce durability and replay safety.

## Decision: Outbox records are append-only and dispatch-state tracked

**Rationale**: Durable command/event side effects must be visible after crashes. Pending outbox records are recoverable; dispatched and failed records remain replay-visible.

**Alternatives considered**:

- Direct side effects during command handling: rejected because crashes can create invisible partial state.
- Outbox records outside replay: rejected because recovery and audit need side-effect lineage.

## Decision: Scheduler leases are durable typed contracts

**Rationale**: Queue coordination requires token validation, expiry, heartbeat, completion, release, retry, and dead-letter transitions. These cannot be hidden in an adapter-native queue state if VeraCrawl replay is authoritative.

**Alternatives considered**:

- Queue-client-native lease state as canonical: rejected because it couples core semantics to infrastructure.
- Stateless scheduling: rejected because crash-resume and duplicate worker claims cannot be proven.

## Decision: Recovery reports block completion when refs are missing

**Rationale**: Durable recovery must be explicit and non-deceptive. Missing event cursor, command, outbox, artifact, lease, or replay refs must produce typed non-success reports and block completion/publication.

**Alternatives considered**:

- Best-effort recovery warnings: rejected because warnings can allow false completion.
- Silent retry loops: rejected because operators need visible recovery diagnostics.
