# Quickstart: Cost Latency Stability Release Gate

Run the deterministic passing fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-quality-release-gate run \
  tests/fixtures/quality-release-ready \
  --profile quality \
  --out .veracrawl-test-runs/quality-release-ready
```

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_quality_release_contracts.py \
  tests/contract/test_quality_release_contract_registry.py \
  tests/contract/test_quality_release_import_boundaries.py \
  tests/unit/test_quality_release_runtime.py \
  tests/unit/test_quality_release_replay.py \
  tests/integration/test_quality_release_fixtures.py
```
