# Feature Specification: Browser Snapshot Runtime

**Feature Branch**: `043-browser-snapshot-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Add a policy-gated browser snapshot runtime for JavaScript-required pages while
preserving VeraCrawl's target architecture boundaries: browser capability must
be reached through ports/adapters, core state must remain framework-neutral and
browser-native-state-free, and every successful snapshot must produce canonical
artifact, policy, budget, command/event, prompt-taint, and replay refs.

## User Stories

### US1 - Capture A Browser-Required Page (P1)

As a crawl operator, I need an authorized JS-required page to produce a browser
snapshot report that contains DOM, screenshot, network trace, console log,
timing, policy, budget, command/event/outbox, and replay refs.

**Independent Test**: Run the `browser-snapshot-success` fixture through the CLI
and assert the report passes with all required browser refs.

### US2 - Enforce Browser Safety Gates (P1)

As a policy owner, I need unsafe browser actions, blocked egress, exhausted
browser budget, and prompt-tainted rendered content to fail deterministically
with typed failure reports.

**Independent Test**: Run negative fixtures for egress denied, unsafe
interaction, budget exceeded, and prompt-tainted content; each must fail with
the expected failure type and no passing report refs.

### US3 - Preserve Replay And Upstream Acquisition Boundaries (P2)

As a replay reviewer, I need browser snapshot reports to carry refs to live HTTP
and structured source prerequisite reports without embedding adapter-native
state or pretending browser artifacts are source evidence.

**Independent Test**: Validate the contract and runtime tests showing pass
requires upstream report refs, replay refs, and browser artifacts; replay
mismatch and missing artifact fixtures must fail.

## Functional Requirements

- **FR-001**: Core browser snapshot runtime MUST accept browser capability
  through `BrowserSourceAdapterPort`; it MUST NOT import concrete browser,
  network, source, model, or agent framework adapters.
- **FR-002**: Passing browser snapshot reports MUST include refs for sandbox
  policy, browser interaction step, DOM artifact, screenshot artifact, network
  trace artifact, console log artifact, timing artifact, browser budget,
  policy decisions, command records, event cursors, outbox records, replay
  bundle, live HTTP acquisition report, and structured source runtime report.
- **FR-003**: Browser snapshot fixtures MUST cover success plus typed failures
  for policy/egress denial, unsafe interaction, budget exhaustion,
  prompt-tainted content, missing artifact, and replay mismatch.
- **FR-004**: The CLI MAY load concrete deterministic fixture adapters, but the
  core runtime MUST remain port-only and canonical reports MUST not store
  browser-native state.
- **FR-005**: Browser snapshot runtime MUST preserve 041 and 042 dependencies by
  carrying upstream report refs and must not bypass source acquisition paths.
- **FR-006**: The registry MUST materialize browser snapshot contracts, command
  types, event types, fixture oracles, and target area coverage.

## Dependencies

- Blocks: 044, 045, 054.
- Requires: 041, 042.

## Completion Gate

Browser-required fixtures pass only with browser artifacts, policy/budget refs,
and replay refs; unsafe interactions, excessive cost, prompt-tainted content, or
blocked network access fail deterministically.

## Non-Goals

- Does not solve CAPTCHA, bypass paywalls, evade WAFs, or automate unauthorized
  login walls.
- Does not add a production Playwright/Selenium adapter in this slice; concrete
  browser engines stay behind the existing browser port and can be introduced by
  later adapters without changing core contracts.
