# Research: Operational Runtime Infrastructure Gate

## Decision: Core gate aggregates existing conformance results

The integrated gate should not duplicate Postgres, Redis, or S3 adapter logic. It should accept already-executed conformance results from the existing core harnesses and validate that all required refs are present in one `RuntimeInfrastructureReport`.

Rationale: This keeps the gate high-cohesion and avoids coupling core to concrete adapters or SDKs.

## Decision: CLI owns dynamic adapter loading

`veracrawl-infrastructure` loads `veracrawl.adapters.persistence.postgres`, `veracrawl.adapters.queue_brokers.redis`, and `veracrawl.adapters.object_stores.s3` dynamically only when a live scenario is requested.

Rationale: This matches specs 017, 018, and 019 and keeps static import-boundary tests meaningful.

## Decision: Integrated pass requires all three live adapter families

No single adapter report can satisfy the integrated infrastructure gate. Passing reports require persistence, queue, object, policy, and replay refs.

Rationale: Target architecture needs the runtime substrate to work together, not just pass isolated adapter conformance.

## Decision: No-runtime stays needs_review

The no-runtime fixture emits `needs_review` with contract-only refs. It does not fail because the operator intentionally requested a non-live runtime check, but it cannot be accepted as operational pass.

Rationale: Prevents false readiness claims while preserving useful contract-only diagnostics.
