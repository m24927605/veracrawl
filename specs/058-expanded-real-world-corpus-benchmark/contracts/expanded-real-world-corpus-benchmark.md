# Contract: Expanded Real-World Public Corpus Benchmark

## CLI

```text
veracrawl-real-quality-corpus run <fixture_dir> --profile quality --out <dir>
```

Outputs:

- `<out>/quality_report.json`
- `<out>/quality_site_observations.json`
- `<out>/pattern_coverage.json`
- `<out>/summary.json`
- `<out>/real_world/run_report.json`
- `<out>/real_world/site_observations.json`
- `<out>/real_world/state/*`

## Commands And Events

- `record_real_world_quality_site_observation`
  - Owner service: `ops`
  - Target aggregate: `RealWorldQualitySiteObservation`
  - Event: `real_world_quality_site_observed`
- `record_real_world_quality_pattern_coverage`
  - Owner service: `ops`
  - Target aggregate: `RealWorldQualityPatternCoverageRecord`
  - Event: `real_world_quality_pattern_coverage_recorded`
- `record_real_world_quality_corpus_report`
  - Owner service: `ops`
  - Target aggregate: `RealWorldQualityCorpusReport`
  - Event: `real_world_quality_corpus_reported`
- `record_real_world_quality_corpus_manifest`
  - Owner service: `tests`
  - Target aggregate: `RealWorldQualityCorpusManifest`
  - Event: `real_world_quality_corpus_manifest_recorded`

## Runtime Flow

1. Load `manifest.yaml` as `RealWorldQualityCorpusManifest`.
2. Convert target specs to a row 055 `RealWorldBenchmarkCorpusManifest`.
3. Run row 055 live HTTP benchmark with the same profile.
4. Build `RealWorldQualitySiteObservation` records from row 055 observations.
5. Build pattern coverage records from passing quality observations.
6. Enforce target, origin, pattern, policy/drift/network, ref, and replay gates.
7. Write deterministic JSON artifacts and summary.

## Negative Cases

- `real-world-quality-insufficient-targets`
- `real-world-quality-insufficient-origins`
- `real-world-quality-insufficient-patterns`
- `real-world-quality-target-drift`
- `real-world-quality-missing-replay`

## Invariants

- Core runtime imports no concrete network adapters, browser engines, model SDKs,
  or agent frameworks.
- Quality thresholds count passing targets only.
- LLM output, graph memory, or inferred page text is not source evidence.
- Policy-denied, network-unavailable, drift, and replay-missing targets do not
  count as passing coverage.
