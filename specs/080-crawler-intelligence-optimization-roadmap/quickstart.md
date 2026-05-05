# Quickstart: Crawler Intelligence Optimization Roadmap

This roadmap is now implemented as a deterministic optimization gate for specs
081-086. The gate validates crawler intelligence algorithms without narrowing
VeraCrawl into a single-site scraper or bypassing policy/replay requirements.

## Validate The Roadmap

1. Confirm spec directories exist:

```bash
test -f specs/080-crawler-intelligence-optimization-roadmap/spec.md
test -f specs/081-focused-frontier-scoring/spec.md
test -f specs/082-dom-page-understanding/spec.md
test -f specs/083-extractor-fallback-confidence/spec.md
test -f specs/084-canonical-dedupe-identity/spec.md
test -f specs/085-recommendation-ranking-runtime/spec.md
test -f specs/086-cost-recovery-evaluation-gates/spec.md
```

2. Confirm roadmap docs reference the optimization set:

```bash
rg -n "080|081|082|083|084|085|086" docs/08-build-roadmap.md specs/038-production-runtime-closure/spec.md specs/068-production-grade-crawler-closure-roadmap/spec.md AGENTS.md
```

3. Confirm no spec claims these are new production-grade closure gates:

```bash
rg -n "post-closure optimization|not additional production-grade closure" specs/080-crawler-intelligence-optimization-roadmap/spec.md specs/068-production-grade-crawler-closure-roadmap/spec.md
```

## Activation Flow For A Lower Spec

Specs 081-086 are currently implemented through the shared optimization gate.
When extending one of them:

1. Preserve the reserved spec number and directory.
2. Run Spec Kit clarify if ambiguity remains.
3. Generate plan, research, data-model, contracts, quickstart, and tasks.
4. Implement only that spec's bounded scope.
5. Record real validation in `tasks.md`.
6. Run cross-artifact analysis before implementation completion where available.

## Run The Implemented Gate

```bash
uv run --extra dev veracrawl-crawler-optimization run \
  tests/fixtures/crawler-optimization-success \
  --out /tmp/veracrawl-crawler-optimization-success
```

## Run Validation

```bash
uv run --extra dev pytest \
  tests/contract/test_crawler_optimization_contracts.py \
  tests/contract/test_crawler_optimization_contract_registry.py \
  tests/contract/test_crawler_optimization_import_boundaries.py \
  tests/unit/test_crawler_optimization_runtime.py \
  tests/unit/test_crawler_optimization_replay.py \
  tests/integration/test_crawler_optimization_fixtures.py
```
