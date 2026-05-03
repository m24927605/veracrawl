# Tasks: Cost Latency Stability Release Gate

## Phase 1: Setup

- [x] T001 Activate `064-quality-release-gate` Spec Kit feature context.
- [x] T002 Add 064 spec, plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 064.
- [x] T004 Update `README.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Contracts And Registry

- [x] T005 Add quality release enums and contracts.
- [x] T006 Export quality release contracts.
- [x] T007 Register contracts, commands, events, fixtures, and target area.
- [x] T008 Add contract, registry, and import-boundary tests.

## Phase 3: Runtime And Replay

- [x] T009 Implement runtime in `src/veracrawl/benchmarks/quality_release.py`.
- [x] T010 Implement replay helpers.
- [x] T011 Add runtime and replay tests.

## Phase 4: CLI And Fixtures

- [x] T012 Add `veracrawl-quality-release-gate` CLI and entry point.
- [x] T013 Add success and negative fixtures.
- [x] T014 Add integration fixture tests.

## Phase 5: Validation

- [x] T015 Run Spec Kit prerequisite check.
- [x] T016 Run ruff.
- [x] T017 Run deterministic quality release CLI validation.
- [x] T018 Run mypy.
- [x] T019 Run registry validation.
- [x] T020 Run focused 064 tests.
- [x] T021 Run full pytest.
- [x] T022 Run Docker-backed pytest.
- [x] T023 Run `git diff --check`.
- [x] T024 Record all validation outputs in this file.
- [x] T025 Verify docs, code, CLI output, and tests claim release readiness only through this gate and only for the defined roadmap rows 058-064.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` completed successfully for `064-quality-release-gate`.
- `uv run --python python3.12 --extra dev ruff check .` passed.
- Deterministic CLI validation passed:
  `uv run --python python3.12 --extra dev veracrawl-quality-release-gate run tests/fixtures/quality-release-ready --profile quality --out .veracrawl-test-runs/quality-release-ready`
  produced `ok=true`, `completion_result=pass`, `release_decision=release_ready`, `observed_quality_gate_count=6`, `stability_run_count=3`, `total_cost_usd=1.32`, `p95_latency_ms=3340`, `throughput_pages_per_minute=41.0`, `retry_rate=0.045`, `token_count=121500`, `model_call_count=249`, and `stability_variance=0.047619047619047616`.
- `uv run --python python3.12 --extra dev mypy src tests` passed with no issues across 670 source files.
- `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; print(validate_registry().model_dump_json(indent=2))'` passed with `ok=true`, no errors, and no warnings.
- Target area count check reported `target_area_count=68`.
- Focused tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_quality_release_contracts.py tests/contract/test_quality_release_contract_registry.py tests/contract/test_quality_release_import_boundaries.py tests/unit/test_quality_release_runtime.py tests/unit/test_quality_release_replay.py tests/integration/test_quality_release_fixtures.py`
  reported `34 passed in 0.77s`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1254 passed, 5 skipped in 243.55s`.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1259 passed in 267.36s`.
- `git diff --check` passed.
- Boundary check with `rg -n "release_ready|release readiness|production crawl quality release|final production" README.md docs specs/064-quality-release-gate src tests` found the new 064 quality release gate, its positive fixture, and pre-existing row 054 production release gate references; intermediate quality specs continue to state non-readiness where applicable. No docs, code, CLI output, or tests claim release readiness outside the defined 054 production release gate or the 064 roadmap rows 058-064 quality release gate.
