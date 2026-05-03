# Tasks: Browser Snapshot Runtime

**Input**: Design documents from `/specs/043-browser-snapshot-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add browser snapshot failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add browser snapshot report and fixture contracts in `src/veracrawl/contracts/browser.py`
- [x] T003 Export browser snapshot contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_browser_snapshot_contracts.py`

## Phase 2: Runtime, Adapter Boundary, And CLI

- [x] T006 Add core aggregate runtime in `src/veracrawl/browser/snapshot_runtime.py`
- [x] T007 Extend deterministic browser adapter artifact refs without leaking adapter-native state
- [x] T008 Add CLI in `src/veracrawl/cli/browser_snapshot.py`
- [x] T009 Add `veracrawl-browser-snapshot` entry point in `pyproject.toml`
- [x] T010 [P] Add unit tests in `tests/unit/test_browser_snapshot_runtime.py`
- [x] T011 [P] Add integration tests in `tests/integration/test_browser_snapshot_fixtures.py`

## Phase 3: Fixtures

- [x] T012 [P] Add success fixture
- [x] T013 [P] Add egress-denied fixture
- [x] T014 [P] Add unsafe-interaction fixture
- [x] T015 [P] Add budget-exceeded fixture
- [x] T016 [P] Add prompt-tainted-content fixture
- [x] T017 [P] Add missing-artifact fixture
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
- [x] T030 Run focused browser snapshot tests
- [x] T031 Run browser snapshot CLI fixture loop
- [x] T032 Run full non-Docker pytest gate
- [x] T033 Run Docker-backed pytest gate
- [x] T034 Run `git diff --check`
- [x] T035 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/043-browser-snapshot-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check .` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src tests/contract/test_browser_snapshot_contracts.py tests/unit/test_browser_snapshot_runtime.py tests/integration/test_browser_snapshot_fixtures.py tests/contract/test_contract_registry.py` passed with 224 checked source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 49 target areas, and `browser_snapshot_runtime` materialized.
- 2026-05-03: focused browser snapshot pytest passed: 19 tests passed.
- 2026-05-03: `veracrawl-browser-snapshot` CLI loop passed for success, egress-denied, unsafe-interaction, budget-exceeded, prompt-tainted-content, missing-artifact, and replay-mismatch fixtures.
- 2026-05-03: full non-Docker pytest passed: 777 passed, 5 skipped.
- 2026-05-03: Docker-backed pytest passed with Postgres, Redis/Valkey, S3-compatible, and infrastructure env flags enabled: 782 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 49 materialized target areas and no unresolved gates.
