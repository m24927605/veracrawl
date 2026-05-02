# Feature Specification: VeraCrawl Scale Hardening

**Feature Branch**: `014-scale-hardening`
**Created**: 2026-05-02
**Status**: Implemented and verified
**Input**: User description: "建立 VeraCrawl Scale Hardening Spine：deterministic sharding、queue topology refs、worker leases/heartbeats、backpressure signals、autoscaling decisions、dead-letter/recovery queue visibility、DR restore/replay validation、scale fixture/oracle 測試基礎。必須遵守 docs/07、09、10、11 與 constitution；不得實作成特定雲端或特定 queue/storage；core 不得直接耦合任何 storage、queue、metrics、tracing、cloud SDK、HTTP client、browser 或 agent framework。"

## Constitution Alignment

- **General-purpose crawler impact**: Scale contracts apply across projects, sites, source adapters, priority bands, queue families, and worker pools. They do not assume a specific website, cloud, queue, or storage vendor.
- **Target/V1 boundary**: This is target architecture scale/reliability work from `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Scale decisions require queue topology refs, queue items, shard leases, dead-letter records, backpressure signals, autoscaling decisions, DR/recovery refs, policy refs, command refs, event cursor refs, outbox refs, and replay bundle refs.
- **Safety and policy impact**: Backpressure and autoscaling decisions are policy-visible. Dead-letter and stale-lease recovery must produce failure/recovery refs and cannot be hidden.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define executable contracts for `QueueTopologySpec`, `QueueItem`, `ShardLease`, `RetryDeadLetterRecord`, `BackpressureSignal`, `AutoscalingDecision`, `ScaleRecoveryReport`, and `ScaleFixtureManifest`.
- **FR-002**: System MUST define queue/scale ports without importing concrete queue, storage, metrics, tracing, cloud, HTTP, browser, or agent framework clients.
- **FR-003**: System MUST register scale contracts, commands, events, fixtures, and target contract area coverage.
- **FR-004**: System MUST provide deterministic scale runtime for sharding, leases, heartbeats, backpressure, autoscaling, dead-letter, recovery, and replay refs.
- **FR-005**: System MUST include success fixtures for sharding/lease, backpressure/autoscale, and dead-letter recovery.
- **FR-006**: System MUST include negative fixtures for stale lease without recovery, unfair site starvation, autoscale without policy, dead-letter without failure record, and replay missing scale refs.
- **FR-007**: System MUST reject pass claims when queue topology, queue item, lease, backpressure, autoscaling, failure/recovery, policy, command/event/outbox, or replay refs are missing.
- **FR-008**: System MUST expose a CLI fixture runner for scale fixtures.
- **FR-009**: System MUST update docs and README with the executable scale spine and non-completion boundary.

## Non-Goals

- This feature does not implement concrete queue brokers, storage engines, metrics/tracing backends, cloud autoscaling APIs, production worker fleets, or production distributed persistence.
- This feature does not implement production browser rendering, concrete agent framework integration, production export delivery, or production monitoring dashboards.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
