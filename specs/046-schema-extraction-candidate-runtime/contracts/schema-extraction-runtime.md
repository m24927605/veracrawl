# Contract: Schema Extraction Candidate Runtime

## CLI Contract

```text
veracrawl-schema-extraction run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `schema-extraction-record-success` | pass |
| `schema-extraction-exploratory-success` | pass |
| `schema-extraction-browser-success` | pass |
| `schema-extraction-drift-repair-required` | needs_review |
| `schema-extraction-missing-normalization` | fail |
| `schema-extraction-schema-validation-failed` | fail |
| `schema-extraction-missing-field-anchor` | fail |
| `schema-extraction-missing-model-tool-trace` | fail |
| `schema-extraction-candidate-direct-publication` | fail |
| `schema-extraction-replay-mismatch` | fail |

## Pass Rules

A passing report requires live normalization refs, normalized document refs,
source anchors, extraction strategy refs, extraction candidate refs, candidate
field anchor refs, schema validation refs, framework-neutral model/tool trace
refs, confidence refs, policy refs, command/event/outbox refs, and replay refs.

Passing reports must not include publication, output manifest, export, or
delivery refs. Needs-review drift reports must include drift signal, rejection,
and repair recommendation refs.
