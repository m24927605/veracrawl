# Tasks: Live Normalization And Site Understanding

**Input**: Design documents from `/specs/045-live-normalization-site-understanding/`

## Phase 1: Contracts And Registry

- [x] T001 Add live normalization failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add live normalization report and fixture contracts in `src/veracrawl/contracts/processing.py`
- [x] T003 Export live normalization contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_live_normalization_contracts.py`

## Phase 2: Runtime And CLI

- [x] T006 Add core aggregate runtime in `src/veracrawl/normalize/live_runtime.py`
- [x] T007 Add CLI in `src/veracrawl/cli/live_normalization.py`
- [x] T008 Add `veracrawl-live-normalization` entry point in `pyproject.toml`
- [x] T009 [P] Add unit tests in `tests/unit/test_live_normalization_runtime.py`
- [x] T010 [P] Add integration tests in `tests/integration/test_live_normalization_fixtures.py`

## Phase 3: Fixtures

- [x] T011 [P] Add listing success fixture
- [x] T012 [P] Add detail success fixture
- [x] T013 [P] Add browser success fixture
- [x] T014 [P] Add missing-upstream fixture
- [x] T015 [P] Add empty-content fixture
- [x] T016 [P] Add missing-anchor-map fixture
- [x] T017 [P] Add missing-site-model fixture
- [x] T018 [P] Add replay-mismatch fixture

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
- [x] T030 Run focused live normalization tests
- [x] T031 Run live normalization CLI fixture loop
- [x] T032 Run full non-Docker pytest gate
- [x] T033 Run Docker-backed pytest gate
- [x] T034 Run `git diff --check`
- [x] T035 Record validation results

## Validation Results

- Spec Kit prerequisites: passed with `research.md`, `data-model.md`,
  `contracts/`, `quickstart.md`, and `tasks.md` detected.
- `uv lock`: passed.
- `uv run --python python3.12 --extra dev ruff check .`: passed.
- `uv run --python python3.12 --extra dev mypy src
  tests/contract/test_live_normalization_contracts.py
  tests/unit/test_live_normalization_runtime.py
  tests/integration/test_live_normalization_fixtures.py
  tests/contract/test_contract_registry.py`: passed with 231 source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json`:
  `ok=true`, 51 target areas, `live_normalization_site_understanding`
  materialized, no unresolved target areas.
- Focused pytest:
  `tests/contract/test_live_normalization_contracts.py`,
  `tests/unit/test_live_normalization_runtime.py`,
  `tests/integration/test_live_normalization_fixtures.py`, and
  `tests/contract/test_contract_registry.py`: 26 passed.
- `veracrawl-live-normalization` CLI loop: listing, detail, browser,
  missing-upstream, empty-content, missing-anchor-map, missing-site-model, and
  replay-mismatch fixtures all matched expected pass/fail statuses.
- Full non-Docker pytest: 821 passed, 5 skipped.
- Docker-backed pytest with Postgres, Redis, S3, and integrated infrastructure
  gates enabled: 826 passed.
- `git diff --check`: passed.
