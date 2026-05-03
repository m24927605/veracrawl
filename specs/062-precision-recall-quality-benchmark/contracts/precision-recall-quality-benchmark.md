# Contract: Precision Recall Quality Benchmark

```sh
uv run --python python3.12 --extra dev veracrawl-quality-metrics run \
  tests/fixtures/precision-recall-quality \
  --profile quality \
  --out .veracrawl-real-runs/precision-recall-quality
```

Outputs:

- `precision_recall_report.json`
- `confusion_records.json`
- `slice_metrics.json`
- `summary.json`

Pass requires corpus precision >= 0.98, recall >= 0.90, F1 >= 0.94, critical
precision >= 0.99, visible abstention/unsupported/needs-review rates, and full
evidence/publication/command/event/outbox/replay refs.
