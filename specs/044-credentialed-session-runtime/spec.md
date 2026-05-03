# Feature Specification: Credentialed Session Runtime

**Feature Branch**: `044-credentialed-session-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Support authorized credentialed sessions without leaking secrets, exceeding
scope, bypassing login authorization, or allowing credentials/session-native
state to become VeraCrawl canonical state.

## User Stories

### US1 - Use Authorized Session Capability (P1)

As a crawl operator, I need authorized session capability to be available through
a session adapter boundary after live HTTP and browser snapshot prerequisites
exist, with credential use audit, redaction, policy, command/event, and replay
refs.

**Independent Test**: Run `credentialed-session-success` through the CLI and
assert it passes with live HTTP refs, browser snapshot refs, credential audit
refs, redacted session artifacts, redacted replay refs, and no raw secret refs.

### US2 - Deny Unsafe Or Out-Of-Scope Credential Use (P1)

As a policy owner, I need missing authorization, out-of-scope origins, unsafe
credential delivery, raw secret leakage, missing audit, and missing redacted
replay cases to fail deterministically.

**Independent Test**: Run the negative credentialed-session fixtures and verify
typed failures with no passing report refs.

## Functional Requirements

- **FR-001**: Core credentialed session runtime MUST use a session port/adapter
  boundary and MUST NOT import concrete session, browser, network, model, or
  agent framework adapters.
- **FR-002**: Passing reports MUST include live HTTP and browser snapshot
  prerequisite refs, credential scope refs, authorized origin refs, approval
  refs, credential use audit refs, session adapter result refs, redacted session
  artifact refs, redacted replay refs, policy refs, command/event/outbox refs,
  and replay bundle refs.
- **FR-003**: Passing reports MUST NOT include raw secret leak refs or
  adapter-native session state as canonical state.
- **FR-004**: Missing authorization, out-of-scope access, unsafe credential use,
  raw secret leakage, missing audit, missing redacted replay, and replay mismatch
  MUST fail with typed diagnostics.
- **FR-005**: The CLI MAY load deterministic session adapters and local fixture
  servers, but core session runtime MUST remain adapter-neutral.

## Dependencies

- Blocks: 054.
- Requires: 039, 041, 043.

## Completion Gate

Credentialed fixtures prove vault boundary, credential audit, redacted replay,
and denial for out-of-scope, missing-authorization, leakage, or unsafe
credential use.

## Non-Goals

- Does not steal credentials or bypass login walls.
- Does not persist raw secrets as canonical state.
- Does not implement a real external vault or browser login automation engine;
  those remain replaceable adapter concerns.
