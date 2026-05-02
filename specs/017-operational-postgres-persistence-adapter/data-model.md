# Data Model: VeraCrawl Operational Postgres Persistence Adapter

## PersistenceAdapterSpec

Adds `postgres` as an operational adapter kind. `postgres_contract` remains a descriptor-only kind.

## Postgres JSONB Document Store

Adapter-owned table:

```sql
CREATE TABLE IF NOT EXISTS veracrawl_documents (
  collection TEXT NOT NULL,
  key TEXT NOT NULL,
  document JSONB NOT NULL,
  PRIMARY KEY (collection, key)
)
```

## PersistenceAdapterConformanceReport

Operational Postgres pass uses the existing conformance report and must include adapter, transaction, migration, idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay refs.

## PersistenceAdapterFixtureManifest

New fixture scenarios:

- `postgres-adapter-conformance-success`
- `postgres-reopen-idempotency-success`
- `postgres-queue-recovery-success`
- `postgres-runtime-unavailable`
