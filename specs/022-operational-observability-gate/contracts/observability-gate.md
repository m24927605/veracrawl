# Contract: Operational Observability Gate

## CLI

```text
veracrawl-observability run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

Backend-neutral handoff args:

- `--telemetry-backend-ref` or `VERACRAWL_TELEMETRY_BACKEND_REF`
- `--collector-handoff-ref` or `VERACRAWL_COLLECTOR_HANDOFF_REF`

The CLI must not accept or persist raw telemetry credentials in this slice.

## Pass Contract

A passing observability report must include:

- observability signal refs
- metric sample refs
- trace span refs
- alert record refs
- runbook action refs
- quality report refs and cost metric refs
- dashboard snapshot refs and projection watermark refs
- failure and recovery action refs
- DR restore report refs for recovery-related visibility
- policy, command, event cursor, and outbox refs
- redaction map refs
- collector handoff refs and telemetry backend refs
- replay bundle refs
- no missing required refs
- no unredacted sensitive fields
- no unsafe side-effecting runbook action without approval

## No-Runtime Contract

`observability-runtime-unavailable` returns `needs_review` and must include contract-only refs for missing telemetry runtime, collector handoff, or backend refs. It cannot claim operational observability pass.

## Data-Surface-Only Contract

`observability-data-surface-only` returns `needs_review` because an ops console report, quality report, or dashboard snapshot without metric samples, trace spans, alert records, runbook actions, backend refs, and collector refs is not operational observability.

## Negative Contract

Negative fixtures must fail deterministically:

- missing metrics
- missing traces
- missing alerts
- missing runbook actions
- stale dashboard projection watermarks
- missing DR refs
- missing redaction refs
- missing replay refs
- secret-like payload leakage
- unsafe runbook action without approval refs

## Boundary Contract

Core observability code must not statically import concrete telemetry packages or SDKs, including Prometheus, OpenTelemetry, Grafana, cloud monitoring SDKs, paging SDKs, browser libraries, model SDKs, agent frameworks, concrete infrastructure SDKs, or site-specific scraper modules.
