# Quickstart: Normalize and Extract Plane

## Validate Registry

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```

## Run Process Fixtures

```sh
for fixture in \
  process-static-basic \
  process-link-provenance \
  process-anchored-candidate \
  process-missing-raw \
  process-empty-content \
  process-anchor-gap
do
  uv run --python python3.12 --extra dev veracrawl-process run \
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

Passing this feature proves deterministic normalization, anchor maps, link provenance, page classification, site model, anchored candidates, and replay refs. It does not prove evidence verification, publication, graph projection, memory, export, distributed persistence, or production scale readiness.
