# Quickstart: Production Benchmark And Release Gate

Run one fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-release-gate run \
  tests/fixtures/production-release-benchmark-success \
  --profile target \
  --telemetry-backend-ref telemetry-backend:local \
  --collector-handoff-ref collector-handoff:local \
  --out .veracrawl-test-runs/production-release-benchmark-success
```

Run all row 054 fixtures:

```sh
for fixture in tests/fixtures/production-release-*; do
  uv run --python python3.12 --extra dev veracrawl-release-gate run \
    "$fixture" \
    --profile target \
    --telemetry-backend-ref telemetry-backend:local \
    --collector-handoff-ref collector-handoff:local \
    --out ".veracrawl-test-runs/$(basename "$fixture")"
done
```

Validation:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv lock
uv run --python python3.12 --extra dev ruff check .
uv run --python python3.12 --extra dev mypy src tests/contract/test_production_benchmark_release_contracts.py tests/contract/test_production_benchmark_release_contract_registry.py tests/contract/test_production_benchmark_release_import_boundaries.py tests/unit/test_production_benchmark_release_gate.py tests/unit/test_production_benchmark_release_replay.py tests/integration/test_production_benchmark_release_fixtures.py tests/helpers/production_benchmark_release_fixture_assertions.py tests/contract/test_contract_registry.py
uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json
uv run --python python3.12 --extra dev pytest tests/contract/test_production_benchmark_release_contracts.py tests/contract/test_production_benchmark_release_contract_registry.py tests/contract/test_production_benchmark_release_import_boundaries.py tests/unit/test_production_benchmark_release_gate.py tests/unit/test_production_benchmark_release_replay.py tests/integration/test_production_benchmark_release_fixtures.py tests/contract/test_contract_registry.py
uv run --python python3.12 --extra dev pytest
VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest
git diff --check
```
