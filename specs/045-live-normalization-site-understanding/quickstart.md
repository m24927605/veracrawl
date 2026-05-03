# Quickstart: Live Normalization Runtime

Run the listing success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-live-normalization run \
  tests/fixtures/live-normalization-listing-success \
  --profile target \
  --out .veracrawl-test-runs/live-normalization-listing-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_live_normalization_contracts.py \
  tests/unit/test_live_normalization_runtime.py \
  tests/integration/test_live_normalization_fixtures.py
```
