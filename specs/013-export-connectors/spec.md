# Feature Specification: VeraCrawl Export Connectors

**Feature Branch**: `013-export-connectors`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Export Connectors Spine：ExportTargetSpec、ExportJob、ExportAttempt、ExportDeliveryReceipt、ExportWithdrawalJob、ExportWithdrawalAttempt、export dispatch/receipt/withdrawal/correction propagation、destination object mapping、idempotency、policy/review gates、replay refs、fixture/oracle 測試基礎。必須遵守 docs/07、09、10、11 與 constitution；不得實作成單一目的地匯出腳本；core 不得直接耦合任何外部 export target、storage、queue、HTTP client 或 agent framework。"

## Constitution Alignment

- **General-purpose crawler impact**: Export contracts cover file, API, database, warehouse, object store, and queue targets through typed contracts and ports. The feature does not hard-code a single destination.
- **Target/V1 boundary**: This is target architecture work from `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`, sequenced after review/replay/ops.
- **Evidence and replay impact**: Exports require immutable output refs, idempotency keys, delivery receipts, withdrawal mappings, correction records, policy refs, command refs, event cursor refs, outbox refs, and replay-visible reconciliation reports.
- **Safety and policy impact**: Export dispatch and withdrawal require policy refs. Unsupported withdrawal semantics become reviewable `destination_unsupported` outcomes instead of silent success.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define executable contracts for `ExportTargetSpec`, `ExportJob`, `ExportAttempt`, `ExportDeliveryReceipt`, `ExportWithdrawalJob`, `ExportWithdrawalAttempt`, `ExportCorrectionRecord`, `ExportReconciliationReport`, and `ExportFixtureManifest`.
- **FR-002**: System MUST define an `ExportTargetPort` protocol while keeping core independent from concrete destinations, storage clients, queue clients, HTTP clients, and agent frameworks.
- **FR-003**: System MUST register export contracts, commands, events, fixtures, and target area coverage.
- **FR-004**: System MUST provide deterministic export runtime for dispatch, receipt, withdrawal, correction propagation, idempotency, and destination mapping.
- **FR-005**: System MUST include success fixtures for file export, API export, and correction/withdrawal propagation.
- **FR-006**: System MUST include negative fixtures for missing delivery receipt, duplicate idempotency, missing withdrawal mapping, unsupported withdrawal, and correction without withdrawal.
- **FR-007**: System MUST reject pass claims when delivery receipt, destination object mapping, policy, command/event/outbox, or replay refs are missing.
- **FR-008**: System MUST expose a CLI fixture runner for export fixtures.
- **FR-009**: System MUST update docs and README with the executable export spine and non-completion boundary.

## Non-Goals

- This feature does not implement concrete destination adapters, external API calls, database writes, warehouse writes, object-store writes, queue delivery, production export worker fleets, or production credentials.
- This feature does not implement production export scale, distributed queues, distributed persistence, production browser rendering, concrete agent framework integration, or production monitoring.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
