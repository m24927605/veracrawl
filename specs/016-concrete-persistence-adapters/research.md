# Research: VeraCrawl Concrete Persistence Adapter Family

## Decision: SQLite Is A Real Local Adapter

SQLite uses Python standard library `sqlite3`, stores canonical contract JSON by collection/key, and proves reopen, idempotency, event cursor, outbox, artifact index, and queue operation semantics.

## Decision: Postgres Is Contract Harness Only In This Slice

Postgres production deployment needs credentials, migrations, pooling, transaction isolation, backup, and operational tests. This slice declares the contract and conformance harness but marks it `needs_review`, avoiding a false production-ready claim.

## Decision: Core Harness Accepts Ports

Core conformance code accepts a persistence adapter object through port-shaped methods. It does not import SQLite or Postgres modules. The CLI dynamically loads concrete adapters from `veracrawl.adapters.persistence`.

## Decision: Migration Records Are Replay-Critical

Adapter conformance requires migration records with rollback and validation refs. Missing migration refs fail adapter acceptance.
