# Quickstart: VeraCrawl Evidence and Publication Spine

This quickstart validates deterministic evidence and publication gates. It does
not claim graph intelligence, memory intelligence, export delivery, distributed
persistence, production browser rendering, or production scale readiness.

Run all evidence/publication fixtures:

```sh
for fixture in \
  evidence-field-coverage \
  evidence-verification-review \
  evidence-publication-success \
  evidence-missing-anchor \
  evidence-verification-conflict \
  evidence-policy-denied \
  evidence-replay-gap \
  evidence-candidate-direct-publication
do
  uv run --python python3.12 --extra dev veracrawl-evidence run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run the focused test gate:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_evidence_publication_contract_registry.py \
  tests/contract/test_evidence_publication_contracts.py \
  tests/contract/test_evidence_publication_import_boundaries.py \
  tests/unit/test_evidence_coverage.py \
  tests/unit/test_verification_review.py \
  tests/unit/test_publication_gates.py \
  tests/unit/test_publication_replay.py \
  tests/integration/test_evidence_publication_fixtures.py
```
