# Tasks: Production Run Control API

**Input**: Design documents from `/specs/039-production-run-control-api/`

## Phase 1: Contracts And Registry

- [x] T001 Add production run-control enums in `src/veracrawl/contracts/enums.py`
- [x] T002 Add run-control contracts in `src/veracrawl/contracts/objective.py`
- [x] T003 Export run-control contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_production_run_control_contracts.py`

## Phase 2: Runtime And CLI

- [x] T006 Add deterministic run-control runtime in `src/veracrawl/control/run_control.py`
- [x] T007 Add CLI in `src/veracrawl/cli/run_control.py`
- [x] T008 Add `veracrawl-run-control` entry point in `pyproject.toml`
- [x] T009 [P] Add unit tests in `tests/unit/test_production_run_control_runtime.py`
- [x] T010 [P] Add integration tests in `tests/integration/test_production_run_control_fixtures.py`

## Phase 3: Fixtures

- [x] T011 [P] Add success fixture in `tests/fixtures/production-run-control-success/`
- [x] T012 [P] Add paused/resumed fixture in `tests/fixtures/production-run-control-paused-resumed/`
- [x] T013 [P] Add cancelled fixture in `tests/fixtures/production-run-control-cancelled/`
- [x] T014 [P] Add policy-denied fixture in `tests/fixtures/production-run-control-policy-denied/`
- [x] T015 [P] Add missing-approval fixture in `tests/fixtures/production-run-control-missing-approval/`
- [x] T016 [P] Add missing-budget fixture in `tests/fixtures/production-run-control-missing-budget/`
- [x] T017 [P] Add invalid-transition fixture in `tests/fixtures/production-run-control-invalid-transition/`
- [x] T018 [P] Add missing-replay fixture in `tests/fixtures/production-run-control-missing-replay/`

## Phase 4: Docs

- [x] T019 [P] Update `README.md`
- [x] T020 [P] Update `docs/07-data-contracts.md`
- [x] T021 [P] Update `docs/08-build-roadmap.md`
- [x] T022 [P] Update `docs/10-target-implementation-design.md`
- [x] T023 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T024 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T025 Run Spec Kit prerequisite check
- [x] T026 Run `uv lock`
- [x] T027 Run ruff
- [x] T028 Run mypy
- [x] T029 Run registry validation
- [x] T030 Run focused run-control tests
- [x] T031 Run run-control CLI fixture loop
- [x] T032 Run full non-Docker pytest gate
- [x] T033 Run Docker-backed pytest gate
- [x] T034 Run `git diff --check`
- [x] T035 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/039-production-run-control-api`.
- 2026-05-03: `uv lock` resolved 30 packages.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed across 211 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 45 target areas, and `production_run_control_api` materialized.
- 2026-05-03: Focused production run-control tests passed: 29 passed.
- 2026-05-03: `veracrawl-run-control` CLI loop passed across 8 fixtures.
- 2026-05-03: Full non-Docker gate passed: 705 passed, 5 skipped.
- 2026-05-03: Docker-backed gate passed: 710 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 45 materialized target areas and no unresolved gates.
