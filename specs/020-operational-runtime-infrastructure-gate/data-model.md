# Data Model: Operational Runtime Infrastructure Gate

## RuntimeInfrastructureSpec

Declares the required adapter refs and policy refs for an integrated operational infrastructure gate.

Required fields:

- `id`
- `persistence_adapter_ref`
- `queue_broker_adapter_ref`
- `object_store_adapter_ref`
- `required_live_adapter_refs`
- `policy_decision_refs`

## RuntimeInfrastructureReport

Aggregates live conformance refs from persistence, queue broker, and object store reports.

Pass requires:

- runtime infrastructure spec ref
- persistence, queue broker, and object store report refs
- adapter refs for all three live adapter families
- command, idempotency, event cursor, outbox, transaction refs
- queue topology, queue item, broker operation, lease, heartbeat, ack, nack, dead-letter refs
- artifact, object operation, digest, read, head, list, delete, lifecycle refs
- policy refs and replay bundle ref

Non-pass requires failure refs, missing ref fields, or contract-only refs.

## RuntimeInfrastructureFixtureManifest

Declares fixture scenario, expected completion result, expected operator status, and optional negative failure type.

Scenarios:

- `operational-infrastructure-success`
- `operational-infrastructure-idempotency-success`
- `operational-infrastructure-runtime-unavailable`
- `infrastructure-missing-persistence-refs`
- `infrastructure-missing-queue-refs`
- `infrastructure-missing-object-refs`
- `infrastructure-missing-replay-refs`
