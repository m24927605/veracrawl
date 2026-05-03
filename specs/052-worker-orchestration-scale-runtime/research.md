# Research: Worker Orchestration And Scale Runtime

## Decision 1: Add A Worker Orchestration Aggregate

The existing `ScaleRecoveryReport` proves queue topology, shard lease,
backpressure, autoscaling, dead-letter, failure, recovery, and replay refs for a
scale hardening slice. Row 052 needs a production aggregate that also ties these
refs to persistence, queue broker, source acquisition, normalization, evidence,
and all target worker pools.

Rationale:

- Avoids weakening existing lower-level contracts.
- Gives rows 053 and 054 one runtime report for operator and benchmark gates.
- Preserves owner boundaries by composing refs instead of moving queue logic.

Rejected alternative:

- Extend `ScaleRecoveryReport` to own production dependency refs. That would mix
  generic scale hardening with production crawl-worker orchestration.

## Decision 2: Passing Reports Cover Every Target Worker Pool

The report must include frontier, fetch, browser, processing, verification,
review, export, projection, and recovery worker pool refs.

Rationale:

- Long-running crawls fail operationally when one pool lacks leases or recovery.
- This prevents a fetch-only scale proof from being mislabeled target-complete.

Rejected alternative:

- Accept a subset of pools and defer the rest. The user explicitly requires
  target architecture capability without artificial weakening.

## Decision 3: Dead-Letter And Duplicate Outcomes Are Operator-Visible

Passing reports must include dead-letter refs, failure refs, recovery action
refs, duplicate-suppression refs, and replay refs. Hidden dead letters and
duplicate pollution are typed failures.

Rationale:

- Silent item loss and duplicate output pollution are central completion risks.
- Operators and replay must see failed work and dedup decisions.

Rejected alternative:

- Treat duplicate suppression or dead-letter visibility as internal queue
  behavior. That would make correctness unauditable.

## Decision 4: Core Remains Dependency-Neutral

The row 052 runtime creates deterministic refs and composes existing core
contracts. Concrete Redis/Postgres/S3 adapters remain behind existing adapter
packages and Docker-backed tests.

Rationale:

- Core replay and worker orchestration contracts must not depend on operational
  client libraries.
- Docker-backed tests already cover adapter compatibility without coupling core.

Rejected alternative:

- Import concrete broker or database clients directly in the worker
  orchestration runtime. That would violate ports/adapters boundaries.
