# Quickstart: Live HTTP Acquisition Runtime

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-live-http run \
  tests/fixtures/live-http-success \
  --profile target \
  --out .veracrawl-test-runs/live-http-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_live_http_acquisition_contracts.py \
  tests/unit/test_live_http_acquisition_runtime.py \
  tests/integration/test_live_http_acquisition_fixtures.py
```
