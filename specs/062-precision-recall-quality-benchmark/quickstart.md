# Quickstart: Precision Recall Quality Benchmark

```sh
uv run --python python3.12 --extra dev veracrawl-quality-metrics run \
  tests/fixtures/precision-recall-quality \
  --profile quality \
  --out .veracrawl-test-runs/precision-recall-quality
```

Expected pass: precision >= 0.98, recall >= 0.90, F1 >= 0.94, critical
precision >= 0.99, and every metric component has replayable supporting refs.
