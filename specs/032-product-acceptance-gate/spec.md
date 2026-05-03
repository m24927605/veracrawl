# Feature Specification: VeraCrawl Target Product Acceptance Gate

**Feature Branch**: `032-product-acceptance-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Target Product Acceptance Gate：實作 docs/11 Target Product Acceptance Gates 的 executable buyer-value workflow readiness gate，必須覆蓋 multi-site onboarding、objective-to-plan approval、dynamic/auth/document/API crawl、evidence review、conflict resolution、drift repair、memory reuse、export and withdrawal、replay and audit、operator recovery，以及 minimum product gates。必須證明每個 workflow 都有 evidence、replay、operator-visible result、policy、command/event/outbox refs，且 planned、scaffolded、failed、degraded capability 不得被標示 complete/verified/operational。必須遵守 docs/07、09、10、11 與 constitution，不得以單站 scraper、mock UI、scaffold manifest、或 technical contract-only gate 假裝 product readiness。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature proves target product readiness across the full buyer-value workflow set instead of allowing one technical slice, one website, one fixture, or one UI mock to stand in for the general-purpose AI agent crawler.
- **Target/V1 boundary**: This is target architecture acceptance work for `docs/11-target-testing-and-acceptance.md#target-product-acceptance-gates` and `docs/09-target-capability-model.md#completion-states`. It is not a schedule-reduced V1 shortcut.
- **Evidence and replay impact**: Every product workflow readiness record must include evidence, replay, operator-visible result, policy, command, event cursor, outbox, artifact, and acceptance oracle refs before pass.
- **Safety and policy impact**: Dynamic/auth/document/API crawl, export/withdrawal, memory reuse, drift repair, and operator recovery require explicit safety, credential, privacy lifecycle, policy, review, and recovery refs. Unsafe, scaffold-only, failed, degraded, or contract-only claims fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove Buyer-Value Workflows (Priority: P1)

As a product owner, I need a single deterministic gate proving every target product workflow has the evidence, replay, operator visibility, policy, and acceptance refs needed to claim product readiness.

**Why this priority**: Technical contract coverage is not enough; target readiness must prove the workflows buyers actually care about.

**Independent Test**: Run `veracrawl-product-acceptance run tests/fixtures/product-acceptance-success --profile target --out .veracrawl-test-runs/product-acceptance-success`; it emits readiness records for all 10 target product workflows and a pass report.

**Acceptance Scenarios**:

1. **Given** all target product workflows have evidence, replay, operator-visible result, policy, command/event/outbox, artifact, acceptance oracle, and minimum gate refs, **When** the product acceptance gate runs, **Then** it emits one readiness record per workflow and a pass report.
2. **Given** any target workflow is omitted, **When** the gate evaluates product readiness, **Then** it fails with typed missing-workflow diagnostics.

---

### User Story 2 - Enforce Minimum Product Gates (Priority: P2)

As an operator, I need target product readiness to require approved plans, review paths, drift repair, recovery actions, export reconciliation, status accuracy, and buyer-value workflow pass refs.

**Why this priority**: A product can appear technically complete while still lacking the operating paths that make a general-purpose crawler usable and trustworthy.

**Independent Test**: Negative fixtures for missing minimum gates, missing operator visibility, missing export reconciliation, and missing replay fail deterministically.

**Acceptance Scenarios**:

1. **Given** a workflow has contracts and tests but no operator-visible result ref, **When** the gate runs, **Then** it fails as not product-ready.
2. **Given** export/withdrawal lacks receipt, correction/withdrawal, destination mapping, or reconciliation refs, **When** the gate runs, **Then** product acceptance fails.
3. **Given** drift repair lacks reviewed update or verified recovery refs, **When** the gate runs, **Then** product acceptance fails.

---

### User Story 3 - Reject Deceptive Readiness Claims (Priority: P3)

As a Staff reviewer, I need planned, scaffolded, failed, degraded, mock-only, and contract-only claims to be blocked from `complete`, `verified`, or `operational` labels.

**Why this priority**: The constitution forbids pretending target architecture is complete when a capability is only planned, scaffolded, or partially validated.

**Independent Test**: Negative fixtures for false-complete status, scaffold-only product readiness, contract-only readiness, and degraded capability labeling fail deterministically.

**Acceptance Scenarios**:

1. **Given** a product workflow is marked `verified` but has missing acceptance refs, **When** the gate runs, **Then** it fails with false-complete diagnostics.
2. **Given** a product acceptance manifest references mock UI screenshots or contract-only technical reports without workflow evidence, **When** the gate runs, **Then** it fails as scaffold-only or contract-only.
3. **Given** a degraded workflow is labeled operational, **When** the gate runs, **Then** it fails and reports the offending capability claim refs.

### Edge Cases

- Live runtime refs are unavailable; report must return `needs_review`, not pass.
- One or more target product workflows are omitted.
- A workflow has evidence refs but no replay, operator-visible result, policy, or command/event/outbox refs.
- Minimum gate refs are present for some workflows but not the aggregate buyer-value pass.
- A capability claim uses `complete`, `verified`, or `operational` while its state is planned, designed, scaffolded, failed, degraded, or contract-only.
- Export/withdrawal, drift repair, memory reuse, dynamic/auth crawl, and recovery workflows lack their workflow-specific refs.
- Mock UI or technical contract reports are supplied as the only product acceptance evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `ProductWorkflowReadinessRecord`, `ProductAcceptanceGateReport`, and `ProductAcceptanceFixtureManifest` contracts.
- **FR-002**: System MUST define canonical target product workflows: `multi_site_onboarding`, `objective_to_plan_approval`, `dynamic_auth_document_api_crawl`, `evidence_review`, `conflict_resolution`, `drift_repair`, `memory_reuse`, `export_and_withdrawal`, `replay_and_audit`, and `operator_recovery`.
- **FR-003**: System MUST define canonical minimum product gates: `approved_plan_creation`, `reviewer_time_per_output`, `drift_repair_success`, `operator_recovery_completion`, `export_withdrawal_reconciliation`, `user_facing_status_accuracy`, and `buyer_value_workflow_pass`.
- **FR-004**: System MUST require every product workflow readiness record to include evidence refs, replay refs, operator-visible result refs, policy decision refs, command refs, event cursor refs, outbox refs, artifact refs, acceptance oracle refs, and minimum gate refs before pass.
- **FR-005**: System MUST require workflow-specific refs for multi-site source scopes, plan approval, dynamic/browser/auth/document/API crawl, evidence review context, conflict adjudication, drift repair/recovery, memory re-anchoring, export/withdrawal reconciliation, replay audit, and operator recovery.
- **FR-006**: System MUST reject missing workflow, missing minimum gate, missing evidence, missing replay, missing operator visibility, missing policy, missing workflow-specific refs, scaffold-only readiness, contract-only readiness, false complete status, degraded capability mislabeled operational, and missing export reconciliation.
- **FR-007**: System MUST return `needs_review` when live runtime refs needed by product readiness are unavailable; contract-only product descriptors cannot pass.
- **FR-008**: System MUST include a success fixture covering all 10 target workflows and all 7 minimum gates.
- **FR-009**: System MUST include no-runtime and negative fixtures for every failure type listed in FR-006 and FR-007.
- **FR-010**: System MUST register product acceptance contracts, commands, events, fixtures, and target area coverage in the contract registry.
- **FR-011**: System MUST provide a `veracrawl-product-acceptance` fixture runner that validates manifests, expected completion result, typed failure, and writes `run_report.json`.
- **FR-012**: System MUST keep core independent of concrete storage, queues, browser runtimes, HTTP clients, agent frameworks, model SDKs, export targets, UI frameworks, and site-specific scraper logic.
- **FR-013**: System MUST document product acceptance usage and explicitly state that technical contract-only gates, mock UI, scaffold manifests, or degraded runs cannot satisfy product readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **ProductWorkflowReadinessRecord**: Per-workflow proof that buyer-facing value, evidence, replay, policy, operator visibility, command/event/outbox, artifact, and workflow-specific refs exist.
- **ProductAcceptanceGateReport**: Operator/replay-facing report proving all target product workflows and minimum product gates pass or identifying typed readiness failures.
- **ProductAcceptanceFixtureManifest**: Deterministic fixture declaration for success, needs-review, and negative product acceptance scenarios.

### Non-Goals *(mandatory)*

- This feature does not implement a frontend UI, production browser fleet, production external website crawl, production credential vault, production export connector, model call, or agent framework runtime.
- This feature does not make mock UI screenshots, contract-only technical reports, single-site demos, or scaffold manifests valid product readiness proof.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Success fixture emits 10 `ProductWorkflowReadinessRecord` refs and a pass report covering every target product workflow.
- **SC-002**: Success report includes all 7 minimum product gate refs and status accuracy proving no planned, scaffolded, failed, degraded, or contract-only capability is labeled `complete`, `verified`, or `operational`.
- **SC-003**: Missing workflow, missing minimum gate, missing evidence, missing replay, missing operator visibility, missing policy, missing workflow-specific refs, scaffold-only, contract-only, false-complete, degraded-operational, and missing export reconciliation fixtures fail deterministically.
- **SC-004**: Runtime-unavailable fixture returns `needs_review`.
- **SC-005**: Registry validation includes every product acceptance contract, command, event, fixture, and target area coverage.
- **SC-006**: Import-boundary tests prove product acceptance runtime and CLI do not import concrete storage, queue, browser, HTTP, model, agent framework, export, UI, or scraper dependencies.
- **SC-007**: Full local product acceptance fixture loop completes within 30 seconds.

## Assumptions

- Deterministic product acceptance fixtures use stable refs from existing technical gates instead of external websites or live UI automation.
- Product acceptance proves readiness claims and workflow evidence closure; production runtimes remain owned by their existing adapter and infrastructure gates.
- `operational` remains valid only when workflow refs include operator-visible result, observability/recovery, replay, and policy refs.
