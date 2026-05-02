# Quickstart: VeraCrawl Export Connectors

Run export success fixtures:

```sh
for fixture in \
  export-file-success \
  export-api-success \
  export-correction-withdrawal-success
do
  uv run --python python3.12 --extra dev veracrawl-export run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run negative export fixtures:

```sh
for fixture in \
  export-missing-receipt \
  duplicate-export-idempotency \
  withdrawal-missing-mapping \
  destination-unsupported-withdrawal \
  correction-without-withdrawal
do
  uv run --python python3.12 --extra dev veracrawl-export run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run verification gates:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest
```
