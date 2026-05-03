# Tasks: Field-Level Oracle Extraction Benchmark

**Input**: Design documents from `/specs/061-field-level-oracle-extraction-benchmark/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

## Phase 1: Setup

- [x] T001 Activate `061-field-level-oracle-extraction-benchmark` Spec Kit feature context.
- [x] T002 Add 061 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 061.
- [x] T004 Update `README.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Contracts And Registry

- [x] T005 Add field oracle enums in `src/veracrawl/contracts/enums.py`.
- [x] T006 Add field oracle contracts in `src/veracrawl/contracts/field_oracle.py`.
- [x] T007 Export field oracle contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T008 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T009 Add contract tests.
- [x] T010 Add registry tests.
- [x] T011 Add import-boundary tests.

## Phase 3: Runtime And Replay

- [x] T012 Implement runtime in `src/veracrawl/benchmarks/field_oracle.py`.
- [x] T013 Implement replay helpers in `src/veracrawl/review_replay/field_oracle.py`.
- [x] T014 Add runtime tests.
- [x] T015 Add replay tests.

## Phase 4: CLI And Fixtures

- [x] T016 Add `veracrawl-field-oracle-benchmark` CLI.
- [x] T017 Register CLI entry point.
- [x] T018 Add success fixture.
- [x] T019 Add wrong-value fixture.
- [x] T020 Add missing-anchor fixture.
- [x] T021 Add schema-violation fixture.
- [x] T022 Add stale-evidence fixture.
- [x] T023 Add publication-bypass fixture.
- [x] T024 Add LLM-as-evidence fixture.
- [x] T025 Add integration fixture tests.

## Phase 5: Validation

- [x] T026 Run Spec Kit prerequisite check.
- [x] T027 Run ruff.
- [x] T028 Run mypy.
- [x] T029 Run registry validation.
- [x] T030 Run focused 061 tests.
- [x] T031 Run deterministic field oracle CLI validation.
- [x] T032 Run full pytest.
- [x] T033 Run Docker-backed pytest.
- [x] T034 Run `git diff --check`.
- [x] T035 Record all validation outputs in this file.
- [x] T036 Verify no docs, code, CLI output, or tests claim precision/recall, repair success, or production-quality release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks
  --include-tasks` passed for
  `specs/061-field-level-oracle-extraction-benchmark` with `research.md`,
  `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md` available.
- Initial focused `ruff` found one real line-length issue in
  `src/veracrawl/benchmarks/field_oracle.py`; it was fixed before marking lint
  complete.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src tests`: success across 640
  source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate
  --format json` exited successfully; stored output in
  `.veracrawl-test-runs/field-oracle-registry-validation.json`. Summary via
  `jq` returned `ok: true`, `errors: []`, `warnings: []`, and
  `target_area_count: 65`.
- Focused 061 pytest gate:
  `tests/contract/test_field_oracle_contracts.py`,
  `tests/contract/test_field_oracle_contract_registry.py`,
  `tests/contract/test_field_oracle_import_boundaries.py`,
  `tests/unit/test_field_oracle_runtime.py`,
  `tests/unit/test_field_oracle_replay.py`, and
  `tests/integration/test_field_oracle_fixtures.py` passed with
  `28 passed in 19.40s`.
- Deterministic field oracle CLI gate:
  `uv run --python python3.12 --extra dev veracrawl-field-oracle-benchmark run
  tests/fixtures/field-oracle-quality-corpus --profile quality --out
  .veracrawl-test-runs/field-oracle-quality-corpus` returned `ok: true`,
  `completion_result: pass`, `operator_status: field_oracle_completed`,
  `schema_count: 8`, `expected_field_count: 200`,
  `evaluated_field_count: 200`, `accepted_field_count: 200`,
  `exact_match_count: 67`, `normalized_match_count: 67`,
  `acceptable_partial_count: 66`, and `replay_bundle_count: 200`.
- Full non-Docker pytest gate:
  `uv run --python python3.12 --extra dev pytest` passed with `1160 passed,
  5 skipped in 198.62s`.
- Docker-backed pytest gate:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1
  VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python
  python3.12 --extra dev --extra postgres --extra queue-redis --extra
  object-s3 pytest` passed with `1165 passed in 248.17s`.
- `git diff --check`: passed.
- Boundary check: `rg` confirmed 061-facing docs and tasks describe
  precision/recall thresholds, repair success, and final production-quality
  release readiness as later gates, not as completed by 061.
