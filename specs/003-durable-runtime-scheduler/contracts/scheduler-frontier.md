# Contract: Scheduler Frontier

## Frontier Item

Frontier items are owned by `scheduler` and represent durable crawl work. They must not encode site-specific scraper assumptions.

Required behavior:

- enqueue with source ref, run ref, priority, max attempts, and policy refs
- lease highest-priority eligible item
- heartbeat active lease
- complete with valid token
- release with valid token
- expire stale lease
- retry if attempts remain
- dead-letter when retry budget is exhausted

## Queue Lease

Queue leases are durable canonical records, not adapter-native queue state.

Rules:

- active lease requires token and expiry refs
- mutations on leased items require the current token
- invalid token produces a rejected command result and scheduler recovery report
- expired leases make the frontier item eligible for retry
- completed leases cannot be reused

## Events

Scheduler transitions emit replay-critical events:

- `frontier_item_enqueued`
- `frontier_item_leased`
- `queue_lease_heartbeat_recorded`
- `frontier_item_completed`
- `queue_lease_released`
- `queue_lease_expired`
- `frontier_item_dead_lettered`
- `scheduler_recovery_reported`
