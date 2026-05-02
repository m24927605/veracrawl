# Feature Specification: VeraCrawl Concrete Persistence Adapter Family

**Feature Branch**: `016-concrete-persistence-adapters`
**Created**: 2026-05-03
**Status**: Implemented
**Input**: User description: "建立 VeraCrawl Concrete Persistence Adapter Family：SQLite reference adapter、Postgres adapter contract/conformance harness、event log/outbox/artifact index/metadata store adapter boundary、queue adapter conformance tests、migration/replay fixture/oracle 測試基礎。Core 不得直接耦合任何 concrete storage/queue/cloud SDK，所有具體實作必須在 adapters 層並通過 ports。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment

- **General-purpose crawler impact**: Adapter conformance applies across projects, runs, queues, commands, events, outbox topics, artifacts, and worker lease patterns. It does not assume a single website, scraper, queue broker, cloud, or production database.
- **Target/V1 boundary**: This is target architecture adapter-family work after `015-production-persistence-queue-runtime`. It keeps core neutral and places concrete SQLite implementation under `adapters/`.
- **Evidence and replay impact**: Adapter conformance requires transaction, migration, idempotency, event cursor, outbox, artifact index, queue operation, policy, and replay refs.
- **Safety and policy impact**: Concrete adapters must not hide missing idempotency, event gaps, pending outbox, missing artifacts, missing queue lease refs, or migration gaps.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define executable adapter conformance contracts for migration records, adapter conformance reports, and adapter fixture manifests.
- **FR-002**: System MUST provide a SQLite persistence adapter under `veracrawl.adapters.persistence` that implements the persistence/queue ports with Python standard library `sqlite3`.
- **FR-003**: System MUST provide a Postgres adapter contract descriptor and conformance harness without importing a Postgres client into core.
- **FR-004**: Core packages MUST NOT statically import `veracrawl.adapters` or concrete storage/queue/cloud clients.
- **FR-005**: SQLite adapter conformance MUST prove transaction, migration, command idempotency, event log cursor, outbox, artifact index, queue lease heartbeat, ack/nack, dead-letter, and replay refs.
- **FR-006**: Duplicate commands after SQLite adapter reopen MUST create zero duplicate events and zero duplicate outbox records.
- **FR-007**: Negative fixtures MUST fail for missing adapter capability, missing idempotency persistence, event cursor gaps, missing outbox dispatch visibility, and missing migration refs.
- **FR-008**: System MUST expose `veracrawl-persistence-adapter` CLI fixture runner.
- **FR-009**: System MUST register contracts, commands, events, fixtures, target area coverage, README, and target docs updates.

## Non-Goals

- This feature does not implement a live Postgres connection, external queue broker, object store, cloud storage, metrics/tracing backend, deployment automation, or production worker fleet.
- This feature does not make SQLite the only target production storage.
- VeraCrawl core must not import concrete DB/queue/cloud SDKs, browser libraries, model SDKs, or agent frameworks.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

- **SC-001**: SQLite adapter fixtures pass through `veracrawl-persistence-adapter run`.
- **SC-002**: Postgres contract harness fixture returns `needs_review` with explicit contract-only refs, not a false operational pass.
- **SC-003**: Negative adapter fixtures fail deterministically with expected operator statuses.
- **SC-004**: Contract registry validation returns `ok: true`.
- **SC-005**: `ruff`, `mypy`, and full `pytest tests` pass.
