# Quickstart: Production Run Control API

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-run-control run \
  tests/fixtures/production-run-control-success \
  --profile target \
  --out .veracrawl-test-runs/production-run-control-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_production_run_control_contracts.py \
  tests/unit/test_production_run_control_runtime.py \
  tests/integration/test_production_run_control_fixtures.py
```

Run registry validation:

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```
