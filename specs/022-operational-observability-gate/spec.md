# Feature Specification: Operational Observability Gate

**Feature Branch**: `022-operational-observability-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Operational Observability Gate：在 operational runtime infrastructure gate 與 operational disaster recovery gate 之上，實作 backend-neutral metrics/tracing/alerting/runbook/cost/quality observability acceptance gate。必須提供 ObservabilitySignal、MetricSample、TraceSpan、AlertRecord、RunbookAction、ObservabilityReport 與 fixture/oracle 測試，驗證 policy、command/event/outbox/replay refs、ops dashboard projection watermarks、failure/recovery/DR refs、redaction、no-runtime needs_review 與 missing metrics/traces/alerts/runbook/replay negative fixtures。Core 不得直接耦合 Prometheus、OpenTelemetry、Grafana、cloud monitoring SDK、browser library、model SDK 或 agent framework；不得把 ops console data surface 假裝成 production observability pass；不得宣稱 managed cloud observability、deployment 或 worker fleet readiness。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: Observability is a platform capability for every project, site, source adapter, agent workflow, infrastructure adapter, recovery path, graph projection, memory scope, export target, and replay bundle. This feature keeps VeraCrawl general-purpose by proving operational visibility through crawler-wide contracts rather than a single site, scraper, dashboard mock, or telemetry vendor.
- **Target/V1 boundary**: This is target architecture work after the operational runtime infrastructure and disaster recovery gates. It advances the operational state requirements in `docs/09-target-capability-model.md`, the observability requirements in `docs/10-target-implementation-design.md`, and the Operations acceptance gate in `docs/11-target-testing-and-acceptance.md`. It must not claim full target completion, managed cloud observability, production deployment, or production worker fleet readiness.
- **Evidence and replay impact**: The feature affects metric sample refs, trace span refs, alert refs, runbook action refs, cost/quality refs, failure/recovery refs, DR restore refs, ops dashboard projection watermarks, policy refs, command refs, event cursor refs, outbox refs, redaction refs, and replay completeness.
- **Safety and policy impact**: Observability records can expose incident details, URLs, prompts, credential-adjacent context, artifact metadata, customer identifiers, costs, and operational topology. Reports must preserve redaction refs and must not serialize raw secrets, raw prompts, raw artifacts, DSNs, queue URLs, object-store credentials, or cloud credentials.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Operational Visibility (Priority: P1)

As a platform operator, I need one observability gate that proves metrics, traces, alerts, runbook actions, cost/quality signals, failure/recovery records, DR status, and replay refs are connected, so production incidents can be explained without reading raw stores manually.

**Why this priority**: VeraCrawl target capabilities cannot be called operational unless metrics, traces, alerts, runbooks, failures, recovery paths, and replay evidence are available together.

**Independent Test**: Run the observability success fixture. It passes only when the report contains metric samples, trace spans, alerts, runbook actions, quality/cost signals, dashboard watermarks, failure/recovery refs, DR refs, policy refs, command refs, event cursor refs, outbox refs, redaction refs, and replay completeness.

**Acceptance Scenarios**:

1. **Given** a run with complete metric, trace, alert, runbook, cost, quality, failure/recovery, DR, policy, command, event, outbox, and replay refs, **When** the observability gate evaluates the run, **Then** it emits a passing `ObservabilityReport`.
2. **Given** ops dashboard snapshots and projection watermarks from the review/replay/ops console, **When** the observability gate validates them, **Then** stale or missing projections block a pass.

---

### User Story 2 - Reject Fake Observability Completion (Priority: P2)

As a reviewer, I need no-runtime, data-surface-only, dashboard-only, and backend-missing paths to be marked needs-review or failed, so VeraCrawl cannot pretend production observability exists because an ops report or deterministic fixture exists.

**Why this priority**: The target docs explicitly distinguish a replayable ops data surface from production observability backends, alerting, and runbooks. This feature must close that gap honestly without coupling core to a vendor.

**Independent Test**: Run the no-runtime and data-surface-only fixtures. They must return `needs_review` with contract-only refs and must not claim an operational pass.

**Acceptance Scenarios**:

1. **Given** no telemetry runtime or collector handoff is configured, **When** the observability gate runs, **Then** it returns `needs_review` and records the missing metric, trace, alert, and runbook backend refs.
2. **Given** an ops console report with dashboard data but no metric samples, trace spans, alert records, or runbook actions, **When** the observability gate evaluates it, **Then** the result cannot be `pass`.

---

### User Story 3 - Surface Missing Signals And Runbook Failures (Priority: P3)

As an operator, I need missing metrics, traces, alerts, runbook actions, dashboard watermarks, DR refs, redaction refs, and replay refs to fail explicitly with failure records and recovery actions, so observability gaps are actionable and auditable.

**Why this priority**: Observability failures are operational failures. Missing signals or unsafe incident detail leakage must not silently degrade the platform or corrupt replay.

**Independent Test**: Run each negative observability fixture independently. Each fixture must fail deterministically with the expected missing ref fields, failure type, recovery action refs, policy refs, redaction status, and replay status.

**Acceptance Scenarios**:

1. **Given** a report missing trace spans or alert records, **When** the gate validates it, **Then** it fails with a typed failure record and linked recovery action.
2. **Given** an observability record that includes unredacted secret-like incident details, **When** the gate validates it, **Then** it fails and records the redaction violation.

### Edge Cases

- No telemetry runtime, collector, or exporter handoff is available.
- Ops console data exists but metric samples, trace spans, alert records, or runbook actions are missing.
- Metrics exist without trace correlation, command refs, event cursor refs, outbox refs, or replay refs.
- Trace spans exist but contain raw prompt text, raw secret-like values, DSNs, queue URLs, object-store credentials, or cloud credentials.
- Alerts exist but do not map to failure records, DR status, severity, policy refs, or runbook actions.
- Runbook actions exist without approval refs for side-effecting recovery steps.
- Dashboard projection watermarks are stale or absent.
- Cost/quality signals are missing, stale, or disconnected from the run and replay bundle.
- DR refs are missing for recovery-related alerts.
- Redaction map refs are missing even though sensitive fields were present.
- A vendor-specific telemetry adapter reports success but the core observability gate cannot validate canonical VeraCrawl refs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `ObservabilitySignal`, `MetricSample`, `TraceSpan`, `AlertRecord`, `RunbookAction`, `ObservabilityReport`, and observability fixture manifest coverage for the operational observability gate.
- **FR-002**: System MUST require metrics, traces, alerts, runbook actions, cost/quality signals, failure/recovery refs, DR restore refs, dashboard projection watermarks, policy refs, command refs, event cursor refs, outbox refs, redaction refs, and replay refs before any observability report can claim `pass`.
- **FR-003**: System MUST reject ops-console-only, dashboard-only, deterministic fixture-only, data-surface-only, or vendor-native-only signals as operational observability pass evidence.
- **FR-004**: System MUST return `needs_review` with contract-only refs when telemetry runtime, collector handoff, or backend refs are unavailable.
- **FR-005**: System MUST fail observability reports that are missing metric samples, trace spans, alert records, runbook actions, dashboard watermarks, failure/recovery refs, DR refs, policy refs, command refs, event cursor refs, outbox refs, redaction refs, or replay refs.
- **FR-006**: System MUST fail observability reports that contain unredacted raw secrets, DSNs, queue URLs, object-store credentials, cloud credentials, raw prompts, raw artifacts, or incident details requiring redaction.
- **FR-007**: System MUST emit failure and recovery action refs for observability validation failures, including missing signals, stale dashboard watermarks, missing replay refs, and unsafe runbook actions without approval.
- **FR-008**: System MUST keep core observability contracts and validation independent of Prometheus, OpenTelemetry, Grafana, cloud monitoring SDKs, browser libraries, model SDKs, and agent frameworks.
- **FR-009**: System MUST expose a repeatable operator-facing observability fixture runner that writes deterministic reports and redacts sensitive runtime details.
- **FR-010**: System MUST register observability gate contracts, commands, events, fixture oracles, and target area in the canonical registry.
- **FR-011**: System MUST update target docs and README with the operational observability gate, its fixtures, backend-neutral rules, no-runtime behavior, and non-completion boundary.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, telemetry backends, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when observability signals refer to outputs, reviews, exports, or recovery.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when observability records include protected context or recovery actions.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **ObservabilitySignal**: A canonical platform signal that links operational measurements, events, owners, severity, source capability, redaction refs, and replay refs.
- **MetricSample**: A measurement record for queue lag, retry rate, projection lag, browser minutes, token spend, object-store growth, export lag, error rate, DR duration, or quality/cost SLOs.
- **TraceSpan**: A canonical span for command, event, adapter, agent, tool, queue, artifact, projection, export, or recovery execution, with parent/child relationships and redacted attributes.
- **AlertRecord**: A policy-visible operational alert tied to metrics, traces, failures, severity, blast radius, DR refs, and runbook actions.
- **RunbookAction**: A replayable operator or automated action recommendation/execution record with approval refs for side-effecting recovery.
- **ObservabilityReport**: The gate result tying signals, metrics, traces, alerts, runbooks, dashboard watermarks, cost/quality refs, failure/recovery refs, DR refs, policy, command, event, outbox, redaction, and replay refs into one pass/fail/needs-review record.
- **ObservabilityFixtureManifest**: The fixture-level description of success, no-runtime, data-surface-only, and negative observability scenarios and their oracle refs.

### Non-Goals *(mandatory)*

- This feature does not implement managed Prometheus, OpenTelemetry collector deployment, Grafana dashboards, cloud monitoring accounts, paging integrations, on-call automation, deployment automation, production worker fleets, or managed cloud observability operations.
- This feature does not implement production browser rendering, model SDK integration, concrete agent framework integration, CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
- This feature does not claim full target architecture completion. It proves the backend-neutral operational observability gate only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The observability success fixture produces `pass` only when all required metric, trace, alert, runbook, dashboard, cost/quality, failure/recovery, DR, policy, command, event, outbox, redaction, and replay refs are present.
- **SC-002**: The no-runtime fixture produces `needs_review` and never produces an operational observability pass.
- **SC-003**: Negative fixtures for missing metrics, missing traces, missing alerts, missing runbook actions, stale dashboard watermarks, missing DR refs, missing redaction refs, missing replay refs, and unsafe runbook without approval all produce deterministic `fail` results.
- **SC-004**: Contract registry validation succeeds with the new observability contracts, commands, events, fixture oracles, and target area registered.
- **SC-005**: Import-boundary tests prove core observability packages do not import Prometheus, OpenTelemetry, Grafana, cloud monitoring SDKs, browser libraries, model SDKs, agent frameworks, infrastructure SDKs, or site-specific scraper modules.
- **SC-006**: Full relevant quality gates pass, including formatting/linting, typing, contract tests, unit tests, integration fixtures, no-runtime CLI tests, and full pytest.

## Assumptions

- The review/replay/ops console, operational runtime infrastructure gate, and operational disaster recovery gate exist and provide canonical ops, runtime, and DR refs for this feature.
- Observability may use deterministic fixture data to validate canonical contracts; fixture-only signals cannot be labeled operational pass unless they include the required backend/collector handoff refs.
- Backend-neutral means VeraCrawl core validates canonical observability contracts and handoff refs; concrete telemetry vendors remain adapter-owned future work unless separately implemented and tested.
- The operator-facing runner is CLI-first for this slice; a production dashboard frontend and managed alert delivery remain out of scope.
