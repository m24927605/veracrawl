# Tasks: Crawler Intelligence Optimization Roadmap

**Feature**: 080 crawler intelligence optimization roadmap and specs 081-086  
**Branch**: `080-crawler-intelligence-optimization`

## Completed

- [x] T001 Define shared crawler optimization contracts for frontier scoring,
  DOM understanding, extractor fallback/confidence, canonicalization/dedupe,
  ranking, metrics, architecture, and algorithm recommendations.
- [x] T002 Implement deterministic frontier score formula and replayable score
  breakdown records.
- [x] T003 Implement DOM pruning, page-zone classification, and interactive
  element ranking over source-backed HTML artifacts.
- [x] T004 Implement extractor fallback chain, field confidence scores, and
  abstention records.
- [x] T005 Implement URL canonicalization, tracking/session/sort parameter
  removal, SimHash, MinHash, identity decisions, and duplicate suppression.
- [x] T006 Implement heuristic recommendation ranking and ranking evaluation
  metrics.
- [x] T007 Implement aggregate optimization report, negative fixture mapping,
  replay helper, CLI, registry entries, and fixture oracles.
- [x] T008 Add contract, registry, unit, replay, import-boundary, and
  integration fixture tests.
- [x] T009 Run targeted tests, lint, mypy, and CLI smoke validation.

## Validation

- `uv run --extra dev pytest tests/contract/test_crawler_optimization_contracts.py tests/contract/test_crawler_optimization_contract_registry.py tests/contract/test_crawler_optimization_import_boundaries.py tests/unit/test_crawler_optimization_runtime.py tests/unit/test_crawler_optimization_replay.py tests/integration/test_crawler_optimization_fixtures.py`
- `uv run --extra dev ruff check src/veracrawl/contracts/crawler_optimization.py src/veracrawl/benchmarks/crawler_optimization.py src/veracrawl/cli/crawler_optimization.py src/veracrawl/review_replay/crawler_optimization.py tests/contract/test_crawler_optimization_contracts.py tests/contract/test_crawler_optimization_contract_registry.py tests/contract/test_crawler_optimization_import_boundaries.py tests/unit/test_crawler_optimization_runtime.py tests/unit/test_crawler_optimization_replay.py tests/integration/test_crawler_optimization_fixtures.py`
- `uv run --extra dev mypy src/veracrawl/contracts/crawler_optimization.py src/veracrawl/benchmarks/crawler_optimization.py src/veracrawl/cli/crawler_optimization.py src/veracrawl/review_replay/crawler_optimization.py`
- `uv run --extra dev veracrawl-crawler-optimization run tests/fixtures/crawler-optimization-success --out /tmp/veracrawl-crawler-optimization-success`
