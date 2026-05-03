# Feature Specification: VeraCrawl Target Area Readiness Impact Closure

**Feature Branch**: `033-target-area-readiness-closure`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "建立 VeraCrawl Target Area Readiness Impact Closure：修正 TargetContractAreaCoverage 在所有 materialized target areas 仍保留 must define replay/privacy before target-complete claim 的矛盾描述；新增 executable registry tests，確保 materialized target area 不得有 placeholder/followup/target-complete 前置語句，必須呈現已由 registered contracts、fixture gates、policy/replay/privacy lifecycle refs materialized 的狀態。必須遵守 docs/07、09、10、11 與 constitution，不得用文字假裝 target-ready。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This change prevents target-readiness metadata from falsely implying unresolved target work after all registered crawler capability areas are materialized.
- **Target/V1 boundary**: This is target architecture registry correctness work for `docs/09` completion states and `docs/11` non-deceptive completion rules.
- **Evidence and replay impact**: Materialized target areas must state that replay refs are represented by registered contracts and fixture gates, not that replay is still undefined.
- **Safety and policy impact**: Materialized target areas must state that privacy lifecycle/policy refs are represented where required, not that privacy lifecycle is still undefined.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Contradictory Target Area Impact Text (Priority: P1)

As a Staff reviewer, I need every materialized target area to have replay and privacy impact text that matches its materialized registry status.

**Why this priority**: A materialized target area that still says replay/privacy must be defined before target completion undermines non-deceptive target readiness.

**Independent Test**: Registry tests fail if any materialized target area contains `before target-complete`, `must define`, `placeholder`, or a follow-up gate in replay/privacy impact fields.

**Acceptance Scenarios**:

1. **Given** a target area has `coverage_status=materialized`, **When** registry validation runs, **Then** its replay and privacy impact text must describe materialized refs.
2. **Given** a target area is materialized, **When** tests inspect the registry, **Then** it must not have placeholder refs, followup gates, or target-complete prerequisite wording.

---

### User Story 2 - Preserve Deferred-Area Semantics (Priority: P2)

As an architecture owner, I need future non-materialized areas to keep explicit follow-up gate semantics.

**Why this priority**: Closing current target readiness wording must not weaken future validation for genuinely deferred areas.

**Independent Test**: Existing registry validation still requires non-materialized areas to carry a follow-up spec gate.

**Acceptance Scenarios**:

1. **Given** a future target area is not materialized, **When** validation runs, **Then** it still requires a follow-up spec gate.

### Edge Cases

- A materialized area accidentally keeps `must define replay refs before target-complete claim`.
- A materialized area has empty impact text.
- A materialized area has placeholder refs or a follow-up spec gate.
- Future non-materialized areas still require follow-up gates.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST update `TargetContractAreaCoverageRegistration` construction so materialized target areas have replay and privacy lifecycle impact text that describes materialized registered refs.
- **FR-002**: System MUST keep non-materialized target areas requiring `followup_spec_gate`.
- **FR-003**: System MUST add registry tests that fail when a materialized target area has placeholder refs, follow-up gates, `before target-complete`, `must define`, or `placeholder` wording in impact fields.
- **FR-004**: System MUST preserve existing registry validation, contract exports, fixture registrations, and target area materialization.
- **FR-005**: System MUST update active Spec Kit pointers and docs where the closure affects target-readiness claims.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **TargetContractAreaCoverageRegistration**: Registry record whose impact fields must match materialized/deferred status.

### Non-Goals *(mandatory)*

- This feature does not add new crawler runtime behavior, adapters, product workflows, or UI.
- This feature does not use wording changes to hide missing contracts or fixture gates.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Registry scan finds zero materialized target areas with `before target-complete`, `must define`, or `placeholder` wording in replay/privacy impact fields.
- **SC-002**: Registry scan finds zero materialized target areas with placeholder refs or follow-up gates.
- **SC-003**: `validate_registry()` remains `ok: true`.
- **SC-004**: Full test gates remain passing.

## Assumptions

- Current target areas are already materialized by specs 001-032.
- Future deferred areas will still be represented with non-materialized status and explicit follow-up gates.
