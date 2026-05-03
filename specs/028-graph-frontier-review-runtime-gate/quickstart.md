# Quickstart: Graph-Driven Frontier And Review Runtime Gate

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_graph_frontier_review_contracts.py \
  tests/contract/test_graph_frontier_review_contract_registry.py \
  tests/contract/test_graph_frontier_review_import_boundaries.py \
  tests/unit/test_graph_frontier_review_gate.py \
  tests/integration/test_graph_frontier_review_fixtures.py
```

Run fixtures:

```sh
for fixture in \
  graph-frontier-review-success \
  graph-frontier-review-runtime-unavailable \
  graph-frontier-review-signal-as-evidence \
  graph-frontier-review-missing-source-graph \
  graph-frontier-review-missing-explanation \
  graph-frontier-review-unauthorized-frontier-mutation \
  graph-frontier-review-missing-review-route \
  graph-frontier-review-missing-replay \
  graph-frontier-review-unsupported-signal
do
  uv run --python python3.12 --extra dev veracrawl-graph-frontier-review run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
