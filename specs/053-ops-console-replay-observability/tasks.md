# Tasks: Ops Console, Replay, And Observability Runtime

**Input**: Design documents from `/specs/053-ops-console-replay-observability/`

## Phase 1: Contracts And Registry

- [x] T001 Add ops replay/observability failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add row 053 contracts in `src/veracrawl/contracts/ops.py`
- [x] T003 Export row 053 contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_ops_replay_observability_contracts.py`
- [x] T006 [P] Add registry tests in `tests/contract/test_ops_replay_observability_contract_registry.py`
- [x] T007 [P] Add import boundary tests in `tests/contract/test_ops_replay_observability_import_boundaries.py`

## Phase 2: Runtime And CLI

- [x] T008 Implement ops replay/observability runtime in `src/veracrawl/ops/replay_observability_runtime.py`
- [x] T009 Implement replay validation in `src/veracrawl/review_replay/ops_runtime.py`
- [x] T010 Implement fixture CLI in `src/veracrawl/cli/ops_runtime.py`
- [x] T011 Register CLI entry point in `pyproject.toml`
- [x] T012 [P] Add runtime unit tests in `tests/unit/test_ops_replay_observability_runtime.py`
- [x] T013 [P] Add replay unit tests in `tests/unit/test_ops_replay_observability_replay.py`

## Phase 3: Fixtures

- [x] T014 [P] Add review/replay success fixture in `tests/fixtures/ops-runtime-review-replay-success`
- [x] T015 [P] Add incident recovery success fixture in `tests/fixtures/ops-runtime-incident-recovery-success`
- [x] T016 [P] Add cost alert success fixture in `tests/fixtures/ops-runtime-cost-alert-success`
- [x] T017 [P] Add missing publication fixture in `tests/fixtures/ops-runtime-missing-publication`
- [x] T018 [P] Add missing worker orchestration fixture in `tests/fixtures/ops-runtime-missing-worker-orchestration`
- [x] T019 [P] Add missing ops console fixture in `tests/fixtures/ops-runtime-missing-ops-console`
- [x] T020 [P] Add missing observability fixture in `tests/fixtures/ops-runtime-missing-observability`
- [x] T021 [P] Add stale dashboard fixture in `tests/fixtures/ops-runtime-stale-dashboard`
- [x] T022 [P] Add unresolved recovery fixture in `tests/fixtures/ops-runtime-unresolved-recovery`
- [x] T023 [P] Add unsafe operator action fixture in `tests/fixtures/ops-runtime-unsafe-operator-action`
- [x] T024 [P] Add replay mismatch fixture in `tests/fixtures/ops-runtime-replay-mismatch`
- [x] T025 [P] Add fixture helper assertions in `tests/helpers/ops_replay_observability_fixture_assertions.py`
- [x] T026 [P] Add fixture integration tests in `tests/integration/test_ops_replay_observability_fixtures.py`

## Phase 4: Docs

- [x] T027 [P] Update `README.md`
- [x] T028 [P] Update `docs/07-data-contracts.md`
- [x] T029 [P] Update `docs/08-build-roadmap.md`
- [x] T030 [P] Update `docs/10-target-implementation-design.md`
- [x] T031 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T032 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T033 Run Spec Kit prerequisite check
- [x] T034 Run `uv lock`
- [x] T035 Run ruff
- [x] T036 Run mypy
- [x] T037 Run registry validation
- [x] T038 Run focused row 053 tests
- [x] T039 Run row 053 CLI fixture loop
- [x] T040 Run full non-Docker pytest gate
- [x] T041 Run Docker-backed pytest gate
- [x] T042 Run `git diff --check`
- [x] T043 Record validation results

## Validation Results

- 2026-05-03: Spec Kit prerequisite check passed for `specs/053-ops-console-replay-observability` with `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md`.
- 2026-05-03: `uv lock` resolved 30 packages.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check .` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src ...` passed with 259 source files.
- 2026-05-03: `uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json` returned `ok: true`.
- 2026-05-03: Focused row 053 contract, registry, import-boundary, unit, replay, integration, and registry tests passed: 23 passed.
- 2026-05-03: `veracrawl-ops-runtime` CLI loop passed all 11 `tests/fixtures/ops-runtime-*` fixtures.
- 2026-05-03: Full non-Docker pytest gate passed: 1007 passed, 5 skipped.
- 2026-05-03: Docker-backed pytest gate passed with Postgres, Redis, S3, and infrastructure flags: 1012 passed.
- 2026-05-03: `git diff --check` passed.
