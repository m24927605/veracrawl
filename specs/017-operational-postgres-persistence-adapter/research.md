# Research: VeraCrawl Operational Postgres Persistence Adapter

## Decision: Optional Psycopg Runtime

The Postgres adapter uses an optional `postgres` extra with `psycopg[binary]`. Core code never imports psycopg; adapter code dynamic-imports it inside `veracrawl.adapters.persistence.postgres`.

## Decision: JSONB Document Table

The operational slice stores canonical VeraCrawl contract documents in a Postgres JSONB table with `(collection, key)` primary key. This keeps the adapter aligned with current conformance semantics while preserving the future ability to split collections into normalized tables.

## Decision: Explicit Live Gate

Operational pass requires a live DSN. Tests can use `VERACRAWL_POSTGRES_DSN` or `VERACRAWL_POSTGRES_DOCKER=1` to provision a Docker Postgres. Without a live runtime, the no-runtime fixture returns `needs_review`; pass is forbidden.

## Rejected: Treat Contract Descriptor As Operational

The existing `postgres_contract` descriptor is not upgraded into a pass. It remains contract-only. Operational pass belongs only to `postgres` adapter kind after live conformance execution.
