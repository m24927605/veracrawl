# Research: Operational Observability Gate

## Decision: Observability Gate Validates Canonical Signals, Not Vendor State

Define `ObservabilitySignal`, `MetricSample`, `TraceSpan`, `AlertRecord`, `RunbookAction`, and `ObservabilityReport` as VeraCrawl-owned contracts. The gate validates those canonical refs plus collector/backend handoff refs rather than accepting Prometheus, OpenTelemetry, Grafana, cloud monitoring, or paging-native state as source of truth.

**Rationale**: The constitution requires framework and SDK neutrality. Observability must be replaceable across telemetry vendors while preserving replayable VeraCrawl semantics.

**Alternatives considered**:

- Implement directly against OpenTelemetry SDK types. Rejected because it couples core validation to a telemetry framework.
- Treat Grafana/dashboard presence as proof. Rejected because dashboards are presentation, not replay-complete canonical evidence.

## Decision: Ops Console Data Surface Is An Input, Not A Pass

Use existing `OpsConsoleReport`, `QualityReport`, `OpsDashboardSnapshot`, `FailureRecord`, `RecoveryAction`, and `DRRestoreReport` refs as observability inputs. Passing observability still requires canonical metric samples, trace spans, alerts, runbook actions, redaction refs, collector/backend handoff refs, and replay refs.

**Rationale**: `docs/10-target-implementation-design.md` explicitly says the ops console slice does not implement production observability storage, alerting, or runbooks. This gate must not relabel that slice as complete.

**Alternatives considered**:

- Make `OpsConsoleReport` pass observability automatically. Rejected because it would fake target completion.
- Ignore ops console refs. Rejected because target operations acceptance requires dashboard watermarks and operator visibility.

## Decision: No-Runtime Is Needs-Review, Missing Required Canonical Refs Are Fail

When no telemetry runtime, collector handoff, or backend refs are configured, return `needs_review` with contract-only refs. When a report claims pass but lacks required metrics, traces, alerts, runbooks, DR refs, redaction refs, replay refs, or safe runbook approvals, return `fail`.

**Rationale**: This matches prior operational gates: missing live backend capability blocks an operational pass without calling the contract path broken. Deterministic missing required refs are acceptance failures.

**Alternatives considered**:

- Fail no-runtime. Rejected because no-runtime is a valid review state for adapter/runtime absence.
- Mark all gaps needs-review. Rejected because negative fixtures must fail deterministically.

## Decision: Redaction Is A First-Class Gate

Reject observability records that contain raw secret-like values, DSNs, queue URLs, object-store credentials, cloud credentials, raw prompts, raw artifacts, or unredacted incident details.

**Rationale**: Observability often exposes the most sensitive operational context. Target security and privacy requirements require raw secrets and prompts to stay out of logs, replay bundles, and operational reports.

**Alternatives considered**:

- Rely on future telemetry backend redaction. Rejected because canonical contracts must be safe before export.
- Store redaction warnings while allowing pass. Rejected because secret leakage is a blocking security failure.

## Decision: CLI-First Fixture Runner For This Slice

Expose `veracrawl-observability run` for deterministic success, no-runtime, data-surface-only, and negative fixtures.

**Rationale**: Current target slices are CLI-first and write deterministic report artifacts. A production dashboard frontend, collector deployment, paging integration, and on-call automation are separate target gates.

**Alternatives considered**:

- Add a web UI or managed alert delivery. Rejected because those are explicitly non-goals for this slice.
