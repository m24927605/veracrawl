# Feature Specification: Production Run Control API

**Feature Branch**: `039-production-run-control-api`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Constitution Alignment

- **General-purpose crawler impact**: Production run control models projects,
  site scopes, objectives, plans, approvals, budgets, policy snapshots, and run
  lifecycle for arbitrary authorized crawl targets. It does not encode a
  single-site workflow or scraper.
- **Target/V1 boundary**: This is the first post-037 production runtime spec. It
  activates roadmap row 039 and provides the control-plane prerequisite for
  live acquisition, persistence, agent adapters, credentials, and release gates.
- **Evidence and replay impact**: Every lifecycle action must emit canonical
  command result refs, event refs, policy decision refs, replay refs, and
  operator-visible diagnostics.
- **Safety and policy impact**: Runs cannot start without approved objective,
  approved plan, budget ref, source policy refs, policy snapshot refs, and
  approval refs. Policy-denied and invalid transitions must fail visibly.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## User Stories & Testing

### User Story 1 - Start Approved Production Run (Priority: P1)

As a platform operator, I need a real run-control path that turns a project,
site scope, objective, approved plan, budget, and policy snapshot into a running
or completed run through canonical commands/events.

**Independent Test**: Run `veracrawl-run-control run tests/fixtures/production-run-control-success --profile target --out .veracrawl-test-runs/production-run-control-success`; the report passes only when project, site, objective, plan, approval, budget, policy snapshot, command result, event, lifecycle, and replay refs are present.

### User Story 2 - Enforce Run Lifecycle Rules (Priority: P2)

As a Staff reviewer, I need pause, resume, cancel, fail, complete, and invalid
transition behavior to be typed, replayable, and impossible to fake by direct
state mutation.

**Independent Test**: Paused/resumed and cancelled fixtures pass with lifecycle
records; invalid transition fixtures fail with `production_run_control_invalid_transition`.

### User Story 3 - Block Unsafe Or Unapproved Runs (Priority: P3)

As a policy owner, I need run control to block missing approvals, policy denial,
missing budgets, or missing replay refs before any source acquisition spec can
execute.

**Independent Test**: Missing-approval, policy-denied, missing-budget, and
missing-replay fixtures fail or block with typed failure refs and cannot produce
a successful run-control report.

## Requirements

- **FR-001**: System MUST define production run-control contracts for project,
  site scope, run budget, policy snapshot, approval, lifecycle record, report,
  and fixture manifest.
- **FR-002**: System MUST expose a production run-control CLI that executes
  deterministic run-control fixtures and writes `run_report.json`.
- **FR-003**: System MUST allow only approved objectives and approved plans to
  start a run.
- **FR-004**: System MUST require budget refs and policy snapshot refs before a
  run can enter `running`.
- **FR-005**: System MUST emit command results and event refs for create,
  approve, start, pause, resume, cancel, fail, and complete lifecycle actions.
- **FR-006**: System MUST reject invalid run lifecycle transitions with typed
  diagnostics.
- **FR-007**: System MUST block policy-denied and missing-approval runs before
  downstream acquisition can start.
- **FR-008**: System MUST register run-control contracts, commands, events,
  fixture oracles, and target area coverage.
- **FR-009**: System MUST preserve existing runtime, target runtime, source,
  adapter, and processing/evidence fixture behavior.

## Key Entities

- **ProductionProject**: Tenant/project boundary for production crawl runs.
- **ProductionSiteScope**: Authorized site/source scope and policy refs for a
  project.
- **RunBudget**: Crawl, browser, model, queue, storage, and runtime limits for
  a run.
- **RunPolicySnapshot**: Immutable policy refs captured at run start.
- **RunApprovalRecord**: Approval or rejection proof for objective/plan
  activation.
- **RunLifecycleRecord**: Replayable lifecycle transition proof.
- **ProductionRunControlReport**: Operator-visible result of run-control
  execution.
- **ProductionRunControlFixtureManifest**: Fixture expectation contract.

## Non-Goals

- Does not implement live HTTP, browser, structured source, or credentialed
  acquisition.
- Does not implement production persistence wiring; deterministic repositories
  are still behind ports until spec 040.
- Does not implement worker orchestration or scale runtime.
- Does not bypass source scope, robots/terms, credential, browser, prompt-taint,
  privacy, retention, or export policy.

## Success Criteria

- **SC-001**: Success fixture starts/completes an approved run with command,
  event, approval, budget, policy snapshot, lifecycle, and replay refs.
- **SC-002**: Pause/resume and cancel fixtures produce replayable lifecycle
  records.
- **SC-003**: Missing approval, policy denial, missing budget, invalid
  transition, and missing replay fixtures fail or block with typed failure refs.
- **SC-004**: Registry validation passes and `production_run_control_api` target
  area is materialized.
- **SC-005**: Full contract/unit/integration gates pass.
