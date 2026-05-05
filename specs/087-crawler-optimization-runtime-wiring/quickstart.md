# Quickstart: Crawler Optimization Runtime Wiring

## Run Targeted Tests

```bash
uv run --extra dev pytest \
  tests/contract/test_crawler_optimization_runtime_wiring_contracts.py \
  tests/contract/test_crawler_optimization_runtime_wiring_registry.py \
  tests/contract/test_crawler_optimization_runtime_wiring_import_boundaries.py \
  tests/unit/test_crawler_optimization_runtime_wiring.py \
  tests/unit/test_crawler_optimization_runtime_wiring_replay.py
```

## Run Lint And Types

```bash
uv run --extra dev ruff check \
  src/veracrawl/optimization/runtime.py \
  src/veracrawl/review_replay/crawler_optimization_runtime.py \
  tests/contract/test_crawler_optimization_runtime_wiring_contracts.py \
  tests/unit/test_crawler_optimization_runtime_wiring.py

uv run --extra dev mypy \
  src/veracrawl/optimization/runtime.py \
  src/veracrawl/review_replay/crawler_optimization_runtime.py
```

## Acceptance

The feature is complete when the runtime service can create allowed and blocked
frontier optimization decisions, DOM/extraction contexts, dedupe/ranking
decisions, and aggregate reports without importing benchmark modules or concrete
adapters.
