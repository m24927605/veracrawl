# Contract: Field-Level Oracle Extraction Benchmark

## CLI

```sh
uv run --python python3.12 --extra dev veracrawl-field-oracle-benchmark run \
  tests/fixtures/field-oracle-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/field-oracle-quality-corpus
```

## Outputs

- `field_oracle_report.json`
- `field_evaluations.json`
- `expected_fields.json`
- `schemas.json`
- `summary.json`

## Pass Contract

A passing quality fixture must:

- evaluate at least 8 schemas and 200 expected fields
- record field-level exact/normalized/partial/rejected classes
- attach source anchors, artifact refs, content hashes, normalized value refs,
  evidence packet refs, verification decision refs, policy refs,
  command/event/outbox refs, and replay refs to every accepted field
- keep model/agent/tool/context refs as proposal traces only
- emit JSON suitable for row 062 precision/recall computation

## Failure Contract

Negative fixtures must fail with typed `FieldOracleFailureType` diagnostics for
wrong value, missing anchor, schema violation, stale evidence, publication
bypass, and LLM-as-evidence.
