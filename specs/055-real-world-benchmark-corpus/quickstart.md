# Quickstart: Real-World Benchmark Corpus Gate

Run the default public corpus:

```bash
uv run --python python3.12 --extra dev veracrawl-real-benchmark run \
  tests/fixtures/real-world-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/real-world-public-corpus
```

Inspect the aggregate report:

```bash
jq . .veracrawl-real-runs/real-world-public-corpus/run_report.json
```

Expected result:

- `completion_result` is `pass`
- `operator_status` is `real_world_benchmark_completed`
- every site observation has live HTTP, network response, artifact, content hash, canonical URL, command/event/outbox, policy, and replay refs

Run focused validation:

```bash
uv run --python python3.12 --extra dev ruff check \
  src/veracrawl/contracts/real_world_benchmark.py \
  src/veracrawl/benchmarks/real_world.py \
  src/veracrawl/cli/real_benchmark.py \
  tests/contract/test_real_world_benchmark_contracts.py \
  tests/unit/test_real_world_benchmark_runtime.py \
  tests/integration/test_real_world_benchmark_fixtures.py

uv run --python python3.12 --extra dev pytest \
  tests/contract/test_real_world_benchmark_contracts.py \
  tests/contract/test_real_world_benchmark_contract_registry.py \
  tests/contract/test_real_world_benchmark_import_boundaries.py \
  tests/unit/test_real_world_benchmark_runtime.py \
  tests/unit/test_real_world_benchmark_replay.py \
  tests/integration/test_real_world_benchmark_fixtures.py
```
