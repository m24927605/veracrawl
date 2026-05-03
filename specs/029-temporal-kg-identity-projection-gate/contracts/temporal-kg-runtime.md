# Contract: Temporal KG Runtime

The temporal KG runtime gate must materialize only canonical, replayable, evidence-derived graph projection state.

## Required Pass Outputs

- `TemporalKGEntityIdentity`
- `TemporalKGProjectionRecord`
- `TemporalKGRuntimeReport`
- `CommandResult`
- `EventCursorRecord`
- `OutboxRecord`
- `ReplayBundleManifest`

False-merge and false-split scenarios also require:

- `TemporalKGIdentityAdjudicationRecord`
- conflict refs
- invalidation or supersession refs

## Evidence Boundary

Temporal KG refs are forbidden as source evidence. A pass report must include evidence packet refs and canonical source refs, but those refs must point to source-backed evidence and verified/published events, not graph-derived records.

## Runtime Availability

When live temporal KG runtime refs are absent, the fixture returns `needs_review` with contract-only refs and missing runtime refs. It must not claim operational pass.

## Failure Types

- `temporal_kg_missing_runtime_refs`
- `temporal_kg_provisional_identity`
- `temporal_kg_projection_as_evidence`
- `temporal_kg_missing_identity_evidence`
- `temporal_kg_missing_canonical_sources`
- `temporal_kg_missing_bitemporal_refs`
- `temporal_kg_false_merge_without_adjudication`
- `temporal_kg_false_split_without_supersession`
- `temporal_kg_missing_replay_refs`
