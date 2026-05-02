# Data Model: VeraCrawl Concrete Persistence Adapter Family

## PersistenceMigrationRecord

Adapter migration run with adapter ref, migration name/version, schema versions, rollback plan, validation event cursor, status, and failure refs.

## PersistenceAdapterConformanceReport

Adapter conformance result tying adapter spec, transaction, migration, idempotency, event cursor, outbox, artifact index, queue operation, policy, replay, and contract-only refs.

## PersistenceAdapterFixtureManifest

Fixture manifest declaring adapter family scenario, expected result, expected operator status, expected failure type, and negative-case flag.
