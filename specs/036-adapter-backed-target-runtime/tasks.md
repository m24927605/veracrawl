# Tasks: VeraCrawl Adapter-Backed Target Runtime

**Input**: Design documents from `/specs/036-adapter-backed-target-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add adapter-backed target runtime contracts in `src/veracrawl/contracts/target_runtime.py`
- [x] T002 Export adapter-backed contracts in `src/veracrawl/contracts/__init__.py`
- [x] T003 Extend target runtime failure enum in `src/veracrawl/contracts/enums.py`
- [x] T004 Register adapter-backed contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add adapter-backed contract tests in `tests/contract/test_adapter_backed_target_runtime_contracts.py`

## Phase 2: Runtime, Adapter Materialization, And Fixtures

- [x] T006 Add deterministic adapter-backed materialization in `src/veracrawl/adapters/sources/target_runtime.py`
- [x] T007 Extend target runtime runner to enforce adapter-backed records in `src/veracrawl/target_runtime/runner.py`
- [x] T008 Extend target runtime CLI to load adapter-backed manifests outside core in `src/veracrawl/cli/target_runtime.py`
- [x] T009 [P] Add adapter-backed success fixture in `tests/fixtures/adapter-backed-target-success/`
- [x] T010 [P] Add adapter-backed negative fixtures in `tests/fixtures/adapter-backed-target-missing-adapter-result/`, `tests/fixtures/adapter-backed-target-output-mismatch/`, `tests/fixtures/adapter-backed-target-policy-denied/`, `tests/fixtures/adapter-backed-target-replay-mismatch/`, and `tests/fixtures/adapter-backed-target-direct-source-bypass/`
- [x] T011 [P] Add adapter-backed runtime unit tests in `tests/unit/test_adapter_backed_target_runtime_runner.py`
- [x] T012 [P] Add adapter-backed integration fixture tests in `tests/integration/test_adapter_backed_target_runtime_fixtures.py`
- [x] T013 [P] Extend import-boundary tests for adapter-backed runtime in `tests/unit/test_target_runtime_import_boundaries.py`

## Phase 3: Docs

- [x] T014 [P] Update `README.md`
- [x] T015 [P] Update `docs/07-data-contracts.md`
- [x] T016 [P] Update `docs/09-target-capability-model.md`
- [x] T017 [P] Update `docs/10-target-implementation-design.md`
- [x] T018 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T019 [P] Update `AGENTS.md` active Spec Kit pointer

## Phase 4: Verification

- [x] T020 Run Spec Kit prerequisite check
- [x] T021 Run `uv lock`
- [x] T022 Run ruff
- [x] T023 Run mypy
- [x] T024 Run registry validation
- [x] T025 Run focused adapter-backed tests
- [x] T026 Run target runtime CLI loop including 034, 035, and 036 fixtures
- [x] T027 Run full non-Docker pytest gate
- [x] T028 Run Docker-backed pytest gate
- [x] T029 Run `git diff --check`
- [x] T030 Record validation results

## Independent Test Criteria

- Adapter-backed success completes with seven adapter-backed source records derived through adapter materialization.
- Negative adapter-backed fixtures block or fail with typed target runtime failures.
- Existing deterministic 034 and source-backed 035 fixtures still pass.

## Implementation Verification Record

- 2026-05-03: Spec Kit prerequisite check passed for `specs/036-adapter-backed-target-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed with 208 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with 0 registry errors and 43 target areas.
- 2026-05-03: Focused adapter-backed contract, unit, integration, import-boundary, and registry tests passed: 23 passed.
- 2026-05-03: `veracrawl-target-runtime` CLI loop passed for 21 fixtures: 9 deterministic target-runtime fixtures, 6 source-backed target-runtime fixtures, and 6 adapter-backed target-runtime fixtures.
- 2026-05-03: Full non-Docker gate passed: 667 passed, 5 skipped.
- 2026-05-03: Docker-backed gate passed: 672 passed.
- 2026-05-03: Target readiness scan passed with no missing or unresolved target areas; `adapter_backed_target_runtime` is `materialized`.
- 2026-05-03: `git diff --check` passed.
