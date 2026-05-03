# Data Model: Precision Recall Quality Benchmark

- `QualityMetricThresholds`: versioned precision/recall/F1/critical thresholds.
- `FieldConfusionRecord`: one metric component with TP/FP/FN/TN/abstain/
  unsupported/needs-review class and supporting refs.
- `PrecisionRecallSliceMetric`: aggregate counts/rates for one corpus, schema,
  pattern, source type, rendering mode, or confidence bucket.
- `PrecisionRecallQualityReport`: aggregate quality decision and trace refs.
- `QualityMetricManifest`: fixture input with generated or explicit confusion
  records and expected result.
