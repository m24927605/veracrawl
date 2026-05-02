# Concrete Persistence Adapter Contracts

Required contracts:

- `PersistenceMigrationRecord`
- `PersistenceAdapterConformanceReport`
- `PersistenceAdapterFixtureManifest`

Required commands:

- `record_persistence_migration`
- `record_persistence_adapter_conformance_report`

Required events:

- `persistence_migration_recorded`
- `persistence_adapter_conformance_reported`

Required fixtures:

- `sqlite-adapter-conformance-success`
- `sqlite-reopen-idempotency-success`
- `sqlite-queue-recovery-success`
- `postgres-adapter-contract-harness`
- `adapter-missing-capability`
- `sqlite-idempotency-gap`
- `sqlite-event-cursor-gap`
- `sqlite-outbox-gap`
- `sqlite-migration-missing`
