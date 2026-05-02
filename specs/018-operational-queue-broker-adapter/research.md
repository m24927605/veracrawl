# Research: VeraCrawl Operational Queue Broker Adapter

## Decision: Optional Redis Runtime

The Redis/Valkey adapter uses an optional `queue-redis` extra with `redis`. Core code never imports redis; adapter code dynamic-imports it inside `veracrawl.adapters.queue_brokers.redis`.

## Decision: Redis Hashes And Lists

Queue items are stored as JSON documents in hashes and runnable queue order is represented by Redis lists. Leases are stored as JSON documents with fencing tokens and expiry refs. Dead letters are stored separately for replay and recovery.

## Decision: Explicit Live Gate

Operational pass requires a live Redis URL. Tests can use `VERACRAWL_REDIS_URL` or `VERACRAWL_REDIS_DOCKER=1` to provision Docker Redis. Without a live runtime, the no-runtime fixture returns `needs_review`; pass is forbidden.

## Rejected: Treat Persistence Queue Records As Broker Pass

`PersistentQueueOperationRecord` remains canonical persistence lineage. It does not prove a live broker accepted, leased, heartbeat-renewed, acked, nacked, or dead-lettered a queue item.
