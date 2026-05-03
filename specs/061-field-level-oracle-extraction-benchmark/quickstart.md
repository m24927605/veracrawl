# Quickstart: Field-Level Oracle Extraction Benchmark

Run the deterministic field oracle quality fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-field-oracle-benchmark run \
  tests/fixtures/field-oracle-quality-corpus \
  --profile quality \
  --out .veracrawl-test-runs/field-oracle-quality-corpus
```

Inspect outputs:

```sh
jq . .veracrawl-test-runs/field-oracle-quality-corpus/summary.json
jq . .veracrawl-test-runs/field-oracle-quality-corpus/field_oracle_report.json
```

Expected pass characteristics:

- 8 schemas
- 200 expected fields
- 200 evaluated fields
- accepted fields have source anchors, artifacts, content hashes, evidence,
  verification, command/event/outbox, and replay refs
- no LLM output is treated as source evidence
