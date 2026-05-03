# Tasks: Repair Success Rate Benchmark

## Phase 1: Setup

- [x] T001 Activate `063-repair-success-rate-benchmark` Spec Kit feature context.
- [x] T002 Add 063 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 063.
- [x] T004 Update `README.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Contracts And Registry

- [x] T005 Add repair success enums and contracts.
- [x] T006 Export repair success contracts.
- [x] T007 Register contracts, commands, events, fixtures, and target area.
- [x] T008 Add contract, registry, and import-boundary tests.

## Phase 3: Runtime And Replay

- [x] T009 Implement runtime in `src/veracrawl/benchmarks/repair_success.py`.
- [x] T010 Implement replay helpers.
- [x] T011 Add runtime and replay tests.

## Phase 4: CLI And Fixtures

- [x] T012 Add `veracrawl-repair-quality-benchmark` CLI and entry point.
- [x] T013 Add success and negative fixtures.
- [x] T014 Add integration fixture tests.

## Phase 5: Validation

- [x] T015 Run Spec Kit prerequisite check.
- [x] T016 Run ruff.
- [x] T017 Run deterministic repair quality CLI validation.
- [x] T018 Run mypy.
- [x] T019 Run registry validation.
- [x] T020 Run focused 063 tests.
- [x] T021 Run full pytest.
- [x] T022 Run Docker-backed pytest.
- [x] T023 Run `git diff --check`.
- [x] T024 Record all validation outputs in this file.
- [x] T025 Verify no docs, code, CLI output, or tests claim final cost/latency/stability release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` completed successfully for `063-repair-success-rate-benchmark`.
- Initial `uv run --python python3.12 --extra dev ruff check .` failed with one import-order issue in `src/veracrawl/contracts/__init__.py`; `uv run --python python3.12 --extra dev ruff check . --fix` fixed it.
- `uv run --python python3.12 --extra dev ruff check .` passed after the fix.
- Deterministic CLI validation passed:
  `uv run --python python3.12 --extra dev veracrawl-repair-quality-benchmark run tests/fixtures/repair-success-quality --profile quality --out .veracrawl-test-runs/repair-success-quality`
  produced `ok=true`, `completion_result=pass`, `operator_status=repair_quality_completed`, `repair_success_rate=0.9375`, `unsafe_bypass_rate=0.0`, `unresolved_critical_rate=0.0`, `seeded_case_count=37`, `repair_attempt_count=37`, `repairable_case_count=32`, `repaired_case_count=30`, `total_token_count=13653`, `total_cost_usd=0.1813`, and `p95_latency_ms=1795`.
- `uv run --python python3.12 --extra dev mypy src tests` passed with no issues across 660 source files.
- Initial registry command `veracrawl-contracts validate --format json` emitted the registry JSON rather than a validation report, so validation was rerun through `validate_registry()` directly.
- `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; print(validate_registry().model_dump_json(indent=2))'` passed with `ok=true`, no errors, and no warnings.
- Target area count check reported `target_area_count=67`.
- Focused tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_repair_success_contracts.py tests/contract/test_repair_success_contract_registry.py tests/contract/test_repair_success_import_boundaries.py tests/unit/test_repair_success_runtime.py tests/unit/test_repair_success_replay.py tests/integration/test_repair_success_fixtures.py`
  reported `33 passed in 4.05s`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1220 passed, 5 skipped in 241.82s`.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1225 passed in 272.15s`.
- `git diff --check` passed.
- Boundary check with `rg -n "final production-quality release|cost/latency/stability release|production-quality release readiness|final cost/latency/stability" README.md docs specs/063-repair-success-rate-benchmark src tests` found only explicit non-claim or later-spec references; no docs, code, CLI output, or tests claim final cost/latency/stability release completion.
