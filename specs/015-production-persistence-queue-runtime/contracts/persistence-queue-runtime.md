# Persistence And Queue Runtime Contracts

Required contracts:

- `PersistenceAdapterSpec`
- `PersistenceTransactionRecord`
- `IdempotencyPersistenceRecord`
- `PersistentQueueOperationRecord`
- `PersistenceRuntimeReport`
- `PersistenceFixtureManifest`

Required ports:

- `MetadataPersistencePort`
- `EventLogPersistencePort`
- `OutboxPersistencePort`
- `ArtifactIndexPersistencePort`
- `QueuePersistencePort`

Required commands:

- `record_persistence_adapter`
- `record_persistence_transaction`
- `record_idempotency_persistence`
- `record_persistent_queue_operation`
- `record_persistence_runtime_report`

Required events:

- `persistence_adapter_recorded`
- `persistence_transaction_recorded`
- `idempotency_persisted`
- `persistent_queue_operation_recorded`
- `persistence_runtime_reported`

Required fixtures:

- `persistence-transaction-success`
- `idempotent-replay-success`
- `queue-lease-recovery-success`
- `non-atomic-commit`
- `idempotency-not-persisted`
- `event-log-gap`
- `outbox-dispatch-missing`
- `artifact-index-missing`
- `lease-heartbeat-missing`
