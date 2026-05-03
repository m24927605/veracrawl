# Tasks: Production Persistence Runtime Wiring

**Input**: Design documents from `/specs/040-production-persistence-runtime-wiring/`

## Phase 1: Contracts And Registry

- [x] T001 Add production persistence failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add production persistence runtime contracts in `src/veracrawl/contracts/objective.py`
- [x] T003 Export production persistence contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_production_persistence_runtime_contracts.py`

## Phase 2: Ports And Persistence Store Support

- [x] T006 Extend persistence ports with canonical document save/load methods in `src/veracrawl/ports/persistence.py`
- [x] T007 Implement canonical document methods in `src/veracrawl/runtime_support/persistence_store.py`
- [x] T008 Implement canonical document methods in `src/veracrawl/adapters/persistence/json_document.py`
- [x] T009 Verify SQLite adapter inherits canonical document behavior in `src/veracrawl/adapters/persistence/sqlite.py`

## Phase 3: Run-Control Detail API And Runtime Wiring

- [x] T010 Add detailed run-control execution result in `src/veracrawl/control/run_control.py`
- [x] T011 Add production persistence wiring runtime in `src/veracrawl/control/production_persistence.py`
- [x] T012 Add CLI in `src/veracrawl/cli/production_persistence.py`
- [x] T013 Add `veracrawl-production-persistence` entry point in `pyproject.toml`
- [x] T014 [P] Add unit tests in `tests/unit/test_production_persistence_runtime.py`
- [x] T015 [P] Add integration tests in `tests/integration/test_production_persistence_runtime_fixtures.py`

## Phase 4: Fixtures

- [x] T016 [P] Add success fixture in `tests/fixtures/production-persistence-wiring-success/`
- [x] T017 [P] Add idempotent replay fixture in `tests/fixtures/production-persistence-idempotent-replay/`
- [x] T018 [P] Add queue recovery fixture in `tests/fixtures/production-persistence-queue-recovery/`
- [x] T019 [P] Add non-atomic commit fixture in `tests/fixtures/production-persistence-non-atomic-commit/`
- [x] T020 [P] Add canonical state missing fixture in `tests/fixtures/production-persistence-canonical-state-missing/`
- [x] T021 [P] Add idempotency missing fixture in `tests/fixtures/production-persistence-idempotency-missing/`
- [x] T022 [P] Add event gap fixture in `tests/fixtures/production-persistence-event-gap/`
- [x] T023 [P] Add outbox missing fixture in `tests/fixtures/production-persistence-outbox-missing/`
- [x] T024 [P] Add artifact index missing fixture in `tests/fixtures/production-persistence-artifact-index-missing/`
- [x] T025 [P] Add lease heartbeat missing fixture in `tests/fixtures/production-persistence-lease-heartbeat-missing/`
- [x] T026 [P] Add replay missing fixture in `tests/fixtures/production-persistence-replay-missing/`

## Phase 5: Docs

- [x] T027 [P] Update `README.md`
- [x] T028 [P] Update `docs/07-data-contracts.md`
- [x] T029 [P] Update `docs/08-build-roadmap.md`
- [x] T030 [P] Update `docs/10-target-implementation-design.md`
- [x] T031 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T032 Update `AGENTS.md` active Spec Kit pointer

## Phase 6: Verification

- [x] T033 Run Spec Kit prerequisite check
- [x] T034 Run `uv lock`
- [x] T035 Run ruff
- [x] T036 Run mypy
- [x] T037 Run registry validation
- [x] T038 Run focused production persistence tests
- [x] T039 Run production persistence CLI fixture loop
- [x] T040 Run full non-Docker pytest gate
- [x] T041 Run Docker-backed pytest gate
- [x] T042 Run `git diff --check`
- [x] T043 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/040-production-persistence-runtime-wiring`.
- 2026-05-03: `uv lock` resolved 30 packages.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed across 213 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 46 target areas, and `production_persistence_runtime_wiring` materialized.
- 2026-05-03: Focused production persistence/run-control tests passed: 45 passed.
- 2026-05-03: `veracrawl-production-persistence` CLI loop passed across 11 fixtures.
- 2026-05-03: Full non-Docker gate passed: 725 passed, 5 skipped.
- 2026-05-03: Docker-backed gate passed: 730 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 46 materialized target
  areas and no unresolved gates.
