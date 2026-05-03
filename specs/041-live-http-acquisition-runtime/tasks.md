# Tasks: Live HTTP Acquisition Runtime

**Input**: Design documents from `/specs/041-live-http-acquisition-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add live HTTP failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add live HTTP contracts in `src/veracrawl/contracts/network.py`
- [x] T003 Export live HTTP contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_live_http_acquisition_contracts.py`

## Phase 2: Runtime And CLI

- [x] T006 Add live HTTP runtime in `src/veracrawl/fetch/live_http.py`
- [x] T007 Add CLI in `src/veracrawl/cli/live_http.py`
- [x] T008 Add `veracrawl-live-http` entry point in `pyproject.toml`
- [x] T009 [P] Add unit tests in `tests/unit/test_live_http_acquisition_runtime.py`
- [x] T010 [P] Add integration tests in `tests/integration/test_live_http_acquisition_fixtures.py`

## Phase 3: Fixtures

- [x] T011 [P] Add success fixture in `tests/fixtures/live-http-success/`
- [x] T012 [P] Add redirect fixture in `tests/fixtures/live-http-redirect/`
- [x] T013 [P] Add scope denied fixture in `tests/fixtures/live-http-scope-denied/`
- [x] T014 [P] Add private denied fixture in `tests/fixtures/live-http-private-denied/`
- [x] T015 [P] Add malformed response fixture in `tests/fixtures/live-http-malformed-response/`
- [x] T016 [P] Add missing artifact fixture in `tests/fixtures/live-http-missing-artifact/`
- [x] T017 [P] Add replay mismatch fixture in `tests/fixtures/live-http-replay-mismatch/`
- [x] T018 [P] Add direct-source bypass fixture in `tests/fixtures/live-http-direct-source-bypass/`

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
- [x] T030 Run focused live HTTP tests
- [x] T031 Run live HTTP CLI fixture loop
- [x] T032 Run full non-Docker pytest gate
- [x] T033 Run Docker-backed pytest gate
- [x] T034 Run `git diff --check`
- [x] T035 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/041-live-http-acquisition-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check .` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src tests/contract/test_live_http_acquisition_contracts.py tests/unit/test_live_http_acquisition_runtime.py tests/integration/test_live_http_acquisition_fixtures.py tests/contract/test_contract_registry.py` passed with 219 checked source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 47 target areas, and `live_http_acquisition_runtime` materialized.
- 2026-05-03: focused live HTTP pytest passed: 18 tests passed.
- 2026-05-03: `veracrawl-live-http` CLI loop passed for success, redirect, scope-denied, private-denied, malformed-response, missing-artifact, replay-mismatch, and direct-source-bypass fixtures.
- 2026-05-03: full non-Docker pytest passed: 743 passed, 5 skipped.
- 2026-05-03: Docker-backed pytest passed with Postgres, Redis/Valkey, S3-compatible, and infrastructure env flags enabled: 748 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 47 materialized target areas and no unresolved gates.
