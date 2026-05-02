# Contract: Durable Persistence

## Ports

Durable core behavior is exposed through VeraCrawl-owned protocols:

- `UnitOfWorkPort`: begin, record command, append event, append outbox, commit, rollback.
- `DurableCommandRepositoryPort`: save and look up command records by idempotency identity.
- `DurableEventStorePort`: append events with contiguous per-run sequence checks and build cursors.
- `OutboxRepositoryPort`: append pending records, mark dispatched, mark failed, list pending.
- `DurableArtifactIndexPort`: register and validate artifact refs without reading concrete storage clients.

## Idempotency

Duplicate commands are identified by:

```text
command_type + target_aggregate_type + target_aggregate_id + idempotency_key
```

If an identity already has a committed command record, the original command result is returned and no new event or outbox record is appended.

## Event Cursor Rules

- Event sequences are scoped by `run_ref`.
- Appends must be contiguous.
- Cursor records must cover every sequence number from `from_sequence` to `to_sequence`.
- Gaps produce a durable replay recovery failure.

## Outbox Rules

- Every committed durable command with side effects writes an outbox record.
- Pending outbox records survive process restart.
- Dispatch state changes are idempotent.
- Failed dispatch requires operator-visible diagnostics.
