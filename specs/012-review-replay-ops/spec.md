# Feature Specification: VeraCrawl Review Replay Ops Console

**Feature Branch**: `012-review-replay-ops`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "Implement the next target architecture slice after multi-agent repair: review queue, replay audit view, operational failure/recovery records, quality dashboard data, and deterministic fixture/oracle tests. The slice must remain a general-purpose AI agent crawler foundation, must not become a single-site scraper, must keep VeraCrawl core framework-neutral, and must not claim production UI, production monitoring, export delivery, or production scale readiness."

## Constitution Alignment

- **General-purpose crawler impact**: The feature adds review, replay, and operations contracts that work across crawl objectives, websites, schemas, source adapters, graph/memory/agent signals, and failure types. It does not encode any website-specific scraper logic.
- **Target/V1 boundary**: This is target architecture work from `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`. It is an executable foundation slice for target review/replay/ops surfaces, not a full production console.
- **Evidence and replay impact**: The feature materializes review items, replay audit views, failure records, recovery actions, DR restore reports, quality reports, dashboard snapshots, ops console reports, commands, events, fixtures, and replay validators.
- **Safety and policy impact**: Recovery actions that mutate state require policy and review/approval refs. Missing evidence, unresolved failures, stale projections, and unsafe recovery attempts must produce fail/needs-review records instead of hidden success.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define executable contracts for `ReviewItem`, `ReplayAuditView`, `FailureRecord`, `RecoveryAction`, `DRRestoreReport`, `QualityReport`, `OpsDashboardSnapshot`, `OpsConsoleReport`, and `OpsFixtureManifest`.
- **FR-002**: System MUST register ops/review/replay contracts, command types, event types, fixture oracles, and target contract area coverage in the executable registry.
- **FR-003**: System MUST provide a deterministic ops console runtime that emits review queue data, replay audit data, quality dashboard data, failure records, recovery actions, DR restore status, policy refs, command refs, event cursor refs, and outbox refs.
- **FR-004**: System MUST provide deterministic success fixtures for review console, replay audit, and quality dashboard slices.
- **FR-005**: System MUST provide negative fixtures for missing review evidence, unresolved failure without recovery, stale dashboard projection, and unsafe recovery without review/approval.
- **FR-006**: System MUST reject passing ops console reports when replay-critical refs are missing.
- **FR-007**: System MUST reject destructive or side-effecting recovery actions without policy and approval refs.
- **FR-008**: System MUST expose a CLI fixture runner for ops/review/replay fixtures.
- **FR-009**: System MUST keep core independent of concrete agent frameworks, model SDKs, browsers, storage clients, queue clients, graph stores, memory stores, export targets, and HTTP clients.
- **FR-010**: System MUST update README and target docs to describe the executable ops console spine and non-completion boundary.

## Non-Goals

- This feature does not implement a production web UI, dashboard frontend, alerting backend, metrics store, distributed tracing backend, production monitoring system, or on-call runbook automation.
- This feature does not implement export delivery, production browser rendering, distributed persistence, distributed queues, concrete storage adapters, concrete agent framework integration, or production scale operations.
- This feature does not implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
