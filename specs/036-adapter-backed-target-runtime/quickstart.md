# Quickstart: VeraCrawl Adapter-Backed Target Runtime

## Run Adapter-Backed Success

```bash
uv run --python python3.12 --extra dev veracrawl-target-runtime run \
  tests/fixtures/adapter-backed-target-success \
  --profile target \
  --out .veracrawl-test-runs/adapter-backed-target-success
```

## Run Adapter-Backed Negative Fixtures

```bash
for fixture in \
  adapter-backed-target-success \
  adapter-backed-target-missing-adapter-result \
  adapter-backed-target-output-mismatch \
  adapter-backed-target-policy-denied \
  adapter-backed-target-replay-mismatch \
  adapter-backed-target-direct-source-bypass
do
  uv run --python python3.12 --extra dev veracrawl-target-runtime run \
    "tests/fixtures/$fixture" \
    --profile target \
    --out ".veracrawl-test-runs/$fixture"
done
```

## Focused Tests

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_adapter_backed_target_runtime_contracts.py \
  tests/unit/test_adapter_backed_target_runtime_runner.py \
  tests/integration/test_adapter_backed_target_runtime_fixtures.py \
  tests/unit/test_target_runtime_import_boundaries.py
```
