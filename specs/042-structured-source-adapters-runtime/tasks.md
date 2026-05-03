# Tasks: Structured Source Adapters Runtime

**Input**: Design documents from `/specs/042-structured-source-adapters-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add structured source failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add structured source contracts in `src/veracrawl/contracts/source_runtime.py`
- [x] T003 Export structured source contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_structured_source_adapters_contracts.py`

## Phase 2: Runtime, Adapter, And CLI

- [x] T006 Add core aggregate runtime in `src/veracrawl/fetch/structured_source.py`
- [x] T007 Add structured fixture source adapters in `src/veracrawl/adapters/sources/structured_runtime.py`
- [x] T008 Add CLI in `src/veracrawl/cli/structured_source.py`
- [x] T009 Add `veracrawl-structured-source` entry point in `pyproject.toml`
- [x] T010 [P] Add unit tests in `tests/unit/test_structured_source_adapters_runtime.py`
- [x] T011 [P] Add integration tests in `tests/integration/test_structured_source_adapters_fixtures.py`

## Phase 3: Fixtures

- [x] T012 [P] Add success fixture with sitemap/RSS/API/document/file sources
- [x] T013 [P] Add policy-denied fixture
- [x] T014 [P] Add malformed-source fixture
- [x] T015 [P] Add unsupported-adapter fixture
- [x] T016 [P] Add replay-mismatch fixture

## Phase 4: Docs

- [x] T017 [P] Update `README.md`
- [x] T018 [P] Update `docs/07-data-contracts.md`
- [x] T019 [P] Update `docs/08-build-roadmap.md`
- [x] T020 [P] Update `docs/10-target-implementation-design.md`
- [x] T021 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T022 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T023 Run Spec Kit prerequisite check
- [x] T024 Run `uv lock`
- [x] T025 Run ruff
- [x] T026 Run mypy
- [x] T027 Run registry validation
- [x] T028 Run focused structured source tests
- [x] T029 Run structured source CLI fixture loop
- [x] T030 Run full non-Docker pytest gate
- [x] T031 Run Docker-backed pytest gate
- [x] T032 Run `git diff --check`
- [x] T033 Record validation results

## Validation Results

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed and resolved `specs/042-structured-source-adapters-runtime`.
- 2026-05-03: `uv lock` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check .` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src tests/contract/test_structured_source_adapters_contracts.py tests/unit/test_structured_source_adapters_runtime.py tests/integration/test_structured_source_adapters_fixtures.py tests/contract/test_contract_registry.py` passed with 222 checked source files.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`, 48 target areas, and `structured_source_adapters_runtime` materialized.
- 2026-05-03: focused structured source pytest passed: 15 tests passed.
- 2026-05-03: `veracrawl-structured-source` CLI loop passed for success, policy-denied, malformed-source, unsupported-adapter, and replay-mismatch fixtures.
- 2026-05-03: full non-Docker pytest passed: 758 passed, 5 skipped.
- 2026-05-03: Docker-backed pytest passed with Postgres, Redis/Valkey, S3-compatible, and infrastructure env flags enabled: 763 passed.
- 2026-05-03: `git diff --check` passed.
- 2026-05-03: Target area readiness scan passed with 48 materialized target areas and no unresolved gates.
