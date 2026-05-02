# Tasks: VeraCrawl Durable Runtime Persistence and Scheduler Foundation

**Input**: Design documents from `/specs/003-durable-runtime-scheduler/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements durable command, event, outbox, artifact, scheduler, lease, and replay recovery foundations. Contract, unit, integration, fixture/oracle, negative, replay, registry, and import-boundary tests must be written before implementation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared durable foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Each task includes exact file paths.

## Phase 1: Setup

**Purpose**: Prepare CLI, package, fixture, and test locations without changing behavior.

- [X] T001 Add `veracrawl-durable` console script target in `pyproject.toml`
- [X] T002 [P] Create durable CLI module in `src/veracrawl/cli/durable.py`
- [X] T003 [P] Create durable contract module in `src/veracrawl/contracts/durable.py`
- [X] T004 [P] Create scheduler contract module in `src/veracrawl/contracts/scheduler.py`
- [X] T005 [P] Create recovery contract module in `src/veracrawl/contracts/recovery.py`
- [X] T006 [P] Create durable port module in `src/veracrawl/ports/durable.py`
- [X] T007 [P] Create scheduler port module in `src/veracrawl/ports/scheduler.py`
- [X] T008 [P] Create deterministic durable store module in `src/veracrawl/runtime_support/durable_store.py`
- [X] T009 [P] Create durable fixture assertion helpers in `tests/helpers/durable_fixture_assertions.py`
- [X] T010 [P] Create durable fixture directories and README placeholders under `tests/fixtures/durable-runtime-success/`, `tests/fixtures/durable-duplicate-command/`, `tests/fixtures/durable-event-gap/`, `tests/fixtures/durable-pending-outbox/`, `tests/fixtures/durable-stale-lease/`, `tests/fixtures/durable-invalid-lease/`, and `tests/fixtures/durable-missing-artifact/`

---

## Phase 2: Foundational

**Purpose**: Define durable contracts, ports, registry entries, fixture contracts, and import boundaries that all user stories depend on.

### Foundational Tests

- [X] T011 [P] Write durable registry tests for contracts, commands, events, fixtures, and target area coverage in `tests/contract/test_durable_contract_registry.py`
- [X] T012 [P] Write durable port/import-boundary tests rejecting concrete storage, queue, browser, model SDK, agent framework, and site-specific imports in `tests/contract/test_durable_ports_and_boundaries.py`
- [X] T013 [P] Write durable contract validation tests for command records, event cursors, outbox records, recovery reports, frontier items, and leases in `tests/contract/test_scheduler_contracts.py`

### Foundational Implementation

- [X] T014 [P] Implement durable lifecycle enums for unit of work, command records, outbox, frontier, leases, retry, and recovery in `src/veracrawl/contracts/enums.py`
- [X] T015 [P] Implement UnitOfWorkRecord, DurableCommandRecord, OutboxRecord, EventCursorRecord, and DurableFixtureManifest in `src/veracrawl/contracts/durable.py`
- [X] T016 [P] Implement FrontierItem, QueueLease, and SchedulerRecoveryReport in `src/veracrawl/contracts/scheduler.py`
- [X] T017 [P] Implement DurableReplayRecoveryReport in `src/veracrawl/contracts/recovery.py`
- [X] T018 Implement durable UoW, command repository, event store, outbox, artifact index, and durable state repository protocols in `src/veracrawl/ports/durable.py`
- [X] T019 Implement scheduler frontier and queue lease repository protocols in `src/veracrawl/ports/scheduler.py`
- [X] T020 Extend contract exports for durable and scheduler models in `src/veracrawl/contracts/__init__.py`
- [X] T021 Extend registry registrations for durable contracts, scheduler contracts, recovery contracts, command types, event types, and fixtures in `src/veracrawl/contracts/registry.py`

**Checkpoint**: Durable contracts, ports, registry entries, and boundary tests are ready.

---

## Phase 3: User Story 1 - Persist Runtime State Through Ports (Priority: P1)

**Goal**: Persist command, event, outbox, artifact, and replay refs through deterministic durable ports and reload them across store instances.

**Independent Test**: `veracrawl-durable run tests/fixtures/durable-runtime-success --profile target --out .veracrawl-test-runs/durable-runtime-success` and integration tests prove durable refs survive reload and recovery passes.

### Tests for User Story 1

- [X] T022 [P] [US1] Write command idempotency tests for duplicate command handling in `tests/unit/test_durable_command_idempotency.py`
- [X] T023 [P] [US1] Write durable event cursor and outbox state tests in `tests/unit/test_durable_event_outbox.py`
- [X] T024 [P] [US1] Write durable runtime persistence integration test in `tests/integration/test_durable_runtime_persistence.py`
- [X] T025 [P] [US1] Create success fixture manifest and oracle data under `tests/fixtures/durable-runtime-success/`
- [X] T026 [P] [US1] Create duplicate-command fixture manifest and oracle data under `tests/fixtures/durable-duplicate-command/`

### Implementation for User Story 1

- [X] T027 [US1] Implement deterministic shared durable backing store and repository reload behavior in `src/veracrawl/runtime_support/durable_store.py`
- [X] T028 [US1] Implement idempotent durable command handling in `src/veracrawl/runtime_support/durable_store.py`
- [X] T029 [US1] Implement append-only durable event cursor building in `src/veracrawl/runtime_events/durable.py`
- [X] T030 [US1] Implement outbox append, dispatch, failure, and pending listing in `src/veracrawl/runtime_support/durable_store.py`
- [X] T031 [US1] Implement durable artifact ref indexing and validation in `src/veracrawl/runtime_support/durable_store.py`
- [X] T032 [US1] Implement durable success and duplicate-command fixture runner paths in `src/veracrawl/cli/durable.py`

**Checkpoint**: User Story 1 is independently functional and proves durable refs and idempotency without production infrastructure adapters.

---

## Phase 4: User Story 2 - Schedule Frontier Work With Leases (Priority: P2)

**Goal**: Enqueue, lease, heartbeat, complete, release, expire, retry, and dead-letter frontier work through scheduler owner contracts.

**Independent Test**: Scheduler contract and unit tests prove lease-token validation, expiry, retry, and dead-letter behavior without concrete queue clients.

### Tests for User Story 2

- [X] T033 [P] [US2] Write scheduler lease transition tests in `tests/unit/test_scheduler_leases.py`
- [X] T034 [P] [US2] Write invalid lease fixture manifest and oracle data under `tests/fixtures/durable-invalid-lease/`
- [X] T035 [P] [US2] Write stale lease fixture manifest and oracle data under `tests/fixtures/durable-stale-lease/`

### Implementation for User Story 2

- [X] T036 [US2] Implement frontier enqueue and highest-priority lease selection in `src/veracrawl/scheduler/runtime.py`
- [X] T037 [US2] Implement queue lease heartbeat, completion, and release with token validation in `src/veracrawl/scheduler/runtime.py`
- [X] T038 [US2] Implement lease expiry, retry, and dead-letter transitions in `src/veracrawl/scheduler/runtime.py`
- [X] T039 [US2] Implement scheduler recovery report generation in `src/veracrawl/scheduler/runtime.py`
- [X] T040 [US2] Extend durable fixture runner for stale lease and invalid lease scenarios in `src/veracrawl/cli/durable.py`

**Checkpoint**: User Story 2 is independently functional and scheduler state remains durable, owner-controlled, and replay-visible.

---

## Phase 5: User Story 3 - Recover From Crash And Replay Gaps (Priority: P3)

**Goal**: Detect event gaps, pending outbox records, missing artifacts, stale leases, invalid leases, and dead letters through typed durable replay recovery reports.

**Independent Test**: Negative durable fixtures produce fail or needs-review recovery reports and never claim full production completion.

### Tests for User Story 3

- [X] T041 [P] [US3] Write durable replay recovery unit tests in `tests/unit/test_durable_replay_recovery.py`
- [X] T042 [P] [US3] Write negative durable fixture integration tests in `tests/integration/test_durable_negative_fixtures.py`
- [X] T043 [P] [US3] Create event-gap fixture manifest and oracle data under `tests/fixtures/durable-event-gap/`
- [X] T044 [P] [US3] Create pending-outbox fixture manifest and oracle data under `tests/fixtures/durable-pending-outbox/`
- [X] T045 [P] [US3] Create missing-artifact fixture manifest and oracle data under `tests/fixtures/durable-missing-artifact/`

### Implementation for User Story 3

- [X] T046 [US3] Implement durable replay recovery validation in `src/veracrawl/review_replay/durable.py`
- [X] T047 [US3] Implement event-gap detection from durable event cursors in `src/veracrawl/runtime_events/durable.py`
- [X] T048 [US3] Implement pending outbox and missing artifact recovery checks in `src/veracrawl/review_replay/durable.py`
- [X] T049 [US3] Implement stale lease, invalid lease, retry, and dead-letter recovery checks in `src/veracrawl/review_replay/durable.py`
- [X] T050 [US3] Extend durable fixture runner for event-gap, pending-outbox, and missing-artifact scenarios in `src/veracrawl/cli/durable.py`

**Checkpoint**: User Story 3 is independently functional and durable replay recovery blocks false completion.

---

## Phase 6: User Story 4 - Preserve Adapter-Neutral Durable Boundaries (Priority: P4)

**Goal**: Ensure durable runtime and scheduler core remains framework-neutral and infrastructure-adapter-neutral.

**Independent Test**: Import-boundary and registry tests prove no concrete storage, queue, browser, model SDK, agent framework, or site-specific module enters core.

### Tests for User Story 4

- [X] T051 [P] [US4] Extend import-boundary assertions for durable runtime and scheduler modules in `tests/contract/test_durable_ports_and_boundaries.py`
- [X] T052 [P] [US4] Write registry target-area assertions for durable persistence and scheduler compatibility in `tests/contract/test_durable_contract_registry.py`

### Implementation for User Story 4

- [X] T053 [US4] Register durable persistence and scheduler target areas without production adapter claims in `src/veracrawl/contracts/registry.py`
- [X] T054 [US4] Update deterministic fixture adapters to remain under `runtime_support` and not under core owner packages in `src/veracrawl/runtime_support/durable_store.py`

**Checkpoint**: User Story 4 is independently functional and core remains adapter-neutral.

---

## Phase 7: Polish And Cross-Cutting Concerns

**Purpose**: Verify consistency across the full durable scheduler foundation and prepare the next workflow.

- [X] T055 [P] Update package usage notes for durable runtime and scheduler validation in `README.md`
- [X] T056 [P] Update target implementation notes for durable scheduler package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T057 [P] Update target testing notes for durable fixtures and recovery gates in `docs/11-target-testing-and-acceptance.md`
- [X] T058 Run `veracrawl-contracts validate --format json`
- [X] T059 Run durable success and negative fixture CLI commands from `specs/003-durable-runtime-scheduler/quickstart.md`
- [X] T060 Run ruff, mypy, and pytest full durable-scheduler gate with a 30-second local timing check
- [X] T061 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in `specs/003-durable-runtime-scheduler/tasks.md`
- [X] T062 Verify every task maps to a contract, owner service, command/event, fixture/oracle, or verification check
- [X] T063 Confirm no code, docs, tests, CLI output, or task text claims full production crawler, production persistence, full browser, full graph/memory, full export, or production scale readiness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **US1 - Durable State**: Depends on Phase 2 and proves durable refs and idempotency.
- **US2 - Scheduler Leases**: Depends on Phase 2 and can proceed after scheduler contracts exist.
- **US3 - Recovery**: Depends on Phase 2 and integrates durable state plus scheduler leases.
- **US4 - Adapter Neutrality**: Depends on Phase 2 and hardens boundaries across all user stories.
- **Polish**: Depends on selected user stories being complete.

### Parallel Opportunities

- Setup tasks T002-T010 can run in parallel.
- Foundational tests T011-T013 can run in parallel.
- Foundational models T014-T017 can run in parallel before exports and registry work.
- US1 tests T022-T026 can run in parallel.
- US2 tests T033-T035 can run in parallel.
- US3 fixture tasks T043-T045 can run in parallel with recovery tests.
- Documentation tasks T055-T057 can run in parallel after implementation stabilizes.

## Implementation Verification Record

- 2026-05-02: Re-ran Spec Kit prerequisite check with `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`; feature dir and required docs resolved.
- 2026-05-02: Re-ran cross-artifact consistency checks equivalent to `$speckit-analyze`: 18 functional requirements, 8 success criteria, T001-T063 contiguous, no blocking placeholders, and durable contract, scheduler contract, port, fixture, replay recovery, and import-boundary coverage present.
- 2026-05-02: Verified `veracrawl-contracts validate --format json` reports no registry errors.
- 2026-05-02: Verified `veracrawl-durable run tests/fixtures/durable-runtime-success --profile target --out .veracrawl-test-runs/durable-runtime-success` returns `pass`.
- 2026-05-02: Verified durable duplicate-command, event-gap, pending-outbox, stale-lease, invalid-lease, and missing-artifact fixtures produce typed outcomes.
- 2026-05-02: Verified full durable-scheduler gate: `ruff check src tests`, `mypy src`, and `pytest` pass in 1 second, under the 30-second target.
- 2026-05-02: Confirmed no task text claims full production crawler completion, production persistence adapter readiness, full browser capability, full graph/memory capability, full export capability, or production scale readiness.
