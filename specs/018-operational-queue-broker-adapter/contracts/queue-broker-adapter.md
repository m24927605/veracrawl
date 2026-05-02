# Operational Queue Broker Adapter Contracts

Required contracts:

- `QueueBrokerAdapterSpec`
- `QueueBrokerOperationRecord`
- `QueueBrokerConformanceReport`
- `QueueBrokerFixtureManifest`

Required adapter:

- `veracrawl.adapters.queue_brokers.redis.RedisQueueBrokerAdapter`

Required fixtures:

- `redis-broker-conformance-success`
- `redis-broker-idempotency-success`
- `redis-broker-dead-letter-success`
- `redis-broker-runtime-unavailable`
- `broker-missing-fencing-token`
- `broker-missing-heartbeat`
- `broker-missing-dead-letter`

Required CLI behavior:

- `veracrawl-queue-broker run ... --redis-url <url>` executes operational Redis/Valkey fixtures.
- `VERACRAWL_REDIS_URL=<url>` may supply the URL.
- Without URL, operational pass fixtures fail fast; the explicit no-runtime fixture returns `needs_review`.
