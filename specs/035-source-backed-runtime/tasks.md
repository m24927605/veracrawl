# Tasks: VeraCrawl Source-Backed Target Runtime

**Input**: Design documents from `/specs/035-source-backed-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add source-backed target runtime contracts in `src/veracrawl/contracts/target_runtime.py`
- [x] T002 Export source-backed contracts in `src/veracrawl/contracts/__init__.py`
- [x] T003 Register source-backed contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`
- [x] T004 [P] Add source-backed contract tests in `tests/contract/test_source_backed_target_runtime_contracts.py`

## Phase 2: Runtime And Fixtures

- [x] T005 Extend target runtime runner to read local source corpus manifests in `src/veracrawl/target_runtime/runner.py`
- [x] T006 Extend target runtime CLI to pass fixture directory context in `src/veracrawl/cli/target_runtime.py`
- [x] T007 [P] Add source-backed success fixture corpus in `tests/fixtures/source-backed-target-success/`
- [x] T008 [P] Add source-backed negative fixtures in `tests/fixtures/source-backed-target-policy-denied/`, `tests/fixtures/source-backed-target-prompt-injection/`, `tests/fixtures/source-backed-target-missing-evidence/`, `tests/fixtures/source-backed-target-replay-mismatch/`, and `tests/fixtures/source-backed-target-partial-export/`
- [x] T009 [P] Add source-backed runtime unit tests in `tests/unit/test_source_backed_target_runtime_runner.py`
- [x] T010 [P] Add source-backed integration fixture tests in `tests/integration/test_source_backed_target_runtime_fixtures.py`
- [x] T011 [P] Extend import-boundary tests for source-backed runtime in `tests/unit/test_target_runtime_import_boundaries.py`

## Phase 3: Docs

- [x] T012 [P] Update `README.md`
- [x] T013 [P] Update `docs/07-data-contracts.md`
- [x] T014 [P] Update `docs/09-target-capability-model.md`
- [x] T015 [P] Update `docs/10-target-implementation-design.md`
- [x] T016 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T017 [P] Update `AGENTS.md` active Spec Kit pointer

## Phase 4: Verification

- [x] T018 Run Spec Kit prerequisite check
- [x] T019 Run `uv lock`
- [x] T020 Run ruff
- [x] T021 Run mypy
- [x] T022 Run registry validation
- [x] T023 Run focused source-backed tests
- [x] T024 Run target runtime CLI loop including 034 and 035 fixtures
- [x] T025 Run full non-Docker pytest gate
- [x] T026 Run Docker-backed pytest gate
- [x] T027 Run `git diff --check`
- [x] T028 Record validation results

## Independent Test Criteria

- Source-backed success completes with seven patterns derived from local files.
- Negative source-backed fixtures block or fail with typed target runtime failures.
- Existing deterministic 034 fixtures still pass.

## Implementation Verification Record

- 2026-05-03: Spec Kit prerequisite check passed for `specs/035-source-backed-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed with 207 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with 0 registry errors and 42 target areas.
- 2026-05-03: Focused source-backed contract, unit, integration, import-boundary, and registry tests passed: 21 passed.
- 2026-05-03: `veracrawl-target-runtime` CLI loop passed for 15 fixtures: 9 deterministic target-runtime fixtures and 6 source-backed target-runtime fixtures.
- 2026-05-03: Full non-Docker gate passed: 650 passed, 5 skipped.
- 2026-05-03: Docker-backed gate passed: 655 passed.
- 2026-05-03: Target readiness scan passed with no missing or unresolved target areas; `source_backed_target_runtime` is `materialized`.
- 2026-05-03: `git diff --check` passed.
