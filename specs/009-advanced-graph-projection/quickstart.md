# Quickstart: VeraCrawl Advanced Graph Projection Spine

Run focused contract and unit tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_advanced_graph_projection_contract_registry.py \
  tests/contract/test_advanced_graph_projection_contracts.py \
  tests/contract/test_advanced_graph_projection_import_boundaries.py \
  tests/unit/test_advanced_graph_projection.py \
  tests/unit/test_advanced_graph_replay.py \
  tests/unit/test_graph_signal_evidence_boundary.py \
  tests/integration/test_advanced_graph_projection_fixtures.py
```

Run advanced graph projection fixtures:

```sh
for fixture in \
  projection-rebuild-success \
  graph-signal-frontier-review \
  temporal-graph-foundation \
  projection-missing-watermark \
  projection-mismatch \
  graph-signal-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-projection run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run full local gate:

```sh
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest
```
