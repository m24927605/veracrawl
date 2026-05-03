# Quickstart: Live Evidence And Verification Runtime

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-live-evidence run \
  tests/fixtures/live-evidence-verification-success \
  --profile target \
  --out .veracrawl-test-runs/live-evidence-verification-success
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_live_evidence_verification_contracts.py \
  tests/unit/test_live_evidence_verification_runtime.py \
  tests/integration/test_live_evidence_verification_fixtures.py
```
