# Quickstart: VeraCrawl Source-Backed Target Runtime

## Run Source-Backed Success

```sh
uv run --python python3.12 --extra dev veracrawl-target-runtime run \
  tests/fixtures/source-backed-target-success \
  --profile target \
  --out .veracrawl-test-runs/source-backed-target-success
```

## Run Source-Backed Negative Fixtures

```sh
for fixture in \
  source-backed-target-success \
  source-backed-target-policy-denied \
  source-backed-target-prompt-injection \
  source-backed-target-missing-evidence \
  source-backed-target-replay-mismatch \
  source-backed-target-partial-export
do
  uv run --python python3.12 --extra dev veracrawl-target-runtime run \
    "tests/fixtures/$fixture" \
    --profile target \
    --out ".veracrawl-test-runs/$fixture"
done
```

## Focused Tests

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_source_backed_target_runtime_contracts.py \
  tests/unit/test_source_backed_target_runtime_runner.py \
  tests/integration/test_source_backed_target_runtime_fixtures.py
```
