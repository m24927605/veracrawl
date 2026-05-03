# Quickstart: Structured Source Adapters Runtime

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-structured-source run \
  tests/fixtures/structured-source-adapters-success \
  --profile target \
  --out .veracrawl-test-runs/structured-source-adapters-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_structured_source_adapters_contracts.py \
  tests/unit/test_structured_source_adapters_runtime.py \
  tests/integration/test_structured_source_adapters_fixtures.py
```
