# Feature Specification: VeraCrawl Operational Postgres Persistence Adapter

**Feature Branch**: `017-operational-postgres-persistence-adapter`
**Created**: 2026-05-03
**Status**: Implemented
**Input**: User description: "建立 VeraCrawl Operational Postgres Persistence Adapter：在 adapters 層實作可執行 Postgres persistence adapter、SQL migration plan、DB-API/psycopg optional runtime boundary、transaction/idempotency/event log/outbox/artifact index/queue conformance、live integration gate 與 no-Postgres environment skip/report。Core 不得直接耦合 psycopg/Postgres/client SDK，不得把 Postgres contract descriptor 假裝成 operational pass，必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment

- **General-purpose crawler impact**: Postgres persistence applies to any crawl project, site, adapter family, queue, artifact, event, and replay record. It does not encode a single-site scraper or vertical workflow.
- **Target/V1 boundary**: This is target persistence adapter work after `016-concrete-persistence-adapters`; it upgrades Postgres from contract descriptor to operational adapter while preserving core neutrality.
- **Evidence and replay impact**: Operational pass requires transaction, migration, idempotency, event cursor, outbox, artifact index, queue operation, lease, policy, and replay refs.
- **Safety and policy impact**: Missing live Postgres DSN/runtime must not be reported as operational pass. Contract-only paths remain `needs_review`.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define an operational `postgres` persistence adapter kind distinct from `postgres_contract`.
- **FR-002**: System MUST implement `veracrawl.adapters.persistence.postgres.PostgresPersistenceAdapter` behind the same port-shaped API used by the conformance harness.
- **FR-003**: Core packages MUST NOT statically import `psycopg`, Postgres clients, `veracrawl.adapters`, concrete queue clients, or cloud SDKs.
- **FR-004**: Postgres adapter MUST persist canonical documents in Postgres with SQL migrations and JSONB storage for metadata, events, outbox, artifact index, queue, idempotency, transaction, and migration records.
- **FR-005**: Postgres adapter conformance MUST prove transaction, migration, command idempotency, event log cursor, outbox, artifact index, queue lease heartbeat, ack/nack, dead-letter, and replay refs.
- **FR-006**: Duplicate commands after Postgres adapter reopen MUST create zero duplicate events and zero duplicate outbox records.
- **FR-007**: CLI fixture execution MUST require an explicit Postgres DSN for operational Postgres pass fixtures and MUST report `needs_review` for no-runtime fixtures instead of faking pass.
- **FR-008**: System MUST expose live integration tests that can run against a provided DSN or Docker-provisioned Postgres.
- **FR-009**: System MUST register Postgres adapter fixtures, target area coverage, docs, quickstart, and non-deceptive completion notes.

## Non-Goals

- This feature does not implement external queue brokers, object storage, cloud deployment, metrics/tracing backends, production worker fleets, or managed Postgres operations.
- This feature does not remove the SQLite adapter or make Postgres the only target storage.
- This feature does not make the existing `postgres_contract` descriptor an operational pass.
- VeraCrawl core must not import concrete DB/queue/cloud SDKs, browser libraries, model SDKs, or agent frameworks.

## Success Criteria

- **SC-001**: Postgres operational fixtures pass against a live Postgres DSN or Docker-provisioned Postgres.
- **SC-002**: No-Postgres runtime fixture returns `needs_review`, not pass.
- **SC-003**: Contract registry validation returns `ok: true`.
- **SC-004**: Core import-boundary tests prove `psycopg` and `veracrawl.adapters` stay outside core.
- **SC-005**: `ruff`, `mypy`, full pytest, and explicit Postgres live integration gate pass in this workspace.
