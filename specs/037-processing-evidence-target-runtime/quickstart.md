# Quickstart: VeraCrawl Processing/Evidence Target Runtime Gate

```bash
uv run --python python3.12 --extra dev veracrawl-target-runtime run \
  tests/fixtures/processing-evidence-target-success \
  --profile target \
  --out .veracrawl-test-runs/processing-evidence-target-success
```

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_processing_evidence_target_runtime_contracts.py \
  tests/unit/test_processing_evidence_target_runtime_runner.py \
  tests/integration/test_processing_evidence_target_runtime_fixtures.py \
  tests/unit/test_target_runtime_import_boundaries.py
```
