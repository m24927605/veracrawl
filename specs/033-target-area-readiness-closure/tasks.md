# Tasks: VeraCrawl Target Area Readiness Impact Closure

**Input**: Design documents from `/specs/033-target-area-readiness-closure/`

## Phase 1: Registry Closure

- [x] T001 Update active Spec Kit pointer in `.specify/feature.json`
- [x] T002 Update active Spec Kit pointer in `AGENTS.md`
- [x] T003 Update materialized target area impact wording in `src/veracrawl/contracts/registry.py`
- [x] T004 Add registry tests for materialized target area readiness wording in `tests/contract/test_contract_registry.py`

## Phase 2: Verification

- [x] T005 Run Spec Kit prerequisite check
- [x] T006 Run `uv lock`
- [x] T007 Run ruff
- [x] T008 Run mypy
- [x] T009 Run registry validation
- [x] T010 Run focused registry tests
- [x] T011 Run full non-Docker pytest gate
- [x] T012 Run Docker-backed pytest gate
- [x] T013 Run `git diff --check` and record validation results

## Implementation Verification Record

- Spec Kit prerequisites: passed; feature directory resolved to `specs/033-target-area-readiness-closure`.
- `uv lock`: passed; lockfile already resolved.
- `ruff check src tests`: passed.
- `mypy src`: passed; 203 source files checked.
- `veracrawl-contracts validate --format json`: passed; registry validation `ok: true`.
- Focused registry tests: passed; 5 tests.
- Full non-Docker pytest gate: passed; 612 passed, 5 skipped.
- Docker-backed pytest gate: passed; 617 passed.
- `git diff --check`: passed.
