# Tasks: Precision Recall Quality Benchmark

## Phase 1: Setup

- [x] T001 Activate `062-precision-recall-quality-benchmark` Spec Kit feature context.
- [x] T002 Add 062 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 062.
- [x] T004 Update `README.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Contracts And Registry

- [x] T005 Add quality metric enums and contracts.
- [x] T006 Export quality metric contracts.
- [x] T007 Register contracts, commands, events, fixtures, and target area.
- [x] T008 Add contract, registry, and import-boundary tests.

## Phase 3: Runtime And Replay

- [x] T009 Implement runtime in `src/veracrawl/benchmarks/quality_metrics.py`.
- [x] T010 Implement replay helpers.
- [x] T011 Add runtime and replay tests.

## Phase 4: CLI And Fixtures

- [x] T012 Add `veracrawl-quality-metrics` CLI and entry point.
- [x] T013 Add success and negative fixtures.
- [x] T014 Add integration fixture tests.

## Phase 5: Validation

- [x] T015 Run Spec Kit prerequisite check.
- [x] T016 Run ruff.
- [x] T017 Run mypy.
- [x] T018 Run registry validation.
- [x] T019 Run focused 062 tests.
- [x] T020 Run deterministic quality metrics CLI validation.
- [x] T021 Run full pytest.
- [x] T022 Run Docker-backed pytest.
- [x] T023 Run `git diff --check`.
- [x] T024 Record all validation outputs in this file.
- [x] T025 Verify no docs, code, CLI output, or tests claim repair success or production-quality release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` completed successfully for `062-precision-recall-quality-benchmark`.
- Initial focused `ruff` validation found one line-length issue in `src/veracrawl/benchmarks/quality_metrics.py`; the line was wrapped and validation reran.
- `uv run --python python3.12 --extra dev ruff check .` passed.
- Deterministic CLI validation passed:
  `uv run --python python3.12 --extra dev veracrawl-quality-metrics --fixture tests/fixtures/precision-recall-quality --output .veracrawl-test-runs/precision-recall-quality`
  produced `ok=true`, `completion_result=pass`, `operator_status=quality_metrics_completed`, `precision=0.9920634920634921`, `recall=0.9615384615384616`, `f1=0.9765625`, `confusion_record_count=314`, `slice_metric_count=6`, `critical_field_precision=1.0`.
- `uv run --python python3.12 --extra dev mypy src tests` passed with no issues across 650 source files.
- `uv run --python python3.12 --extra dev veracrawl-validate-registry --output .veracrawl-test-runs/quality-metrics-registry-validation.json` passed with `ok=true`, no errors, no warnings, and `target_area_count=66`.
- Focused tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_quality_metrics_contracts.py tests/contract/test_quality_metrics_contract_registry.py tests/contract/test_quality_metrics_import_boundaries.py tests/unit/test_quality_metrics_runtime.py tests/unit/test_quality_metrics_replay.py tests/integration/test_quality_metrics_fixtures.py`
  reported `27 passed in 42.04s`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1187 passed, 5 skipped in 239.17s`.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1192 passed in 271.42s`.
- `git diff --check` passed.
- Boundary check with `rg -n "repair success|production-quality release|cost/latency" README.md docs specs/062-precision-recall-quality-benchmark src tests` found only roadmap/later-spec references and the explicit T025 task text; no 062 docs, code, CLI output, or tests claim repair success or production-quality release completion.
