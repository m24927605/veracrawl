# Quickstart: Target Website Pattern Coverage Gate

```bash
for fixture in \
  website-pattern-coverage-success \
  website-pattern-runtime-unavailable \
  website-pattern-missing-pattern \
  website-pattern-unsupported-pattern \
  website-pattern-single-site-assumption \
  website-pattern-scaffold-only \
  website-pattern-missing-source-adapter \
  website-pattern-missing-site-model \
  website-pattern-missing-output-evidence \
  website-pattern-missing-pattern-specific-refs \
  website-pattern-unsafe-interaction \
  website-pattern-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-website-patterns run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_website_pattern_coverage_contracts.py \
  tests/contract/test_website_pattern_coverage_contract_registry.py \
  tests/contract/test_website_pattern_coverage_import_boundaries.py \
  tests/unit/test_website_pattern_coverage_gate.py \
  tests/integration/test_website_pattern_coverage_fixtures.py
```
