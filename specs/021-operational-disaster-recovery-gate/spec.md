# Feature Specification: Operational Disaster Recovery Gate

**Feature Branch**: `021-operational-disaster-recovery-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Operational Disaster Recovery Gate：在 operational runtime infrastructure gate 之上，實作 DRRestorePlan、DRRestoreRun、DRRestoreReport 的可執行復原工作流與驗收 gate，必須透過 adapter/ports 讀寫 live Postgres metadata/event/outbox refs、Redis queue recovery refs、S3-compatible artifact refs，驗證 ordered restore phases、restore point、backup manifest、metadata restore、artifact reachability、event replay、projection rebuild、export reconciliation、unresolved refs、failure/recovery action、policy refs 與 replay completeness。Core 不得直接耦合 psycopg、redis、boto3/botocore、cloud SDK、browser library、model SDK 或 agent framework；不得把 deterministic fixture 或單一 adapter conformance 假裝成 operational DR pass；不得宣稱 managed cloud backup、deployment、production observability 或 production worker fleet readiness。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: Disaster recovery is a target platform capability for every project, site, source adapter, queue family, artifact family, graph projection, memory index, export state, and replay bundle. This feature preserves VeraCrawl as a general-purpose AI agent crawler by proving the operational recovery substrate is not tied to one website, schema, scraper, or destination.
- **Target/V1 boundary**: This is target architecture work after the operational runtime infrastructure gate. It must not reduce scope for schedule reasons, and it must not claim full target completion. It specifically advances the Scale and Reliability Profile and Operations acceptance gates in `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: The feature affects restore-point refs, backup manifests, metadata/event/outbox refs, artifact reachability refs, replay validation refs, projection rebuild refs, export reconciliation refs, failure records, recovery actions, policy refs, command refs, event cursors, and replay completeness.
- **Safety and policy impact**: Recovery actions that can change external state, restore deleted/tombstoned data, replay events, rebuild projections, reconcile exports, or expose incident details require policy refs and, when side-effecting, approval/review refs. Secrets, DSNs, queue URLs, object-store credentials, artifact content, and incident details must be redacted from reports.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Operational DR Pass (Priority: P1)

As a platform operator, I need one recovery gate that proves a restore plan can execute ordered restore phases across the live operational infrastructure substrate, so a VeraCrawl run can be restored, replayed, validated, and reported without hidden manual assumptions.

**Why this priority**: A production-grade crawler cannot claim operational reliability unless metadata, events, queues, artifacts, projections, exports, policies, and replay can be restored and validated together.

**Independent Test**: Run the operational DR success fixture with live Postgres, Redis/Valkey, and S3-compatible runtimes. The fixture passes only when the DR report contains restore-point, backup manifest, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, policy, command, event cursor, outbox, queue recovery, failure/recovery, and replay refs.

**Acceptance Scenarios**:

1. **Given** a valid restore plan with ordered phases and live operational infrastructure refs, **When** the DR gate runs, **Then** it emits a passing DR restore report with no unresolved refs and no data loss.
2. **Given** a valid restore run that replays restored events, **When** projection rebuild and export reconciliation refs are validated, **Then** the report remains replay-complete and operator-visible.

---

### User Story 2 - Reject Fake Operational DR Completion (Priority: P2)

As a reviewer, I need no-runtime, contract-only, deterministic fixture-only, and single-adapter paths to be labeled needs-review or failed, so VeraCrawl cannot pretend operational DR is complete without a live integrated substrate.

**Why this priority**: The user explicitly requires that VeraCrawl not weaken the target architecture or fake completion. DR must be proven with the integrated infrastructure, not with a mock, note, or isolated adapter conformance report.

**Independent Test**: Run the no-runtime and contract-only DR fixtures without live infrastructure. They must return `needs_review` with contract-only refs and must not claim an operational pass.

**Acceptance Scenarios**:

1. **Given** no live Postgres, Redis/Valkey, or S3-compatible runtime is provided, **When** the DR gate runs, **Then** it returns `needs_review` and records which operational refs are absent.
2. **Given** only one adapter conformance report is available, **When** the DR gate evaluates the restore, **Then** it rejects the pass claim because the integrated restore refs are incomplete.

---

### User Story 3 - Surface DR Failures And Recovery Actions (Priority: P3)

As an operator, I need missing metadata, artifact, event replay, projection, export reconciliation, unresolved-ref, and unsafe recovery cases to fail explicitly with failure and recovery records, so incidents are recoverable and reviewable rather than silent.

**Why this priority**: Recovery systems are only useful when failure modes are typed, replayable, and actionable. Silent data loss or unresolved refs would break the evidence and replay guarantees required for target architecture.

**Independent Test**: Run each negative DR fixture independently. Each fixture must fail deterministically with the expected missing ref fields, failure type, recovery action refs, policy refs, and replay status.

**Acceptance Scenarios**:

1. **Given** a restore report missing artifact reachability or event replay refs, **When** the DR gate validates it, **Then** the result is `fail`, a failure record is emitted, and a recovery action is linked.
2. **Given** a side-effecting recovery action without approval or policy refs, **When** the gate evaluates the action, **Then** the action is rejected and the report cannot pass.

### Edge Cases

- No live runtime is available for one or more required infrastructure families.
- Restore phases are out of order, skipped without plan permission, or missing validation gates.
- Backup manifest, restore point, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, queue recovery, command, event cursor, outbox, policy, or replay refs are missing.
- Artifact reachability passes but event replay or projection rebuild fails.
- Export reconciliation is unsupported or incomplete for restored outputs.
- Unresolved refs exist even though other validation gates pass.
- Data loss is detected during restore validation.
- Recovery action is destructive, externally side-effecting, or unsafe without approval/review refs.
- Adapter-specific credentials or incident details appear in persisted reports.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `DRRestorePlan`, `DRRestoreRun`, `DRRestoreReport`, and DR fixture manifest coverage for the operational disaster recovery gate.
- **FR-002**: System MUST require ordered restore phases for metadata restore, artifact restore/reachability, event replay, projection rebuild, export reconciliation, reference validation, and report publication.
- **FR-003**: System MUST require live integrated Postgres metadata/event/outbox refs, Redis/Valkey queue recovery refs, and S3-compatible artifact refs before any operational DR report can claim `pass`.
- **FR-004**: System MUST reject deterministic fixture-only, contract-only, or single-adapter conformance results as operational DR pass evidence.
- **FR-005**: System MUST return `needs_review` with contract-only refs when live operational infrastructure is not provided.
- **FR-006**: System MUST fail restore reports that are missing restore point, backup manifest, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, policy, command, event cursor, outbox, queue recovery, or replay refs.
- **FR-007**: System MUST fail restore reports with unresolved refs or detected data loss.
- **FR-008**: System MUST emit failure and recovery action refs for failed restore validation, including unsafe recovery without approval.
- **FR-009**: System MUST keep core and DR validation logic independent of concrete database drivers, queue clients, object-store clients, cloud SDKs, browser libraries, model SDKs, and agent frameworks.
- **FR-010**: System MUST expose a repeatable operator-facing DR fixture runner that writes deterministic reports and redacts DSNs, queue URLs, object-store credentials, artifact content, and incident details.
- **FR-011**: System MUST register the DR gate contracts, commands, events, fixture oracles, and target area in the canonical registry.
- **FR-012**: System MUST update target docs and README with the operational DR gate, its fixtures, live gate requirements, and non-completion boundary.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when restored outputs or export reconciliation are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when restore or recovery touches protected artifacts or destinations.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **DRRestorePlan**: The approved recovery plan, restore scope, restore point, backup manifest, ordered phase graph, validation gates, rollback behavior, and approval refs.
- **DRRestoreRun**: The execution record for a restore plan, including phase results, current phase, emitted events, failures, and final status.
- **DRRestoreReport**: The validation report tying metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, unresolved refs, data loss, policy refs, and replay refs to a pass/fail/needs-review result.
- **DRFixtureManifest**: The fixture-level description of success, no-runtime, and negative DR scenarios and their oracle refs.
- **FailureRecord**: The typed operational failure produced when restore validation fails.
- **RecoveryAction**: The policy/review/approval-gated recovery action linked to a failed restore phase or unsafe recovery path.

### Non-Goals *(mandatory)*

- This feature does not implement managed cloud backup services, cloud IAM provisioning, cross-region replication, deployment automation, production worker fleets, production observability backends, alerting backends, or managed on-call runbooks.
- This feature does not implement production browser rendering, model SDK integration, concrete agent framework integration, CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
- This feature does not claim full target architecture completion. It proves the operational DR gate only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The operational DR success fixture produces `pass` only when all required live infrastructure, restore, policy, command, event, queue, artifact, projection, export, failure/recovery, and replay refs are present.
- **SC-002**: The no-runtime fixture produces `needs_review` and never produces an operational pass.
- **SC-003**: Negative fixtures for missing metadata restore, missing artifact reachability, missing event replay, missing projection rebuild, missing export reconciliation, unresolved refs, data loss, and unsafe recovery without approval all produce deterministic `fail` results.
- **SC-004**: Contract registry validation succeeds with the new DR contracts, commands, events, fixture oracles, and target area registered.
- **SC-005**: Import-boundary tests prove core DR packages do not import concrete infrastructure SDKs, browser libraries, model SDKs, agent frameworks, or site-specific scraper modules.
- **SC-006**: Full relevant quality gates pass, including formatting/linting, typing, contract tests, unit tests, integration fixtures, and live Docker-backed operational DR gate tests.

## Assumptions

- The operational Postgres, Redis/Valkey, and S3-compatible adapter gates from specs 017, 018, 019, and 020 are available as the live substrate for this feature.
- DR restore validation may use deterministic fixture data seeded into live local runtimes during tests; that fixture data cannot be labeled operational pass unless it flows through the live adapter-backed gate.
- Projection rebuild and export reconciliation are validated by canonical refs and replay reports in this slice; concrete production graph stores, warehouses, APIs, cloud backup systems, and alerting systems remain separate target gates.
- The operator-facing runner is CLI-first for this slice; a production dashboard frontend remains out of scope.
