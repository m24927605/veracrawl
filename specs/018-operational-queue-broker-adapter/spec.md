# Feature Specification: VeraCrawl Operational Queue Broker Adapter

**Feature Branch**: `018-operational-queue-broker-adapter`
**Created**: 2026-05-03
**Status**: Implemented
**Input**: User description: "建立 VeraCrawl Operational Queue Broker Adapter：在 adapters 層實作 broker-neutral queue abstraction 與 Redis/Valkey operational adapter、queue broker conformance harness、enqueue/lease/heartbeat/ack/nack/dead-letter/fencing token/visibility timeout/retry/idempotency/fairness/backpressure refs、live Docker integration gate 與 no-broker runtime needs_review guard。Core 不得直接耦合 redis/queue broker SDK，不得把 persistence queue operation refs 假裝成 live broker pass，必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment

- **General-purpose crawler impact**: Queue broker conformance applies to any crawl project, site, source adapter, worker pool, queue family, and retry class. It does not encode a single-site scraper or vertical workflow.
- **Target/V1 boundary**: This is target scale/reliability work after operational Postgres persistence. It turns queue broker execution into a live adapter capability rather than only persistent queue operation records.
- **Evidence and replay impact**: Operational pass requires queue topology, queue item, broker operation, lease/fencing token, heartbeat, ack/nack, dead-letter, retry, backpressure/fairness, policy, and replay refs.
- **Safety and policy impact**: Missing Redis/Valkey URL/runtime must not be reported as operational pass. Persistence queue operation refs must not be treated as live broker execution.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define queue broker adapter specs, operation records, conformance reports, and fixture manifests.
- **FR-002**: System MUST implement a broker-neutral core conformance harness that depends on contracts/ports only.
- **FR-003**: System MUST implement `veracrawl.adapters.queue_brokers.redis.RedisQueueBrokerAdapter` behind the broker-neutral boundary.
- **FR-004**: Core packages MUST NOT statically import `redis`, broker clients, `veracrawl.adapters`, concrete storage clients, or cloud SDKs.
- **FR-005**: Redis/Valkey conformance MUST prove enqueue, lease, heartbeat, ack, nack, dead-letter, fencing token, visibility timeout, retry, idempotency, fairness, backpressure, policy, and replay refs.
- **FR-006**: Duplicate enqueue after adapter reopen MUST create zero duplicate broker queue items.
- **FR-007**: CLI fixture execution MUST require an explicit broker URL for operational pass fixtures and MUST report `needs_review` for no-runtime fixtures instead of faking pass.
- **FR-008**: System MUST expose live integration tests that can run against a provided Redis URL or Docker-provisioned Redis.
- **FR-009**: System MUST register queue broker fixtures, target area coverage, docs, quickstart, and non-deceptive completion notes.

## Non-Goals

- This feature does not implement a production worker fleet, cloud queue service, managed Redis operations, metrics/tracing backend, autoscaling controller, or deployment automation.
- This feature does not remove canonical persistence queue operation records; live broker execution complements them.
- This feature does not make persistence queue refs an operational broker pass.
- VeraCrawl core must not import concrete DB/queue/cloud SDKs, browser libraries, model SDKs, or agent frameworks.

## Success Criteria

- **SC-001**: Redis operational fixtures pass against a live Redis URL or Docker-provisioned Redis.
- **SC-002**: No-broker runtime fixture returns `needs_review`, not pass.
- **SC-003**: Contract registry validation returns `ok: true`.
- **SC-004**: Core import-boundary tests prove `redis` and `veracrawl.adapters` stay outside core.
- **SC-005**: `ruff`, `mypy`, full pytest, and explicit Redis live integration gate pass in this workspace.
