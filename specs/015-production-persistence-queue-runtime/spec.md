# Feature Specification: VeraCrawl Production Persistence And Queue Runtime

**Feature Branch**: `015-production-persistence-queue-runtime`
**Created**: 2026-05-03
**Status**: Implemented and verified
**Input**: User description: "建立 VeraCrawl Production Persistence And Queue Runtime：production-grade metadata/event/outbox/artifact persistence adapters、queue adapter spine、unit-of-work transaction boundary、idempotency persistence、lease heartbeat/ack/nack/dead-letter recovery、adapter contract tests、fixture/oracle 測試基礎。Core 必須維持 storage/queue/cloud SDK neutral，只能透過 ports/adapters 對接具體基礎設施，必須遵守 docs/07、09、10、11 與 constitution；不得實作成特定雲端或特定 queue/storage。"

## Constitution Alignment

- **General-purpose crawler impact**: Persistence and queue runtime contracts apply across projects, runs, source adapters, queue families, artifacts, commands, events, outbox topics, and worker pools. They do not assume one website, queue broker, database, object store, cloud, schema, or output domain.
- **Target/V1 boundary**: This is target architecture dependency work after `014-scale-hardening`. It materializes production-facing persistence/queue semantics while preserving adapter neutrality from `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Mutating work requires transaction records, durable command records, idempotency records, event cursor refs, outbox refs, artifact index refs, queue operation refs, lease refs, policy refs, and replay bundle refs.
- **Safety and policy impact**: Persistence must not hide queue, outbox, artifact, or replay failures. Queue recovery and dead-letter behavior must produce failure/recovery visibility and must not bypass scope, budget, rate, credential, browser, or publication policy.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios And Testing

### User Story 1 - Atomic Durable Mutation (Priority: P1)

As a VeraCrawl runtime owner, I need command records, events, outbox records, artifact index entries, and queue operations to commit or fail as one replayable unit so interrupted crawls do not corrupt canonical state.

**Independent Test**: Run `persistence-transaction-success`; the report must include transaction, command, event cursor, outbox, artifact, idempotency, queue, policy, and replay refs.

### User Story 2 - Persisted Idempotency And Replay (Priority: P1)

As a worker retrying after a crash, I need repeated commands with the same idempotency key to return the original result without duplicating events, outbox records, or queue side effects after the adapter is reopened.

**Independent Test**: Run `idempotent-replay-success`; a reopened store must dedupe the duplicate command and preserve one event and one outbox record.

### User Story 3 - Queue Lease Recovery (Priority: P1)

As a scheduler worker, I need queue enqueue, lease, heartbeat, ack, nack, and dead-letter transitions to be persisted with lease fencing and recovery refs.

**Independent Test**: Run `queue-lease-recovery-success`; persisted queue operation records must include lease, heartbeat, ack/nack/dead-letter, failure, and recovery refs.

### Edge Cases

- Non-atomic commit claims fail when transaction refs or committed refs are missing.
- Duplicate commands fail when idempotency records are not persisted.
- Event log replay fails when event cursors are missing or non-contiguous.
- Pending outbox records fail when dispatch/recovery visibility is missing.
- Artifact publication or replay fails when artifact index refs are missing.
- Lease recovery fails when heartbeat, ack/nack, dead-letter, failure, or recovery refs are missing.

## Requirements

- **FR-001**: System MUST define executable contracts for persistence adapter specs, transaction records, idempotency persistence records, persistent queue operation records, persistence runtime reports, and persistence fixture manifests.
- **FR-002**: System MUST expose persistence and queue ports without importing concrete storage, queue, cloud, metrics, tracing, HTTP, browser, model SDK, or agent framework clients.
- **FR-003**: System MUST provide a standard-library reference persistence store that proves adapter semantics through filesystem-backed fixture state and reopen/replay tests; this reference store MUST NOT be documented as the only production storage.
- **FR-004**: System MUST persist command idempotency so duplicate commands after reopen do not create duplicate events, outbox records, or queue operations.
- **FR-005**: System MUST persist event log ordering and produce replay cursor records for complete runs; cursor gaps must fail deterministic acceptance.
- **FR-006**: System MUST persist outbox records and expose pending/dispatch/failure visibility.
- **FR-007**: System MUST persist artifact index refs required by replay and publication lineage.
- **FR-008**: System MUST persist queue enqueue, lease, heartbeat, ack, nack, and dead-letter operations with lease and recovery refs.
- **FR-009**: System MUST expose a `veracrawl-persistence` CLI fixture runner.
- **FR-010**: System MUST register contracts, commands, events, fixtures, target contract area coverage, README, and target docs updates.
- **FR-011**: System MUST include success fixtures for transaction persistence, idempotent replay, and queue lease recovery.
- **FR-012**: System MUST include negative fixtures for non-atomic commit, missing idempotency persistence, event log gaps, pending outbox without recovery, missing artifact index, and missing lease heartbeat/recovery.

## Non-Goals

- This feature does not bind VeraCrawl core to Postgres, Redis, Kafka, SQS, cloud storage, SQLAlchemy, metrics backends, tracing backends, HTTP clients, browsers, model SDKs, or agent frameworks.
- This feature does not complete production deployment, production worker fleets, production observability, production backup operations, concrete cloud adapters, or external queue/broker operations.
- This feature does not implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

- **SC-001**: All success fixtures pass through `veracrawl-persistence run` and produce complete transaction, idempotency, event cursor, outbox, artifact, queue, policy, and replay refs.
- **SC-002**: Duplicate command replay after reopening the reference persistence store emits zero duplicate events and zero duplicate outbox records.
- **SC-003**: All negative fixtures fail deterministically with expected operator statuses and missing refs.
- **SC-004**: Contract registry validation returns `ok: true`.
- **SC-005**: `ruff`, `mypy`, and full `pytest tests` pass.
