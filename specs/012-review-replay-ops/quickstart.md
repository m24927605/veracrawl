# Quickstart: VeraCrawl Review Replay Ops Console

Run the ops console success fixtures:

```sh
for fixture in \
  review-console-success \
  replay-audit-success \
  quality-dashboard-success
do
  uv run --python python3.12 --extra dev veracrawl-ops run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run negative ops fixtures:

```sh
for fixture in \
  missing-review-evidence \
  unresolved-failure-without-recovery \
  stale-dashboard-projection \
  unsafe-recovery-without-review
do
  uv run --python python3.12 --extra dev veracrawl-ops run \
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
