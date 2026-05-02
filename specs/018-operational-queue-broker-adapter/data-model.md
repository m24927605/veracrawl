# Data Model: VeraCrawl Operational Queue Broker Adapter

## QueueBrokerAdapterSpec

Declares broker kind, queue names, capability refs, visibility timeout, fencing support, idempotency support, fairness refs, backpressure refs, and policy refs.

## QueueBrokerOperationRecord

Records live broker operations: enqueue, lease, heartbeat, ack, nack, dead-letter, and duplicate enqueue. Operation refs include queue item, lease, fencing token, retry, failure, recovery, dead-letter, fairness, backpressure, and policy refs.

## QueueBrokerConformanceReport

Operational pass requires adapter, topology, queue item, broker operation, lease, heartbeat, ack/nack, dead-letter, fairness, backpressure, policy, and replay refs. No-runtime reports are `needs_review`.

## QueueBrokerFixtureManifest

Fixture scenarios:

- `redis-broker-conformance-success`
- `redis-broker-idempotency-success`
- `redis-broker-dead-letter-success`
- `redis-broker-runtime-unavailable`
- `broker-missing-fencing-token`
- `broker-missing-heartbeat`
- `broker-missing-dead-letter`
