# Tasks: VeraCrawl Target Crawl Runtime

**Input**: Design documents from `/specs/034-target-crawl-runtime/`

## Phase 1: Setup

- [x] T001 Add `veracrawl-target-runtime` console script in `pyproject.toml`
- [x] T002 [P] Create target runtime package in `src/veracrawl/target_runtime/__init__.py`
- [x] T003 [P] Create target runtime CLI module in `src/veracrawl/cli/target_runtime.py`
- [x] T004 [P] Create target runtime contract module in `src/veracrawl/contracts/target_runtime.py`

## Phase 2: Contracts And Registry

- [x] T005 [P] Add target runtime status and failure enums in `src/veracrawl/contracts/enums.py`
- [x] T006 Implement target runtime Pydantic contracts in `src/veracrawl/contracts/target_runtime.py`
- [x] T007 Export target runtime contracts in `src/veracrawl/contracts/__init__.py`
- [x] T008 Register target runtime contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`
- [x] T009 [P] Write target runtime contract tests in `tests/contract/test_target_runtime_contracts.py`
- [x] T010 [P] Write target runtime registry assertions in `tests/contract/test_contract_registry.py`

## Phase 3: Runtime And Fixture Harness

- [x] T011 [P] Write import-boundary tests in `tests/unit/test_target_runtime_import_boundaries.py`
- [x] T012 [P] Write target runtime runner tests in `tests/unit/test_target_runtime_runner.py`
- [x] T013 [P] Create target runtime fixture assertion helper in `tests/helpers/target_runtime_fixture_assertions.py`
- [x] T014 [P] Create success fixture and oracle files in `tests/fixtures/target-runtime-success/`
- [x] T015 [P] Create drift-repair and needs-review fixtures in `tests/fixtures/target-runtime-drift-repair/` and `tests/fixtures/target-runtime-needs-review/`
- [x] T016 [P] Create negative fixtures in `tests/fixtures/target-runtime-policy-denied/`, `tests/fixtures/target-runtime-prompt-injection/`, `tests/fixtures/target-runtime-missing-evidence/`, `tests/fixtures/target-runtime-replay-mismatch/`, `tests/fixtures/target-runtime-partial-export/`, and `tests/fixtures/target-runtime-false-complete/`
- [x] T017 Implement deterministic target runtime runner in `src/veracrawl/target_runtime/runner.py`
- [x] T018 Implement target runtime CLI fixture validation and `run_report.json` writing in `src/veracrawl/cli/target_runtime.py`
- [x] T019 Write integration fixture loop tests in `tests/integration/test_target_runtime_fixtures.py`

## Phase 4: Docs And Cross-References

- [x] T020 [P] Update `README.md` with target runtime CLI usage
- [x] T021 [P] Update `docs/07-data-contracts.md` with target runtime contract refs
- [x] T022 [P] Update `docs/09-target-capability-model.md` with executable target runtime capability
- [x] T023 [P] Update `docs/10-target-implementation-design.md` with target runtime module and boundaries
- [x] T024 [P] Update `docs/11-target-testing-and-acceptance.md` with target runtime acceptance fixtures
- [x] T025 [P] Verify `AGENTS.md` active Spec Kit pointer references 034

## Phase 5: Verification

- [x] T026 Run Spec Kit prerequisite check for `specs/034-target-crawl-runtime`
- [x] T027 Run `uv lock`
- [x] T028 Run ruff on `src tests`
- [x] T029 Run mypy on `src`
- [x] T030 Run contract registry validation
- [x] T031 Run focused target runtime tests
- [x] T032 Run target runtime CLI fixture loop
- [x] T033 Run full non-Docker pytest gate
- [x] T034 Run Docker-backed pytest gate
- [x] T035 Run `git diff --check`
- [x] T036 Record validation results in this tasks file

## Dependencies

- Phase 1 must complete before Phase 2.
- Phase 2 contracts must complete before runtime implementation tasks T017-T019.
- Fixture files T014-T016 and tests T011-T013 can be written before runtime implementation.
- Documentation tasks T020-T025 can run after contracts and runtime behavior are stable.
- Verification tasks T026-T036 run last.

## Parallel Execution Examples

- T002, T003, and T004 touch disjoint files and can run in parallel.
- T009, T011, T012, and T013 touch disjoint test/helper files and can run in parallel after contract shape is known.
- T014, T015, and T016 create disjoint fixture directories and can run in parallel.
- T020, T021, T022, T023, and T024 update separate documentation files and can run in parallel after implementation semantics are final.

## Independent Test Criteria

- **US1**: `target-runtime-success` completes with at least seven covered website patterns and every accepted output/evidence/graph/export/replay ref family present.
- **US2**: `target-runtime-drift-repair` records framework-neutral AI recommendation and repair refs without concrete framework imports.
- **US3**: `target-runtime-needs-review` produces operator-visible review and recovery refs without false completion.
- **US4**: Negative fixtures for policy denial, prompt injection, missing evidence, replay mismatch, partial export, and false complete fail deterministically.

## Implementation Verification Record

- Spec Kit prerequisites: passed; feature directory resolved to `specs/034-target-crawl-runtime`.
- `uv lock`: passed; 30 packages resolved.
- `ruff check src tests`: passed.
- `mypy src`: passed; 207 source files checked.
- `veracrawl-contracts validate --format json`: passed; registry validation `ok: true`; `target_crawl_runtime` is `materialized`.
- Focused target runtime tests: passed; 28 tests.
- Target runtime CLI fixture loop: passed; 9 fixtures (`complete`, `needs_review`, `blocked`, and `failed` paths).
- Full non-Docker pytest gate: passed; 635 passed, 5 skipped.
- Docker-backed pytest gate: passed; 640 passed.
- `git diff --check`: passed.
- Registry readiness scan: passed; no missing, unresolved, follow-up, or placeholder target areas.
