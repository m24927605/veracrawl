# Research: Production Run Control API

## Decision: Extend Objective Contracts

Add production run-control contracts to `veracrawl.contracts.objective` rather
than creating a separate contract module.

**Rationale**: Project, site scope, approval, budget, policy snapshot, lifecycle,
and run-control report are control-plane concepts owned by the same service as
`CrawlObjective`, `CrawlPlan`, and `CrawlRun`.

## Decision: Deterministic Runner Before Production Persistence

Implement `veracrawl.control.run_control` with deterministic in-memory execution
behind existing command/event helpers.

**Rationale**: Spec 040 owns production persistence wiring. Spec 039 must prove
the lifecycle and policy semantics without importing concrete storage clients.

## Decision: Separate CLI From Existing Runtime Fixture CLI

Add `veracrawl-run-control` rather than overloading `veracrawl-runtime`.

**Rationale**: `veracrawl-runtime` executes the existing objective-to-output
spine. Run-control fixtures focus on project/site/objective/plan/run lifecycle
and should remain a bounded production control-plane gate.

## Decision: Typed Failure Enum

Add production run-control failure types for policy denial, missing approval,
missing budget, invalid transition, and missing replay.

**Rationale**: Negative fixtures need operator-visible, replayable failure
semantics and must not collapse to generic validation errors.
