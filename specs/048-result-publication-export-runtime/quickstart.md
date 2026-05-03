# Quickstart: Result Publication And Export Runtime

Run a single fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-result-publication run \
  tests/fixtures/result-publication-export-success \
  --profile target \
  --out .veracrawl-test-runs/result-publication-export-success
```

Run the focused gate:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_result_publication_export_contracts.py \
  tests/unit/test_result_publication_export_runtime.py \
  tests/integration/test_result_publication_export_fixtures.py
```
