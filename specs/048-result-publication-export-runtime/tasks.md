# Tasks: Result Publication And Export Runtime

**Input**: Design documents from `/specs/048-result-publication-export-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add result publication/export failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add Result API snapshot, runtime report, and fixture manifest contracts in `src/veracrawl/contracts/publication.py`
- [x] T003 Export result publication contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_result_publication_export_contracts.py`

## Phase 2: Runtime And CLI

- [x] T006 Add core aggregate runtime in `src/veracrawl/publish/result_runtime.py`
- [x] T007 Add CLI in `src/veracrawl/cli/result_publication.py`
- [x] T008 Add `veracrawl-result-publication` entry point in `pyproject.toml`
- [x] T009 [P] Add unit tests in `tests/unit/test_result_publication_export_runtime.py`
- [x] T010 [P] Add integration tests in `tests/integration/test_result_publication_export_fixtures.py`

## Phase 3: Fixtures

- [x] T011 [P] Add export success fixture
- [x] T012 [P] Add API success fixture
- [x] T013 [P] Add correction/withdrawal success fixture
- [x] T014 [P] Add missing-live-evidence fixture
- [x] T015 [P] Add publication-policy-denied fixture
- [x] T016 [P] Add verification-not-accepted fixture
- [x] T017 [P] Add missing-output-manifest fixture
- [x] T018 [P] Add export-missing-receipt fixture
- [x] T019 [P] Add withdrawal-missing-propagation fixture
- [x] T020 [P] Add correction-without-withdrawal fixture
- [x] T021 [P] Add privacy-missing fixture
- [x] T022 [P] Add direct-export-bypass fixture
- [x] T023 [P] Add replay-mismatch fixture

## Phase 4: Docs

- [x] T024 [P] Update `README.md`
- [x] T025 [P] Update `docs/07-data-contracts.md`
- [x] T026 [P] Update `docs/08-build-roadmap.md`
- [x] T027 [P] Update `docs/10-target-implementation-design.md`
- [x] T028 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T029 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T030 Run Spec Kit prerequisite check
- [x] T031 Run `uv lock`
- [x] T032 Run ruff
- [x] T033 Run mypy
- [x] T034 Run registry validation
- [x] T035 Run focused result publication tests
- [x] T036 Run result publication CLI fixture loop
- [x] T037 Run full non-Docker pytest gate
- [x] T038 Run Docker-backed pytest gate
- [x] T039 Run `git diff --check`
- [x] T040 Record validation results

## Validation Results

- Spec Kit prerequisite: passed for `specs/048-result-publication-export-runtime`.
- `uv lock`: resolved 30 packages.
- `ruff check .`: passed.
- Focused mypy: passed for `src`, result publication contract/unit/integration tests, and registry test; 237 source files checked.
- Registry validation: `ok=true`, no errors.
- Focused pytest: 34 passed.
- `veracrawl-result-publication` CLI loop: 13 fixtures passed.
- Full non-Docker pytest: 899 passed, 5 skipped.
- Docker-backed pytest: 904 passed.
- `git diff --check`: passed.
