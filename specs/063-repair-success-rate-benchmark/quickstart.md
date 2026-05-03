# Quickstart: Repair Success Rate Benchmark

Run the deterministic passing fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-repair-quality-benchmark run \
  tests/fixtures/repair-success-quality \
  --profile quality \
  --out .veracrawl-test-runs/repair-success-quality
```

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_repair_success_contracts.py \
  tests/contract/test_repair_success_contract_registry.py \
  tests/contract/test_repair_success_import_boundaries.py \
  tests/unit/test_repair_success_runtime.py \
  tests/unit/test_repair_success_replay.py \
  tests/integration/test_repair_success_fixtures.py
```
