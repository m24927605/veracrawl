# Quickstart: VeraCrawl Target Crawl Runtime

## Run The Success Fixture

```sh
uv run --python python3.12 --extra dev veracrawl-target-runtime run \
  tests/fixtures/target-runtime-success \
  --profile target \
  --out .veracrawl-test-runs/target-runtime-success
```

Expected result:

```json
{"ok": true, "fixture_id": "target-runtime-success", "status": "complete", "completion_result": "pass"}
```

The generated report is written to:

```text
.veracrawl-test-runs/target-runtime-success/run_report.json
```

## Run All Target Runtime Fixtures

```sh
for fixture in \
  target-runtime-success \
  target-runtime-drift-repair \
  target-runtime-needs-review \
  target-runtime-policy-denied \
  target-runtime-prompt-injection \
  target-runtime-missing-evidence \
  target-runtime-replay-mismatch \
  target-runtime-partial-export \
  target-runtime-false-complete
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
  tests/contract/test_target_runtime_contracts.py \
  tests/unit/test_target_runtime_runner.py \
  tests/unit/test_target_runtime_import_boundaries.py \
  tests/integration/test_target_runtime_fixtures.py
```

## Required Final Gates

```sh
uv lock
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 \
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
  pytest tests/contract tests/unit tests/integration
git diff --check
```

## Acceptance Notes

- Success requires at least seven website patterns in one run.
- AI planning/repair must appear through framework-neutral recommendation records.
- `needs_review`, `blocked`, and `failed` fixtures must not be mislabeled complete.
- No target runtime core module may import concrete agent frameworks, model SDKs, storage clients, queue clients, browser runtimes, HTTP clients, export targets, UI frameworks, or site-specific scraper modules.
