# Tasks: VeraCrawl Operational Disaster Recovery Gate

**Input**: Design documents from `specs/021-operational-disaster-recovery-gate/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 021 feature context
- [x] T002 Add `veracrawl-dr` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend DR enums and failure mappings in `src/veracrawl/contracts/enums.py`
- [x] T004 Extend ops contracts with `DRRestorePlan`, `DRRestoreRun`, `DRRestoreFixtureManifest`, and operational DR fields in `src/veracrawl/contracts/ops.py`
- [x] T005 Export new DR contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register DR contracts, commands, events, fixture oracles, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: User Story 1 - Verify Operational DR Pass (P1)

**Independent Test**: `dr-restore-success` passes only when live Postgres, Redis/Valkey, and S3-compatible refs contribute a replay-complete DR report.

- [x] T008 [P] [US1] Add DR contract tests in `tests/contract/test_operational_dr_contracts.py`
- [x] T009 [P] [US1] Add DR registry tests in `tests/contract/test_operational_dr_contract_registry.py`
- [x] T010 [P] [US1] Add success fixture assertion helper in `tests/helpers/dr_fixture_assertions.py`
- [x] T011 [US1] Implement core DR success gate in `src/veracrawl/runtime_support/disaster_recovery.py`
- [x] T012 [US1] Implement dynamic adapter-owned CLI runner in `src/veracrawl/cli/dr.py`
- [x] T013 [US1] Add `dr-restore-success` fixture/oracles under `tests/fixtures/dr-restore-success/`
- [x] T014 [US1] Add operational DR success fixture integration test in `tests/integration/test_operational_dr_fixtures.py`
- [x] T015 [US1] Add Docker-backed live DR gate test in `tests/integration/test_operational_disaster_recovery_live.py`

## Phase 4: User Story 2 - Reject Fake Operational DR Completion (P2)

**Independent Test**: no-runtime and contract-only paths return `needs_review` and cannot claim operational DR pass.

- [x] T016 [P] [US2] Add DR import-boundary test in `tests/contract/test_operational_dr_import_boundaries.py`
- [x] T017 [P] [US2] Add no-runtime fixture/oracles under `tests/fixtures/dr-restore-runtime-unavailable/`
- [x] T018 [US2] Implement no-runtime/contract-only DR result behavior in `src/veracrawl/runtime_support/disaster_recovery.py`
- [x] T019 [US2] Add CLI no-runtime coverage in `tests/integration/test_operational_dr_fixtures.py`

## Phase 5: User Story 3 - Surface DR Failures And Recovery Actions (P3)

**Independent Test**: every negative DR fixture fails deterministically with missing refs, failure records, recovery actions, policy refs, and replay status.

- [x] T020 [P] [US3] Add negative fixture/oracles for missing metadata, artifact, event replay, projection, export, unresolved refs, data loss, and unsafe recovery under `tests/fixtures/`
- [x] T021 [P] [US3] Add negative unit tests in `tests/unit/test_operational_dr_gate.py`
- [x] T022 [US3] Implement negative DR failure scenarios and recovery action generation in `src/veracrawl/runtime_support/disaster_recovery.py`
- [x] T023 [US3] Add negative fixture integration assertions in `tests/integration/test_operational_dr_fixtures.py`

## Phase 6: Documentation And Acceptance

- [x] T024 Update `README.md` with operational DR gate usage and non-completion boundary
- [x] T025 Update `docs/07-data-contracts.md` with operational DR gate contracts, commands, events, fixture rules, and target state
- [x] T026 Update `docs/09-target-capability-model.md` with operational DR acceptance language
- [x] T027 Update `docs/10-target-implementation-design.md` with the operational DR gate slice
- [x] T028 Update `docs/11-target-testing-and-acceptance.md` with DR fixture contract and acceptance gates
- [x] T029 Run registry validation, ruff, mypy, focused tests, CLI no-runtime/negative fixtures, Docker-backed live test, and full test suite
- [x] T030 Record real verification results in this `tasks.md`

## Dependencies

- Phase 1 must complete before contract or implementation work.
- Phase 2 blocks all user stories.
- US1 establishes the success path and live substrate integration.
- US2 depends on shared contracts and can run after US1 contracts exist.
- US3 depends on the DR gate core and can run after US1 success behavior exists.
- Documentation and acceptance run after implementation and tests.

## Parallel Examples

- T008, T009, and T010 can run in parallel after T003-T007.
- T016 and T017 can run in parallel after foundational contracts.
- T020 and T021 can run in parallel after the negative scenario names are fixed.

## Validation Record

- Spec Kit prerequisite check: `.specify/scripts/bash/check-prerequisites.sh --json --include-tasks` returned feature dir `specs/021-operational-disaster-recovery-gate` and available docs `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
- Contract registry validation: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-contracts validate --format json` returned `"ok": true`.
- Ruff: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 ruff check src tests` returned `All checks passed!`.
- Mypy: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 mypy src` returned `Success: no issues found in 167 source files`.
- Focused DR tests: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract/test_operational_dr_contracts.py tests/contract/test_operational_dr_contract_registry.py tests/contract/test_operational_dr_import_boundaries.py tests/unit/test_operational_dr_gate.py tests/integration/test_operational_dr_fixtures.py` returned `14 passed in 0.48s`.
- CLI no-runtime/negative fixtures: `veracrawl-dr run` returned `needs_review` for `dr-restore-runtime-unavailable` and `fail` for all eight negative fixtures with their expected operator statuses.
- Docker-backed live DR gate: `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_disaster_recovery_live.py` returned `1 passed in 3.72s`.
- Full pytest: `uv lock && uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 ruff check src tests && uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 mypy src && VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests` returned `385 passed, 3 skipped in 19.37s`.
