# Feature Specification: Security Privacy Lifecycle Gate

**Feature Branch**: `023-security-privacy-lifecycle-gate`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Security Privacy Lifecycle Gate：在 operational infrastructure、DR、observability gates 之上，實作 target security/privacy/lifecycle acceptance gate，必須提供 SecurityPolicyCheck、CredentialUseAudit、PromptTaintBoundary、ArtifactLifecycleAction、ProjectionCleanupRecord、SecurityPrivacyReport 與 fixture/oracle 測試，驗證 egress allowlist/private-network deny、prompt-injection/tool misuse blocking、credential prompt leakage 0、raw secret never serialized、artifact classify/redact/tombstone/delete/legal hold/retention/projection cleanup、redacted replay completeness、policy/command/event/outbox/replay/observability refs。Core 不得耦合 browser/model/agent framework/cloud/security vendor SDK，不得實作 CAPTCHA/paywall/WAF/stealth/credential theft/bypass，不得把普通 policy refs 假裝成完整 security privacy lifecycle pass。必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: Security and privacy lifecycle behavior applies to every project, website, adapter, artifact, agent context, export target, replay bundle, graph/memory projection, and recovery path. This feature preserves the general-purpose crawler by defining platform-wide gates instead of one-site access workarounds.
- **Target/V1 boundary**: This is target architecture work for the Security, Privacy, And Lifecycle Profile in `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`. It must not claim target completion, browser execution, authorized-session adapter completion, cloud security integration, or production compliance certification.
- **Evidence and replay impact**: The feature affects policy refs, credential use audit refs, prompt taint refs, artifact lifecycle refs, projection cleanup refs, command refs, event cursor refs, outbox refs, redaction map refs, replay bundle refs, observability refs, and failure/recovery refs.
- **Safety and policy impact**: Unsafe network, prompt, credential, browser, memory, graph, export, recovery, and artifact lifecycle actions must be blocked and logged. Raw secrets must never appear in prompts, logs, replay bundles, artifacts, untrusted page text, or agent-visible state.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove Security And Privacy Lifecycle Pass (Priority: P1)

As a security reviewer, I need one report proving network, credential, prompt, artifact lifecycle, projection cleanup, redacted replay, observability, policy, command, event, and outbox refs are connected, so VeraCrawl can be operated without unsafe hidden exceptions.

**Independent Test**: Run `security-privacy-success`; it passes only with egress/private-network checks, credential audit, prompt taint boundary, lifecycle actions, projection cleanup, redacted replay, observability, policy, command, event cursor, and outbox refs.

### User Story 2 - Reject Policy-Refs-Only Completion (Priority: P2)

As an architecture reviewer, I need policy refs alone to be rejected, so VeraCrawl cannot claim security/privacy readiness without concrete lifecycle and replay evidence.

**Independent Test**: Run `security-privacy-policy-only`; it returns `needs_review` and cannot claim pass.

### User Story 3 - Block Unsafe And Leaky Paths (Priority: P3)

As an operator, I need unsafe network, prompt-injection, credential leakage, missing lifecycle propagation, legal-hold delete, and missing redacted replay cases to fail deterministically with failure/recovery refs.

**Independent Test**: Run each negative fixture independently and assert the expected failure status, missing ref field, policy refs, observability refs, and replay status.

### Edge Cases

- Egress origin is not allowlisted, or target resolves to private/link-local/loopback address.
- Prompt-injection content attempts tool misuse, credential exfiltration, publication, or recovery actions.
- Credential use lacks authorization, scoped delivery mode, origin allowlist, audit refs, or redaction refs.
- Raw secret-like values appear in prompt, log, replay, artifact, trace, or untrusted page refs.
- Redaction, tombstone, delete, retention, legal hold, or projection cleanup refs are missing.
- Delete is requested while legal hold is active.
- Redacted replay lacks structural completeness.
- Observability refs are absent for security/privacy failure or recovery.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define executable `SecurityPolicyCheck`, `CredentialUseAudit`, `PromptTaintBoundary`, `ArtifactLifecycleAction`, `ProjectionCleanupRecord`, `SecurityPrivacyReport`, and `SecurityPrivacyFixtureManifest`.
- **FR-002**: Passing reports MUST require egress allowlist/private-network deny refs, prompt taint refs, credential audit refs, lifecycle action refs, projection cleanup refs, redacted replay refs, observability refs, policy refs, command refs, event cursor refs, outbox refs, failure/recovery refs, and zero credential prompt leakage.
- **FR-003**: System MUST return `needs_review` for policy-refs-only security/privacy evidence.
- **FR-004**: System MUST fail unsafe network, prompt-injection tool misuse, credential prompt leakage, missing lifecycle propagation, legal-hold delete, missing projection cleanup, missing redacted replay, and missing observability refs.
- **FR-005**: System MUST reject any raw secret-like value in prompt, log, replay, artifact, trace, browser, model, or agent-visible refs.
- **FR-006**: System MUST keep core security/privacy validation independent of browser libraries, model SDKs, agent frameworks, cloud SDKs, and security vendor SDKs.
- **FR-007**: System MUST expose a repeatable `veracrawl-security-privacy` fixture runner.
- **FR-008**: System MUST register contracts, commands, events, fixture oracles, and target area in the canonical registry.
- **FR-009**: System MUST update README and target docs with capability, fixtures, and non-completion boundary.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid single-site, bypass, or vertical assumptions.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define output/evidence behavior when privacy lifecycle affects source evidence, publication, export, graph, memory, or replay.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal behavior.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **SecurityPolicyCheck**: Policy-visible check for unsafe network, prompt, credential, browser, memory, graph, export, recovery, or artifact lifecycle action.
- **CredentialUseAudit**: Scoped credential delivery audit record with origin, mode, authorization, redaction, policy, and replay refs.
- **PromptTaintBoundary**: Record proving untrusted content and tainted context cannot steer unsafe tools, credential use, publication, or recovery.
- **ArtifactLifecycleAction**: Classify, redact, tombstone, delete, legal hold, retention, or release action with policy, approval, projection, and replay refs.
- **ProjectionCleanupRecord**: Cleanup propagation record for graph, memory, search, dashboard, export, and replay projections affected by privacy lifecycle changes.
- **SecurityPrivacyReport**: Gate result tying all security/privacy refs into one pass/fail/needs-review record.

### Non-Goals *(mandatory)*

- This feature does not implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
- This feature does not implement concrete browser execution, concrete authorized-session adapter runtime, model SDK integration, agent framework integration, cloud security integrations, DLP vendors, compliance certification, or production deployment automation.
- This feature does not claim full target architecture completion. It proves the backend/vendor-neutral security privacy lifecycle gate only.

## Success Criteria *(mandatory)*

- **SC-001**: `security-privacy-success` produces `pass` only when all required refs and zero leakage are present.
- **SC-002**: `security-privacy-policy-only` produces `needs_review` and never `pass`.
- **SC-003**: Negative fixtures produce deterministic `fail` results for unsafe network, prompt-injection tool misuse, credential leakage, missing lifecycle propagation, legal-hold delete, missing projection cleanup, missing redacted replay, and missing observability refs.
- **SC-004**: Registry validation, import-boundary tests, focused tests, CLI fixtures, ruff, mypy, and full pytest pass.

## Assumptions

- Existing policy, artifact, ops, replay, observability, and failure/recovery contracts provide refs consumed by this gate.
- This slice validates canonical security/privacy lifecycle behavior; concrete vaults, browser workers, DLP vendors, and cloud security systems remain adapter-owned future gates.
