# Tasks: Live Evidence And Verification Runtime

**Input**: Design documents from `/specs/047-live-evidence-verification-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add live evidence failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add live evidence report and fixture contracts in `src/veracrawl/contracts/evidence.py`
- [x] T003 Export live evidence contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_live_evidence_verification_contracts.py`

## Phase 2: Runtime And CLI

- [x] T006 Add core aggregate runtime in `src/veracrawl/evidence/live_verification.py`
- [x] T007 Add CLI in `src/veracrawl/cli/live_evidence.py`
- [x] T008 Add `veracrawl-live-evidence` entry point in `pyproject.toml`
- [x] T009 [P] Add unit tests in `tests/unit/test_live_evidence_verification_runtime.py`
- [x] T010 [P] Add integration tests in `tests/integration/test_live_evidence_verification_fixtures.py`

## Phase 3: Fixtures

- [x] T011 [P] Add success fixture
- [x] T012 [P] Add missing-schema-extraction fixture
- [x] T013 [P] Add missing-source-anchor fixture
- [x] T014 [P] Add stale-evidence fixture
- [x] T015 [P] Add contradiction fixture
- [x] T016 [P] Add graph-only fixture
- [x] T017 [P] Add memory-only fixture
- [x] T018 [P] Add conflict fixture
- [x] T019 [P] Add publication-bypass fixture
- [x] T020 [P] Add replay-mismatch fixture

## Phase 4: Docs

- [x] T021 [P] Update `README.md`
- [x] T022 [P] Update `docs/07-data-contracts.md`
- [x] T023 [P] Update `docs/08-build-roadmap.md`
- [x] T024 [P] Update `docs/10-target-implementation-design.md`
- [x] T025 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T026 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T027 Run Spec Kit prerequisite check
- [x] T028 Run `uv lock`
- [x] T029 Run ruff
- [x] T030 Run mypy
- [x] T031 Run registry validation
- [x] T032 Run focused live evidence tests
- [x] T033 Run live evidence CLI fixture loop
- [x] T034 Run full non-Docker pytest gate
- [x] T035 Run Docker-backed pytest gate
- [x] T036 Run `git diff --check`
- [x] T037 Record validation results

## Validation Results

- Spec Kit prerequisite: passed for `specs/047-live-evidence-verification-runtime`.
- `uv lock`: resolved 30 packages.
- `ruff check .`: passed.
- Focused mypy: passed for `src`, live evidence contract/unit/integration tests, and registry test; 235 source files checked.
- Registry validation: `ok=true`, no errors.
- Focused pytest: 30 passed.
- `veracrawl-live-evidence` CLI loop: 10 fixtures passed.
- Full non-Docker pytest: 870 passed, 5 skipped.
- Docker-backed pytest: 875 passed.
- `git diff --check`: passed.
