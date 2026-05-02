# Quickstart: VeraCrawl Scale Hardening

Run scale success fixtures:

```sh
for fixture in \
  scale-sharding-success \
  backpressure-autoscale-success \
  dead-letter-recovery-success
do
  uv run --python python3.12 --extra dev veracrawl-scale run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run negative scale fixtures:

```sh
for fixture in \
  stale-lease-without-recovery \
  unfair-site-starvation \
  autoscale-without-policy \
  dead-letter-missing-failure-record \
  replay-missing-scale-refs
do
  uv run --python python3.12 --extra dev veracrawl-scale run \
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
uv run --python python3.12 --extra dev pytest tests
```
