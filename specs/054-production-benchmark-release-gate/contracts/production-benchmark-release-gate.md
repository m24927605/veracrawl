# Contract: Production Benchmark Release Gate

## CLI

```text
veracrawl-release-gate run <fixture_dir> --profile target --out <output_dir>
```

Optional runtime handoff refs:

```text
--telemetry-backend-ref <ref>
--collector-handoff-ref <ref>
```

The CLI loads `manifest.yaml`, validates
`ProductionBenchmarkReleaseFixtureManifest`, runs the deterministic release
gate, compares expected completion/status/failure, then writes
`run_report.json`.

## Runtime API

```python
run_production_benchmark_release_gate(
    *,
    fixture_id: str,
    scenario: str,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> ProductionBenchmarkReleaseResult
```

The result contains one `ProductionBenchmarkReleaseReport` plus subordinate
target, source coverage, product acceptance, security/privacy, publication,
worker orchestration, and ops runtime results when those dependencies are
present.

## Commands

- `record_production_benchmark_release_report`
- `record_production_benchmark_release_fixture_manifest`

## Events

- `production_benchmark_release_reported`
- `production_benchmark_release_fixture_manifest_recorded`

## Fixture IDs

Success:

- `production-release-benchmark-success`

Negative:

- `production-release-missing-target-runtime`
- `production-release-missing-source-coverage`
- `production-release-missing-product-acceptance`
- `production-release-missing-security-privacy`
- `production-release-missing-publication`
- `production-release-missing-worker-orchestration`
- `production-release-missing-ops-runtime`
- `production-release-slo-violation`
- `production-release-blocker-present`
- `production-release-false-ready`
- `production-release-replay-mismatch`
