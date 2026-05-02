# Feature Specification: VeraCrawl Operational Runtime Infrastructure Gate

**Feature Branch**: `020-operational-runtime-infrastructure-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Operational Runtime Infrastructure Gate：把已完成的 operational Postgres persistence adapter、Redis/Valkey queue broker adapter、S3-compatible/MinIO object store adapter 以 framework-neutral、adapter-owned 的方式串成同一個 live runtime infrastructure acceptance gate；需要 runtime infrastructure contracts/report、CLI、fixtures/oracles、Docker-backed integration test、no-runtime needs_review guard、negative missing-ref fixtures，證明 command/event/outbox/idempotency、queue enqueue/lease/heartbeat/ack/dead-letter、artifact put/get/head/list/delete/digest/lifecycle/replay refs 能在同一個 run 中協作。Core 不得直接耦合 psycopg/redis/boto3/botocore/cloud SDK、browser library、model SDK 或 agent framework；不得把單一 adapter conformance 假裝成 integrated runtime pass；不得宣稱 managed cloud/deployment/observability/worker fleet readiness。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment

- **General-purpose crawler impact**: This feature strengthens VeraCrawl as a general-purpose AI agent crawler by proving the operational infrastructure substrate can coordinate persistence, queueing, and artifact storage for any crawl run without site-specific assumptions.
- **Target/V1 boundary**: This is target architecture dependency work after specs 017, 018, and 019. It does not reduce target architecture and does not claim full crawler product completion.
- **Evidence and replay impact**: The gate aggregates command, event cursor, outbox, idempotency, queue operation, lease, dead-letter, artifact operation, digest, lifecycle, policy, and replay refs into one immutable runtime infrastructure report.
- **Safety and policy impact**: The feature enforces privacy/lifecycle refs for artifacts, policy refs for all adapters, and no-runtime/negative failure reporting. It does not handle source credentials, browser interaction, prompt context, export delivery, or publication.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing

### User Story 1 - Integrated Live Infrastructure Pass (Priority: P1)

An operator can run one fixture against live Postgres, Redis/Valkey, and S3-compatible object storage and receive a single `pass` report proving the three operational adapters cooperated for one runtime infrastructure gate.

**Why this priority**: Individual adapter passes are not enough for target readiness. The runtime must prove that metadata/event/outbox, broker queueing, and object artifacts can be validated together.

**Independent Test**: Run `veracrawl-infrastructure run tests/fixtures/operational-infrastructure-success ...` with live DSNs/URLs/endpoints and verify a pass report with all required refs.

**Acceptance Scenarios**:

1. **Given** live Postgres, Redis/Valkey, and S3-compatible runtimes, **When** the success fixture runs, **Then** the report includes adapter refs, command/event/outbox/idempotency refs, queue operation/lease/heartbeat/ack/dead-letter refs, object operation/digest/read/head/list/delete/lifecycle refs, policy refs, and a replay bundle ref.
2. **Given** only one adapter conformance report exists, **When** an integrated pass is requested, **Then** the report must not pass unless all three adapter families contribute live refs.

### User Story 2 - Runtime Unavailable Guard (Priority: P2)

An operator can run the no-runtime fixture and receive `needs_review` instead of a false operational pass.

**Why this priority**: Missing live infrastructure must be visible and cannot be disguised by contract descriptors or deterministic fixture stores.

**Independent Test**: Run the no-runtime fixture without DSNs/URLs/endpoints and verify `needs_review` with contract-only refs.

**Acceptance Scenarios**:

1. **Given** no live runtime arguments or environment variables, **When** the no-runtime fixture runs, **Then** the completion result is `needs_review`.
2. **Given** deterministic fixture artifact refs, **When** the infrastructure gate is evaluated, **Then** those refs cannot satisfy operational object store pass requirements.

### User Story 3 - Missing Reference Failures (Priority: P3)

Review and replay can deterministically fail an infrastructure report that omits persistence, queue, object, or replay refs.

**Why this priority**: Integrated infrastructure pass must be falsifiable. Negative fixtures prevent vague or partial reports from being accepted.

**Independent Test**: Run negative fixtures and verify typed `fail` statuses with missing ref fields.

**Acceptance Scenarios**:

1. **Given** an infrastructure report missing persistence refs, **When** it is validated, **Then** it fails with `infrastructure_missing_persistence_refs`.
2. **Given** an infrastructure report missing queue refs, **When** it is validated, **Then** it fails with `infrastructure_missing_queue_refs`.
3. **Given** an infrastructure report missing object refs or replay refs, **When** it is validated, **Then** it fails with the corresponding typed status.

### Edge Cases

- A partial live runtime is unavailable: return `needs_review`, not pass.
- A single adapter family passes while the others are contract-only: fail or needs_review, never pass.
- Duplicate command/enqueue/put after adapter reopen must be reported as deduped in the integrated idempotency scenario.
- Dead-letter and delete refs must be present in passing reports.
- Core import-boundary checks must reject direct imports of `psycopg`, `redis`, `boto3`, `botocore`, cloud SDKs, browser libraries, model SDKs, or agent frameworks.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define runtime infrastructure contracts for integrated adapter specs, reports, and fixture manifests.
- **FR-002**: System MUST implement a core infrastructure gate harness that accepts ports/results and does not import concrete adapters or infrastructure SDKs.
- **FR-003**: System MUST aggregate operational Postgres, Redis/Valkey, and S3-compatible conformance refs into one pass/fail/needs_review report.
- **FR-004**: System MUST implement `veracrawl-infrastructure` CLI with dynamic adapter loading and live args/env vars for Postgres, Redis, and S3-compatible endpoints.
- **FR-005**: System MUST provide live success, live idempotency, no-runtime, and negative missing-ref fixtures.
- **FR-006**: System MUST prove no-runtime returns `needs_review` with contract-only refs.
- **FR-007**: System MUST fail deterministic negative fixtures for missing persistence, queue, object, or replay refs.
- **FR-008**: System MUST run a Docker-backed integration gate with Postgres, Redis, and MinIO in one test.
- **FR-009**: System MUST update registry, docs, quickstart, README, and AGENTS active spec references.
- **FR-010**: System MUST avoid claiming managed cloud, deployment, production worker fleet, metrics/tracing backend, production observability, browser rendering, model SDK, or agent framework readiness.

### VeraCrawl Contract Requirements

- **VC-001**: Preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: Define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: Publication outputs are not affected; infrastructure refs do not satisfy source evidence or publication evidence coverage.
- **VC-004**: Define privacy lifecycle and retention refs for object artifacts; credential, prompt-injection, browser, and export boundaries are not expanded.
- **VC-005**: Define fixture/oracle, negative, replay, live Docker, and import-boundary tests before implementation.

### Key Entities

- **RuntimeInfrastructureSpec**: Declares required live adapter refs for Postgres persistence, Redis/Valkey queue broker, and S3-compatible object store.
- **RuntimeInfrastructureReport**: Aggregates persistence, queue, object, policy, failure, contract-only, and replay refs into a pass/fail/needs_review result.
- **RuntimeInfrastructureFixtureManifest**: Declares scenario, expected completion result, expected operator status, and negative failure type.
