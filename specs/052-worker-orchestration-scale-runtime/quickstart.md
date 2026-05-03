# Quickstart: Worker Orchestration And Scale Runtime

Run focused checks:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_worker_orchestration_contracts.py \
  tests/unit/test_worker_orchestration_runtime.py \
  tests/integration/test_worker_orchestration_fixtures.py
```

Run all row 052 fixtures:

```sh
tmpdir=$(mktemp -d)
for fixture in tests/fixtures/worker-orchestration-*; do
  uv run --python python3.12 --extra dev veracrawl-worker-orchestration run \
    "$fixture" \
    --profile target \
    --out "$tmpdir/$(basename "$fixture")"
done
```

Validate the registry:

```sh
uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json
```
