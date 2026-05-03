# Tasks: Credentialed Session Runtime

**Input**: Design documents from `/specs/044-credentialed-session-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add credentialed session failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add credentialed session report and fixture contracts in `src/veracrawl/contracts/security_privacy.py`
- [x] T003 Export credentialed session contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_credentialed_session_contracts.py`

## Phase 2: Runtime, Adapter, And CLI

- [x] T006 Add session port in `src/veracrawl/ports/session.py`
- [x] T007 Add core aggregate runtime in `src/veracrawl/fetch/credentialed_session.py`
- [x] T008 Add deterministic session adapter in `src/veracrawl/adapters/session/deterministic.py`
- [x] T009 Add CLI in `src/veracrawl/cli/credentialed_session.py`
- [x] T010 Add `veracrawl-credentialed-session` entry point in `pyproject.toml`
- [x] T011 [P] Add unit tests in `tests/unit/test_credentialed_session_runtime.py`
- [x] T012 [P] Add integration tests in `tests/integration/test_credentialed_session_fixtures.py`

## Phase 3: Fixtures

- [x] T013 [P] Add success fixture
- [x] T014 [P] Add missing-authorization fixture
- [x] T015 [P] Add out-of-scope fixture
- [x] T016 [P] Add raw-secret-leak fixture
- [x] T017 [P] Add unsafe-use fixture
- [x] T018 [P] Add missing-audit fixture
- [x] T019 [P] Add missing-redacted-replay fixture
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
- [x] T032 Run focused credentialed session tests
- [x] T033 Run credentialed session CLI fixture loop
- [x] T034 Run full non-Docker pytest gate
- [x] T035 Run Docker-backed pytest gate
- [x] T036 Run `git diff --check`
- [x] T037 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/044-credentialed-session-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check .` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src tests/contract/test_credentialed_session_contracts.py tests/unit/test_credentialed_session_runtime.py tests/integration/test_credentialed_session_fixtures.py tests/contract/test_contract_registry.py` passed with 229 checked source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 50 target areas, and `credentialed_session_runtime` materialized.
- 2026-05-03: focused credentialed session pytest passed: 23 tests passed.
- 2026-05-03: `veracrawl-credentialed-session` CLI loop passed for success, missing-authorization, out-of-scope, raw-secret-leak, unsafe-use, missing-audit, missing-redacted-replay, and replay-mismatch fixtures.
- 2026-05-03: full non-Docker pytest passed: 800 passed, 5 skipped.
- 2026-05-03: Docker-backed pytest passed with Postgres, Redis/Valkey, S3-compatible, and infrastructure env flags enabled: 805 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 50 materialized target areas and no unresolved gates.
