# Tasks: VeraCrawl Target Product Acceptance Gate

**Input**: Design documents from `/specs/032-product-acceptance-gate/`

## Phase 1: Setup

- [x] T001 Add `veracrawl-product-acceptance` console script target in `pyproject.toml`
- [x] T002 [P] Create product acceptance CLI in `src/veracrawl/cli/product_acceptance.py`
- [x] T003 [P] Create product acceptance runtime in `src/veracrawl/product_acceptance/gate.py`

## Phase 2: Contracts And Registry

- [x] T004 [P] Add product acceptance enums in `src/veracrawl/contracts/enums.py`
- [x] T005 [P] Add product acceptance contracts in `src/veracrawl/contracts/product_acceptance.py`
- [x] T006 Export product acceptance contracts in `src/veracrawl/contracts/__init__.py`
- [x] T007 Extend registry for product acceptance contracts, commands, events, fixtures, and target area coverage
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
- [x] T028 Run focused product acceptance tests
- [x] T029 Run product acceptance CLI fixture loop
- [x] T030 Run full non-Docker pytest gate
- [x] T031 Run Docker-backed pytest gate
- [x] T032 Run `git diff --check` and record validation results

## Implementation Verification Record

- Spec Kit prerequisites: passed; feature directory resolved to `specs/032-product-acceptance-gate`.
- `uv lock`: passed; lockfile already resolved.
- `ruff check src tests`: passed.
- `mypy src`: passed; 203 source files checked.
- `veracrawl-contracts validate --format json`: passed; registry validation `ok: true`.
- Focused product acceptance tests: passed; 49 tests.
- Product acceptance CLI fixture loop: passed; 14 fixtures (`pass`, `needs_review`, and 12 typed `fail` paths).
- Full non-Docker pytest gate: passed; 611 passed, 5 skipped.
- Docker-backed pytest gate: passed; 616 passed.
- `git diff --check`: passed.
