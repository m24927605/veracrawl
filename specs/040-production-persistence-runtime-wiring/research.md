# Research: Production Persistence Runtime Wiring

## Decision: Wire Run-Control Through Ports, Not Concrete Adapters

Use a core runtime module that accepts a port-shaped persistence store. The
module persists run-control canonical documents, events, outbox, idempotency,
artifact index, queue operations, and replay refs without importing concrete
Postgres, Redis/Valkey, S3, browser, model, or agent framework clients.

**Rationale**: Specs 017-020 already prove concrete adapter behavior. Spec 040
must prove the production run-control state can use those port shapes without
turning core into adapter glue.

## Decision: Add Canonical Document Methods To Persistence Ports

Extend persistence ports and existing reference/JSON-document adapters with
typed canonical document save/load methods.

**Rationale**: Canonical run-control state must survive restart as actual
contracts, not as refs only. Using typed port methods keeps low coupling and
avoids direct access to adapter internals.

## Decision: Use Detailed Run-Control Execution

Expose a detailed run-control execution result from spec 039 while preserving
the existing public report-returning function.

**Rationale**: Persistence wiring needs the ProductionProject, ProductionSiteScope,
CrawlObjective, CrawlPlan, CrawlRun, budget, policy snapshot, approval, policy
decisions, lifecycle records, and report that the run-control path actually
created.

## Decision: Deterministic Reference Fixtures For 040

Use the existing reference filesystem persistence store for deterministic CLI
fixtures and reopen tests. Do not claim live Postgres/Redis/S3 operational pass
from this spec.

**Rationale**: Deterministic fixtures give exact replay/oracle behavior in CI.
Concrete live adapter gates remain owned by their adapter specs.

## Rejected Alternative: Reuse 015 Fixtures As 040 Completion

Rejected because 015 proves generic persistence/queue semantics but does not
prove row 039 production run-control state is wired through the production
persistence ports.

## Rejected Alternative: Persist Only Report Refs

Rejected because target architecture requires canonical state to survive
restart and replay. The implementation must reload typed canonical documents.
