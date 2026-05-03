# Quickstart: Credentialed Session Runtime

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-credentialed-session run \
  tests/fixtures/credentialed-session-success \
  --profile target \
  --out .veracrawl-test-runs/credentialed-session-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_credentialed_session_contracts.py \
  tests/unit/test_credentialed_session_runtime.py \
  tests/integration/test_credentialed_session_fixtures.py
```
