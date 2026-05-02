# Contract: Advanced Graph Projection Build

## Command

`build_advanced_graph_projection`

## Inputs

- basic graph manifest refs
- graph node refs
- graph edge refs
- source output refs
- evidence packet refs
- policy decision refs

## Outputs

- `ProjectionSpec`
- `ProjectionRebuildJob`
- `ProjectionWatermark`
- `GraphDeltaReport`
- `GraphQualityReport`
- `GraphSignal`
- `TemporalGraphProjectionRecord`
- `AdvancedGraphProjectionReport`

## Failure Outputs

- `ProjectionMismatchReport` for rebuild hash mismatch
- typed failure refs for missing watermark or graph-signal-as-evidence attempts

## Invariants

- Rebuild success requires expected hash equals actual hash.
- Rebuild pass requires projection watermark, event cursor refs, command refs, outbox refs, and policy refs.
- Projection output remains derived state and cannot replace source evidence.
