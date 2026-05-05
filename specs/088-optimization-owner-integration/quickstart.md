# Quickstart: Optimization Owner-Service Integration

This feature activates the completed crawler optimization runtime through
owner-service integration modules while preserving adapter-free, benchmark-free,
framework-neutral core code.

## Validate Spec Set

```bash
test -f specs/088-optimization-owner-integration/spec.md
test -f specs/089-priority-frontier-scheduler-integration/spec.md
test -f specs/090-dom-intelligence-normalize-integration/spec.md
test -f specs/091-extraction-fallback-verification-integration/spec.md
test -f specs/092-canonical-dedupe-identity-integration/spec.md
test -f specs/093-recommendation-ranking-publication-integration/spec.md
test -f specs/094-optimization-cost-cache-budget-runtime/spec.md
test -f specs/095-drift-recovery-feedback-runtime/spec.md
test -f specs/096-optimization-regression-release-gate/spec.md
```

## Validate Roadmap References

```bash
rg -n "088|089|090|091|092|093|094|095|096" docs/08-build-roadmap.md specs/038-production-runtime-closure/spec.md specs/080-crawler-intelligence-optimization-roadmap/spec.md AGENTS.md
```

## Run Focused Validation

```bash
uv run --extra dev pytest \
  tests/contract/test_crawler_optimization_owner_integration_contracts.py \
  tests/contract/test_crawler_optimization_owner_integration_registry.py \
  tests/contract/test_crawler_optimization_owner_integration_import_boundaries.py \
  tests/unit/test_crawler_optimization_owner_integration.py \
  tests/unit/test_crawler_optimization_owner_integration_replay.py
```

## Validate Spec 096 Release Evidence

```bash
uv run --extra dev pytest \
  tests/unit/test_crawler_optimization_owner_integration_replay.py::test_owner_integration_replay_passes_for_complete_refs \
  tests/contract/test_crawler_optimization_owner_integration_contracts.py::test_regression_gate_pass_requires_lower_report_kind_coverage \
  tests/contract/test_crawler_optimization_owner_integration_contracts.py::test_regression_gate_pass_requires_structured_lower_report_refs
```

## Run Project Validation

```bash
uv run --extra dev ruff check
uv run --extra dev mypy src/veracrawl/scheduler/optimization_integration.py src/veracrawl/normalize/optimization_integration.py src/veracrawl/extract/optimization_integration.py src/veracrawl/graph/optimization_integration.py src/veracrawl/publish/optimization_integration.py src/veracrawl/ops/optimization_integration.py src/veracrawl/review_replay/crawler_optimization_owner_integration.py src/veracrawl/contracts/crawler_optimization.py
uv run --extra dev pytest
git diff --check
```
