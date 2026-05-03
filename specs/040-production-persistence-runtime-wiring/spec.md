# Feature Specification: Production Persistence Runtime Wiring

**Feature Branch**: `040-production-persistence-runtime-wiring`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Constitution Alignment

- **General-purpose crawler impact**: Production persistence wiring applies to
  arbitrary projects, site scopes, objectives, run lifecycles, artifacts,
  events, outbox records, idempotency records, and queue leases. It does not
  encode a single website, selector set, cloud provider, queue broker, object
  store, database schema, or output domain.
- **Target/V1 boundary**: This activates roadmap row 040. It wires the row 039
  production run-control API through production-shaped persistence, artifact,
  event, outbox, idempotency, and queue ports. It does not add live source
  acquisition, browser execution, worker autoscaling, or model/agent adapters.
- **Evidence and replay impact**: Canonical run-control state, run-control
  events, persistence command records, event cursors, outbox records,
  idempotency records, artifact index refs, queue operation refs, lease refs,
  policy refs, and replay bundle refs must survive adapter reopen and replay
  validation.
- **Safety and policy impact**: Runtime wiring must not claim pass when
  transaction atomicity, canonical state, idempotency, event cursor, outbox,
  artifact index, lease heartbeat, policy, or replay refs are missing.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## User Stories & Testing

### User Story 1 - Persist Approved Run-Control State (Priority: P1)

As a runtime owner, I need an approved production run from spec 039 to commit
its canonical project/site/objective/plan/run/budget/policy/approval/lifecycle
state through persistence ports so a restart can reload and replay it.

**Independent Test**: Run `veracrawl-production-persistence run tests/fixtures/production-persistence-wiring-success --profile target --out .veracrawl-test-runs/production-persistence-wiring-success`; the report passes only when canonical state refs, transaction refs, run-control event refs, event cursor refs, outbox refs, artifact refs, idempotency refs, queue operation refs, lease refs, policy refs, and replay refs are present after adapter reopen.

### User Story 2 - Preserve Duplicate-Safe Replay (Priority: P1)

As a worker retrying after a crash, I need duplicate production persistence
commands to return the original result after adapter reopen without duplicating
events or outbox records.

**Independent Test**: `production-persistence-idempotent-replay` reopens the
adapter, retries the same idempotency key, and passes only when duplicate
dedupe is recorded with zero duplicate event/outbox side effects.

### User Story 3 - Recover Queue Lease Lineage (Priority: P2)

As a scheduler owner, I need queue enqueue, lease, heartbeat, nack,
dead-letter, failure, and recovery refs to persist with the production run
state so worker failure is visible and replayable.

**Independent Test**: `production-persistence-queue-recovery` passes only when
lease heartbeat, nack, dead-letter, failure, recovery, and replay refs are all
present.

### User Story 4 - Reject False Production Passes (Priority: P3)

As a Staff reviewer, I need missing transaction, canonical state, idempotency,
event cursor, outbox, artifact index, lease heartbeat, policy, or replay refs
to fail with typed diagnostics instead of being treated as production-ready.

**Independent Test**: Negative fixtures for non-atomic commit, missing
canonical state, missing idempotency, event gap, missing outbox, missing
artifact index, missing lease heartbeat, and missing replay all fail with typed
operator status and cannot produce a passing production persistence report.

## Requirements

- **FR-001**: System MUST define production persistence wiring contracts for
  run-control canonical state persistence reports and fixture manifests.
- **FR-002**: System MUST define typed failure states for missing transaction,
  canonical state, idempotency, event cursor, outbox, artifact index, lease
  heartbeat, policy, and replay refs.
- **FR-003**: System MUST expose a `veracrawl-production-persistence` CLI that
  executes deterministic fixtures and writes `run_report.json`.
- **FR-004**: System MUST persist row 039 canonical run-control state through
  port-shaped persistence APIs, not in process-local state.
- **FR-005**: System MUST persist run-control event refs and build a contiguous
  event cursor after adapter reopen.
- **FR-006**: System MUST persist outbox records and idempotency records so a
  duplicate command after adapter reopen creates zero duplicate events and zero
  duplicate outbox records.
- **FR-007**: System MUST persist artifact index refs for the run-control report
  and replay bundle.
- **FR-008**: System MUST persist queue enqueue, lease, heartbeat, ack, nack,
  dead-letter, failure, and recovery operation refs relevant to the scenario.
- **FR-009**: System MUST register contracts, commands, events, fixture oracles,
  and target area coverage for `production_persistence_runtime_wiring`.
- **FR-010**: System MUST preserve core independence from concrete Postgres,
  Redis/Valkey, S3, browser, model SDK, and agent framework clients; concrete
  adapters remain behind adapter-owned implementations.
- **FR-011**: System MUST preserve all existing 039 run-control and 015-020
  persistence/adapter/infrastructure behavior.

## Key Entities

- **ProductionPersistenceRuntimeReport**: Operator-visible proof that an
  approved run-control execution has durable canonical state, event, outbox,
  idempotency, artifact, queue, policy, and replay refs after adapter reopen.
- **ProductionPersistenceFixtureManifest**: Fixture expectation contract for
  production persistence wiring scenarios.
- **Canonical run-control documents**: Persisted ProductionProject,
  ProductionSiteScope, CrawlObjective, CrawlPlan, RunPlanSnapshot, CrawlRun,
  RunBudget, RunPolicySnapshot, RunApprovalRecord, PolicyDecision,
  RunLifecycleRecord, and ProductionRunControlReport documents.
- **Persistence side effects**: Transaction, durable command, idempotency,
  event cursor, outbox, artifact index, queue operation, lease, failure,
  recovery, policy, and replay refs.

## Non-Goals

- Does not implement live HTTP, browser, structured source, or credentialed
  acquisition.
- Does not create a new Postgres, Redis/Valkey, or S3 adapter; those
  conformance surfaces already exist and remain adapter-owned.
- Does not import concrete database, queue, object store, browser, model SDK,
  or agent framework clients into core packages.
- Does not implement worker autoscaling, deployment, metrics/tracing backends,
  managed cloud operations, or disaster recovery.

## Success Criteria

- **SC-001**: Success fixture persists approved run-control canonical state and
  passes after adapter reopen.
- **SC-002**: Idempotent replay fixture dedupes duplicate command after reopen
  with zero duplicate event/outbox side effects.
- **SC-003**: Queue recovery fixture records heartbeat, nack, dead-letter,
  failure, recovery, lease, and replay refs.
- **SC-004**: Negative fixtures fail with typed missing-ref diagnostics and do
  not claim pass.
- **SC-005**: Registry validation passes and
  `production_persistence_runtime_wiring` target area is materialized.
- **SC-006**: Focused contract/unit/integration tests, CLI fixture loop, ruff,
  mypy, and full non-Docker/Docker-backed test gates pass.
