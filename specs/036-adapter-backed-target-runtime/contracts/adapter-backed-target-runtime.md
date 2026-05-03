# Contract: Adapter-Backed Target Runtime

## Contracts

- `TargetAdapterBackedSourceEntry`
- `TargetAdapterBackedSourceManifest`
- `TargetAdapterBackedSourceRecord`
- `TargetRuntimeFixtureManifest.adapter_backed_source_ref`
- `TargetRuntimeFixtureManifest.expected_adapter_result_count`
- `TargetRuntimeReport.adapter_backed_source_refs`
- `TargetRuntimeReport.source_adapter_result_refs`
- `TargetRuntimeReport.adapter_output_refs`

## Commands And Events

- `record_target_adapter_backed_source_manifest`
- `record_target_adapter_backed_source`
- `target_adapter_backed_source_manifest_recorded`
- `target_adapter_backed_source_recorded`

## Fixtures

- `adapter-backed-target-success`
- `adapter-backed-target-missing-adapter-result`
- `adapter-backed-target-output-mismatch`
- `adapter-backed-target-policy-denied`
- `adapter-backed-target-replay-mismatch`
- `adapter-backed-target-direct-source-bypass`

## Acceptance

- Passing adapter-backed reports require at least seven adapter-backed source records and seven source adapter result refs.
- Negative adapter-backed fixtures must fail or block with typed target runtime failures.
- Target runtime core import-boundary tests must continue to pass.
