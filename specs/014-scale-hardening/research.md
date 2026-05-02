# Research: VeraCrawl Scale Hardening

## Decision: Model Scale As Replayable Control Records

- **Rationale**: Sharding, leases, backpressure, autoscaling, and recovery must be auditable decisions, not hidden worker behavior.
- **Rejected alternative**: Add a queue broker now. Rejected because it would couple core to infrastructure before contracts are stable.

## Decision: Make Fairness Explicit

- **Rationale**: Target docs require one bad or high-volume site not to starve unrelated jobs.
- **Rejected alternative**: Global FIFO only. Rejected because it violates per-project/per-site fairness.

## Decision: Treat Autoscaling As Throughput Only

- **Rationale**: Autoscaling must not change correctness; owner services, expected versions, and idempotency preserve correctness.
- **Rejected alternative**: Let autoscaling mutate domain state. Rejected because it bypasses owner-service contracts.
