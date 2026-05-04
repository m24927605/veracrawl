# Tasks: Production Grade Web Crawler Release Gate

## Implementation

- [x] T001 Define aggregate release contracts: gate report, capability matrix,
  release blocker, release decision, false-ready guard, and release report.
- [x] T002 Register aggregate release contracts, commands, events, target area
  coverage, and fixture oracles.
- [x] T003 Implement lower-gate report ingestion so 075 cannot pass from
  ref-only strings or missing lower gate data.
- [x] T004 Add positive and missing-lower-gate fixtures/oracles.
- [x] T005 Add contract, registry, runtime, fixture, and import-boundary tests.
- [x] T006 Run full validation suite and write exact results here.
- [x] T007 Commit and fast-forward merge implementation.

## Validation Results

- Focused production-grade tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_production_grade_contracts.py tests/contract/test_production_grade_contract_registry.py tests/contract/test_production_grade_import_boundaries.py tests/unit/test_production_grade_runtime.py tests/integration/test_production_grade_fixtures.py -q`.
- Focused ruff passed:
  `uv run --python python3.12 --extra dev ruff check ...production_grade...`.
- Registry validation passed:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`.
- Full ruff passed:
  `uv run --python python3.12 --extra dev ruff check .`.
- Full mypy passed:
  `uv run --python python3.12 --extra dev mypy src tests` returned
  `Success: no issues found in 688 source files`.
- Registry validation passed:
  `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; r=validate_registry(); print({"ok": r.ok, "errors": r.errors, "warnings": r.warnings})'`
  returned `{'ok': True, 'errors': [], 'warnings': []}`.
- Focused production-grade tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_production_grade_contracts.py tests/contract/test_production_grade_contract_registry.py tests/contract/test_production_grade_import_boundaries.py tests/unit/test_production_grade_runtime.py tests/integration/test_production_grade_fixtures.py -q`
  returned 29 passing tests.
- First full pytest run failed honestly:
  `uv run --python python3.12 --extra dev pytest -q` failed at
  `tests/contract/test_contract_registry.py::test_target_contract_area_coverage_is_explicit`
  because the new `production_grade_web_crawler_release_gate` target area was
  not added to the explicit registry whitelist.
- Fix applied:
  `tests/contract/test_contract_registry.py` now includes
  `production_grade_web_crawler_release_gate` in the expected target area set.
- Targeted rerun passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_contract_registry.py::test_target_contract_area_coverage_is_explicit -q`.
- Full pytest rerun passed:
  `uv run --python python3.12 --extra dev pytest -q` exited 0.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest -q`
  exited 0.
- Final ruff after docs/spec/test updates passed:
  `uv run --python python3.12 --extra dev ruff check .`.
