# Quickstart: Operational Observability Gate

Run no-runtime and negative fixtures:

```sh
for fixture in \
  observability-runtime-unavailable \
  observability-data-surface-only \
  observability-missing-metrics \
  observability-missing-traces \
  observability-missing-alerts \
  observability-missing-runbook \
  observability-stale-dashboard-watermark \
  observability-missing-dr-refs \
  observability-missing-redaction \
  observability-missing-replay \
  observability-secret-leak \
  observability-unsafe-runbook-without-approval
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-observability run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run the backend-neutral success fixture:

```sh
uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-observability run \
  tests/fixtures/observability-success \
  --profile target \
  --telemetry-backend-ref "$VERACRAWL_TELEMETRY_BACKEND_REF" \
  --collector-handoff-ref "$VERACRAWL_COLLECTOR_HANDOFF_REF" \
  --out .veracrawl-test-runs/observability-success
```

Run focused tests:

```sh
uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest \
  tests/contract/test_operational_observability_contracts.py \
  tests/contract/test_operational_observability_contract_registry.py \
  tests/contract/test_operational_observability_import_boundaries.py \
  tests/unit/test_operational_observability_gate.py \
  tests/integration/test_operational_observability_fixtures.py
```
