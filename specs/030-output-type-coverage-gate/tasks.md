# Tasks: VeraCrawl Target Output Type Coverage Gate

**Input**: Design documents from `/specs/030-output-type-coverage-gate/`

## Phase 1: Setup

- [x] T001 Add `veracrawl-output-coverage` console script target in `pyproject.toml`
- [x] T002 [P] Create output coverage CLI in `src/veracrawl/cli/output_coverage.py`
- [x] T003 [P] Create output coverage runtime in `src/veracrawl/publish/output_coverage.py`

## Phase 2: Contracts And Registry

- [x] T004 [P] Add output coverage enums in `src/veracrawl/contracts/enums.py`
- [x] T005 [P] Add output coverage contracts in `src/veracrawl/contracts/publication.py`
- [x] T006 Export output coverage contracts in `src/veracrawl/contracts/__init__.py`
- [x] T007 Extend registry for output coverage contracts, commands, events, fixtures, and target area coverage
- [x] T008 [P] Write contract tests
- [x] T009 [P] Write registry tests
- [x] T010 [P] Write import-boundary tests

## Phase 3: Runtime, Fixtures, Tests

- [x] T011 [P] Write unit gate tests
- [x] T012 [P] Create fixture assertion helpers
- [x] T013 Create success, needs-review, and negative fixtures
- [x] T014 Implement success, needs-review, and negative runtime behavior
- [x] T015 Implement CLI fixture validation and `run_report.json` writing
- [x] T016 [P] Write integration fixture tests

## Phase 4: Docs And Verification

- [x] T017 [P] Update README usage notes
- [x] T018 [P] Update `docs/07-data-contracts.md`
- [x] T019 [P] Update `docs/09-target-capability-model.md`
- [x] T020 [P] Update `docs/10-target-implementation-design.md`
- [x] T021 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T022 [P] Update active Spec Kit pointer in `AGENTS.md`
- [x] T023 Run Spec Kit prerequisite check
- [x] T024 Run `uv lock`
- [x] T025 Run ruff
- [x] T026 Run mypy
- [x] T027 Run registry validation
- [x] T028 Run focused output coverage tests
- [x] T029 Run output coverage CLI fixture loop
- [x] T030 Run full non-Docker pytest gate
- [x] T031 Run Docker-backed pytest gate
- [x] T032 Run `git diff --check` and record validation results

## Implementation Verification Record

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/030-output-type-coverage-gate`.
- `uv lock` passed.
- `uv run --python python3.12 --extra dev ruff check src tests` passed.
- `uv run --python python3.12 --extra dev mypy src` passed with 195 source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json`
  passed with registry validation `ok: true`.
- Focused output coverage pytest passed: 17 passed in 0.78s.
- Output coverage CLI fixture loop passed for success, runtime-unavailable, and
  all thirteen negative fixtures.
- Full non-Docker pytest gate passed: 545 passed, 5 skipped in 16.90s.
- Docker-backed pytest gate passed: 550 passed in 41.92s.
- `git diff --check` passed after this verification record update.
