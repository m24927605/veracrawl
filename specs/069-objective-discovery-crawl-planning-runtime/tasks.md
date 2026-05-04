# Tasks: Objective Discovery And Crawl Planning Runtime

## Implementation

- [x] T001 Define discovery planning contracts with candidate targets, entry
  points, approval decisions, AI trace refs, policy refs, command/event/outbox
  refs, and replay refs.
- [x] T002 Register discovery planning contracts, commands, events, target area
  coverage, and fixture oracles.
- [x] T003 Implement `veracrawl-discovery-planner` through the shared
  production-grade runtime and CLI.
- [x] T004 Add positive fixture/oracle corpus for objective-to-plan discovery.
- [x] T005 Add contract, registry, runtime, fixture, and import-boundary tests.

## Validation Results

- Focused production-grade tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_production_grade_contracts.py tests/contract/test_production_grade_contract_registry.py tests/contract/test_production_grade_import_boundaries.py tests/unit/test_production_grade_runtime.py tests/integration/test_production_grade_fixtures.py -q`.
- Focused ruff passed:
  `uv run --python python3.12 --extra dev ruff check ...production_grade...`.
- Full-suite validation is recorded in spec 075 after aggregate execution.
