# Tasks: Schema Extraction Candidate Runtime

**Input**: Design documents from `/specs/046-schema-extraction-candidate-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add schema extraction failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Extend extraction candidate contract refs in `src/veracrawl/contracts/processing.py`
- [x] T003 Add schema extraction report and fixture contracts in `src/veracrawl/contracts/processing.py`
- [x] T004 Export schema extraction contracts in `src/veracrawl/contracts/__init__.py`
- [x] T005 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T006 [P] Add contract tests in `tests/contract/test_schema_extraction_contracts.py`

## Phase 2: Runtime And CLI

- [x] T007 Add core aggregate runtime in `src/veracrawl/extract/schema_runtime.py`
- [x] T008 Add CLI in `src/veracrawl/cli/schema_extraction.py`
- [x] T009 Add `veracrawl-schema-extraction` entry point in `pyproject.toml`
- [x] T010 [P] Add unit tests in `tests/unit/test_schema_extraction_runtime.py`
- [x] T011 [P] Add integration tests in `tests/integration/test_schema_extraction_fixtures.py`

## Phase 3: Fixtures

- [x] T012 [P] Add record success fixture
- [x] T013 [P] Add exploratory success fixture
- [x] T014 [P] Add browser success fixture
- [x] T015 [P] Add drift repair needs-review fixture
- [x] T016 [P] Add missing-normalization fixture
- [x] T017 [P] Add schema-validation-failed fixture
- [x] T018 [P] Add missing-field-anchor fixture
- [x] T019 [P] Add missing-model-tool-trace fixture
- [x] T020 [P] Add candidate-direct-publication fixture
- [x] T021 [P] Add replay-mismatch fixture

## Phase 4: Docs

- [x] T022 [P] Update `README.md`
- [x] T023 [P] Update `docs/07-data-contracts.md`
- [x] T024 [P] Update `docs/08-build-roadmap.md`
- [x] T025 [P] Update `docs/10-target-implementation-design.md`
- [x] T026 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T027 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T028 Run Spec Kit prerequisite check
- [x] T029 Run `uv lock`
- [x] T030 Run ruff
- [x] T031 Run mypy
- [x] T032 Run registry validation
- [x] T033 Run focused schema extraction tests
- [x] T034 Run schema extraction CLI fixture loop
- [x] T035 Run full non-Docker pytest gate
- [x] T036 Run Docker-backed pytest gate
- [x] T037 Run `git diff --check`
- [x] T038 Record validation results

## Validation Results

- Spec Kit prerequisites: passed with `research.md`, `data-model.md`,
  `contracts/`, `quickstart.md`, and `tasks.md` detected.
- `uv lock`: passed.
- `uv run --python python3.12 --extra dev ruff check .`: passed.
- `uv run --python python3.12 --extra dev mypy src
  tests/contract/test_schema_extraction_contracts.py
  tests/unit/test_schema_extraction_runtime.py
  tests/integration/test_schema_extraction_fixtures.py
  tests/contract/test_contract_registry.py`: passed with 233 source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json`:
  `ok=true`, 52 target areas, `schema_extraction_candidate_runtime`
  materialized, no unresolved target areas.
- Focused pytest:
  `tests/contract/test_schema_extraction_contracts.py`,
  `tests/unit/test_schema_extraction_runtime.py`,
  `tests/integration/test_schema_extraction_fixtures.py`, and
  `tests/contract/test_contract_registry.py`: 29 passed.
- `veracrawl-schema-extraction` CLI loop: record, exploratory, browser,
  drift-repair, missing-normalization, schema-validation-failed,
  missing-field-anchor, missing-model-tool-trace,
  candidate-direct-publication, and replay-mismatch fixtures all matched
  expected pass/needs-review/fail statuses.
- Full non-Docker pytest: 845 passed, 5 skipped.
- Docker-backed pytest with Postgres, Redis, S3, and integrated infrastructure
  gates enabled: 850 passed.
- `git diff --check`: passed.
