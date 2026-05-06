# Quickstart: Optimization Objective Gate

## Validate Spec Kit Prerequisites

```bash
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

## Run Targeted Tests

```bash
uv run --extra dev pytest \
  tests/contract/test_crawler_optimization_objective_gate_contracts.py \
  tests/contract/test_crawler_optimization_objective_gate_registry.py \
  tests/contract/test_crawler_optimization_objective_gate_import_boundaries.py \
  tests/unit/test_crawler_optimization_objective_gate.py \
  tests/unit/test_crawler_optimization_objective_gate_replay.py
```

## Run Lint And Type Checks

```bash
uv run --extra dev ruff check
uv run --extra dev mypy \
  src/veracrawl/contracts/crawler_optimization.py \
  src/veracrawl/contracts/registry.py \
  src/veracrawl/optimization/objective_gate.py \
  src/veracrawl/review_replay/crawler_optimization_objective_gate.py
```

## Run Full Regression

```bash
uv run --extra dev pytest
git diff --check
```

## Expected Evidence

- New contracts validate pass and negative cases.
- Runtime score computation matches the approved weighted formula.
- Agent loop evidence rejects missing phases, low confidence, missing stop
  conditions, and LLM output used as evidence.
- Release gate rejects missing/failed 096 lower gate refs and missing replay or
  policy refs.
- Registry exposes contracts, commands, events, and negative fixtures.
- Roadmap docs name 097 as the end-to-end objective gate after specs 080-096.
