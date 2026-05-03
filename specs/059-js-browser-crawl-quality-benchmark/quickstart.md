# Quickstart: JavaScript Browser Crawl Quality Benchmark

Run deterministic fixture validation:

```sh
uv run --python python3.12 --extra dev veracrawl-browser-quality-benchmark run \
  tests/fixtures/browser-quality-corpus \
  --profile quality \
  --browser-adapter deterministic \
  --out .veracrawl-test-runs/browser-quality-corpus
```

Install browser runtime for live validation:

```sh
uv run --python python3.12 --extra browser-playwright python -m playwright install chromium
```

Run live public browser validation:

```sh
uv run --python python3.12 --extra dev --extra browser-playwright \
  veracrawl-browser-quality-benchmark run \
  tests/fixtures/browser-quality-corpus \
  --profile quality \
  --browser-adapter playwright \
  --out .veracrawl-real-runs/browser-quality-corpus
```

Inspect outputs:

```sh
jq . .veracrawl-real-runs/browser-quality-corpus/summary.json
jq . .veracrawl-real-runs/browser-quality-corpus/browser_quality_report.json
jq . .veracrawl-real-runs/browser-quality-corpus/browser_quality_deltas.json
```

Focused validation:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_browser_quality_contracts.py \
  tests/contract/test_browser_quality_contract_registry.py \
  tests/contract/test_browser_quality_import_boundaries.py \
  tests/unit/test_browser_quality_runtime.py \
  tests/unit/test_browser_quality_replay.py \
  tests/integration/test_browser_quality_fixtures.py
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
