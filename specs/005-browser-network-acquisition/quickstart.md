# Quickstart: Browser and Network Acquisition Runtime

## Validate Registry

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```

## Run Success Fixtures

```sh
for fixture in \
  network-http-success \
  network-http-redirect \
  network-browser-readonly
do
  uv run --python python3.12 --extra dev veracrawl-network run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

## Run Negative Fixtures

```sh
for fixture in \
  network-robots-blocked \
  network-private-denied \
  network-egress-denied \
  network-rate-budget \
  network-size-budget \
  network-redirect-denied \
  network-timeout \
  network-browser-unsafe-side-effect
do
  uv run --python python3.12 --extra dev veracrawl-network run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

## Run Quality Gate

```sh
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest
```

## Non-Completion Boundary

Passing this feature proves real local HTTP acquisition, network/browser contracts, browser sandbox gates, replay refs, and deterministic fixture coverage. It does not prove full browser rendering, authenticated crawling, graph/memory intelligence, export delivery, distributed persistence, or production scale readiness.
