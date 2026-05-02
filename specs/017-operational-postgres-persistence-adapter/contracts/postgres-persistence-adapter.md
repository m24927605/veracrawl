# Operational Postgres Persistence Adapter Contracts

Required adapter:

- `veracrawl.adapters.persistence.postgres.PostgresPersistenceAdapter`

Required adapter kind:

- `postgres`

Required fixtures:

- `postgres-adapter-conformance-success`
- `postgres-reopen-idempotency-success`
- `postgres-queue-recovery-success`
- `postgres-runtime-unavailable`

Required CLI behavior:

- `veracrawl-persistence-adapter run ... --postgres-dsn <dsn>` executes operational Postgres fixtures.
- `VERACRAWL_POSTGRES_DSN=<dsn>` may supply the DSN.
- Without DSN, operational pass fixtures fail fast; the explicit no-runtime fixture returns `needs_review`.
