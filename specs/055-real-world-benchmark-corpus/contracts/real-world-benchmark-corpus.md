# Contract: Real-World Benchmark Corpus Gate

## Commands

- `record_real_world_benchmark_site_observation`
  - Owner: `ops`
  - Target aggregate: `RealWorldBenchmarkSiteObservation`
  - Emits: `real_world_benchmark_site_observed`
  - Required policy decisions: `source_adapter`, `fetch`, `runtime_verification`

- `record_real_world_benchmark_run_report`
  - Owner: `ops`
  - Target aggregate: `RealWorldBenchmarkRunReport`
  - Emits: `real_world_benchmark_run_reported`
  - Required policy decisions: `source_adapter`, `fetch`, `runtime_verification`

- `record_real_world_benchmark_corpus_manifest`
  - Owner: `tests`
  - Target aggregate: `RealWorldBenchmarkCorpusManifest`
  - Emits: `real_world_benchmark_corpus_manifest_recorded`

## Events

- `real_world_benchmark_site_observed`
- `real_world_benchmark_run_reported`
- `real_world_benchmark_corpus_manifest_recorded`

Every event must retain stable refs only. Raw external page bodies are artifact-backed and must not be copied into event payloads.

## CLI

```text
veracrawl-real-benchmark run <fixture_dir> --profile target --out <dir>
```

Required behavior:

- Load `manifest.yaml` as `RealWorldBenchmarkCorpusManifest`.
- Enforce profile, origin allowlist, private-network denial, robots preflight, timeout, and size budgets.
- Execute each target through existing live HTTP runtime.
- Evaluate declared observations.
- Write:
  - `run_report.json`
  - `site_observations.json`
  - `summary.json`
  - state files under `state/`
- Exit non-zero when the manifest expectation is not met.

## Fixture Layout

```text
tests/fixtures/real-world-public-corpus/
  manifest.yaml
  oracles/
    expected_outputs.yaml
    expected_events.yaml
    expected_replay.yaml
    thresholds.yaml
  README.md
```

The default public corpus covers static, listing/detail, pagination, and API-like public targets without credentials or browser execution.
