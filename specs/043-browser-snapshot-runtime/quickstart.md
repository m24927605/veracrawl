# Quickstart: Browser Snapshot Runtime

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-browser-snapshot run \
  tests/fixtures/browser-snapshot-success \
  --profile target \
  --out .veracrawl-test-runs/browser-snapshot-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_browser_snapshot_contracts.py \
  tests/unit/test_browser_snapshot_runtime.py \
  tests/integration/test_browser_snapshot_fixtures.py
```
