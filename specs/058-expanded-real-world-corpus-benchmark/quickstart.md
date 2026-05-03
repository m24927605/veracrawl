# Quickstart: Expanded Real-World Public Corpus Benchmark

Run deterministic fixture validation:

```sh
uv run --python python3.12 --extra dev veracrawl-real-quality-corpus run \
  tests/fixtures/real-world-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/real-world-quality-corpus
```

Inspect outputs:

```sh
jq . .veracrawl-real-runs/real-world-quality-corpus/summary.json
jq . .veracrawl-real-runs/real-world-quality-corpus/quality_report.json
jq . .veracrawl-real-runs/real-world-quality-corpus/pattern_coverage.json
```

Focused validation:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_real_world_quality_contracts.py \
  tests/contract/test_real_world_quality_contract_registry.py \
  tests/contract/test_real_world_quality_import_boundaries.py \
  tests/unit/test_real_world_quality_runtime.py \
  tests/unit/test_real_world_quality_replay.py \
  tests/integration/test_real_world_quality_fixtures.py
```

Full validation:

```sh
uv run --python python3.12 --extra dev ruff check .
uv run --python python3.12 --extra dev mypy src tests
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev pytest
VERACRAWL_POSTGRES_DOCKER=1 \
VERACRAWL_REDIS_DOCKER=1 \
VERACRAWL_S3_DOCKER=1 \
VERACRAWL_INFRASTRUCTURE_DOCKER=1 \
uv run --python python3.12 \
  --extra dev \
  --extra postgres \
  --extra queue-redis \
  --extra object-s3 \
  pytest
```
