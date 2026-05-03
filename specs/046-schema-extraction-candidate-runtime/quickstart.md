# Quickstart: Schema Extraction Candidate Runtime

Run the record success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-schema-extraction run \
  tests/fixtures/schema-extraction-record-success \
  --profile target \
  --out .veracrawl-test-runs/schema-extraction-record-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_schema_extraction_contracts.py \
  tests/unit/test_schema_extraction_runtime.py \
  tests/integration/test_schema_extraction_fixtures.py
```
