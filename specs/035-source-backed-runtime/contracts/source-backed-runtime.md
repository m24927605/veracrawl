# Contract: Source-Backed Target Runtime

## Contracts

- `TargetSourceCorpusManifest`
- `TargetSourceCorpusEntry`
- `TargetSourceObservationRecord`

## Commands

- `record_target_source_corpus`
- `record_target_source_observation`

## Events

- `target_source_corpus_recorded`
- `target_source_observation_recorded`

## Fixture Scenarios

- `source-backed-target-success`
- `source-backed-target-policy-denied`
- `source-backed-target-prompt-injection`
- `source-backed-target-missing-evidence`
- `source-backed-target-replay-mismatch`
- `source-backed-target-partial-export`

## Runtime Rules

- Passing source-backed reports require at least seven local corpus entries and seven target pattern records.
- Accepted outputs must be derived from source content and stable content hashes.
- Prompt-injection and policy-denied entries block completion.
- Missing evidence, replay mismatch, and partial export fail completion.
- Existing 034 deterministic target runtime fixtures must remain compatible.
