# Tasks: VeraCrawl Processing/Evidence Target Runtime Gate

**Input**: Design documents from `/specs/037-processing-evidence-target-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add processing/evidence contracts in `src/veracrawl/contracts/target_runtime.py`
- [x] T002 Export processing/evidence contracts in `src/veracrawl/contracts/__init__.py`
- [x] T003 Extend target runtime failure enum in `src/veracrawl/contracts/enums.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_processing_evidence_target_runtime_contracts.py`

## Phase 2: Runtime, Materialization, And Fixtures

- [x] T006 Add deterministic processing/evidence materialization in `src/veracrawl/adapters/sources/target_processing.py`
- [x] T007 Extend target runtime runner to enforce processing/evidence records in `src/veracrawl/target_runtime/runner.py`
- [x] T008 Extend target runtime CLI to load processing/evidence manifests outside core in `src/veracrawl/cli/target_runtime.py`
- [x] T009 [P] Add processing/evidence success fixture in `tests/fixtures/processing-evidence-target-success/`
- [x] T010 [P] Add processing/evidence negative fixtures
- [x] T011 [P] Add unit tests in `tests/unit/test_processing_evidence_target_runtime_runner.py`
- [x] T012 [P] Add integration fixture tests in `tests/integration/test_processing_evidence_target_runtime_fixtures.py`
- [x] T013 [P] Extend import-boundary tests if needed

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
- [x] T025 Run focused processing/evidence tests
- [x] T026 Run target runtime CLI loop including 034, 035, 036, and 037 fixtures
- [x] T027 Run full non-Docker pytest gate
- [x] T028 Run Docker-backed pytest gate
- [x] T029 Run `git diff --check`
- [x] T030 Record validation results

## Independent Test Criteria

- Processing/evidence success completes with seven processing/evidence records.
- Negative processing/evidence fixtures fail with typed target runtime failures.
- Existing deterministic 034, source-backed 035, and adapter-backed 036 fixtures still pass.

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/037-processing-evidence-target-runtime`.
- 2026-05-03: `uv lock` resolved 30 packages without lock drift.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed across 209 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- 2026-05-03: Focused processing/evidence target runtime tests passed: 25 passed.
- 2026-05-03: Target runtime CLI loop for specs 034, 035, 036, and 037 passed across 27 fixtures.
- 2026-05-03: Full non-Docker gate passed: 685 passed, 5 skipped.
- 2026-05-03: Docker-backed gate passed: 690 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 44 materialized target areas, no unresolved gates, and `processing_evidence_target_runtime` materialized.
