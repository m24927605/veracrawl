# Research: Operational Disaster Recovery Gate

## Decision: Operational DR Gate Aggregates Existing Live Infrastructure Results

Use the existing operational infrastructure gate as the substrate for the DR success fixture. The DR gate consumes the integrated `RuntimeInfrastructureReport` plus phase-specific refs for restore point, backup manifest, metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, policy, command, event cursor, outbox, queue recovery, failure/recovery, and replay.

**Rationale**: The user explicitly requires DR to be proven through live Postgres, Redis/Valkey, and S3-compatible refs. Reusing the integrated infrastructure gate prevents a single adapter result from being misrepresented as operational DR completion.

**Alternatives considered**:

- Re-run each adapter independently in the DR module. Rejected because it duplicates the infrastructure gate and risks inconsistent pass semantics.
- Accept deterministic fixture refs for DR pass. Rejected because this would fake operational readiness.

## Decision: Core DR Validation Stays SDK-Neutral

Keep `runtime_support.disaster_recovery` limited to VeraCrawl contracts and core conformance result types. Concrete Postgres, Redis, S3, Docker, or SDK interactions stay in CLI/integration code.

**Rationale**: This preserves the ports/adapters boundary and avoids coupling core recovery semantics to infrastructure SDKs.

**Alternatives considered**:

- Import concrete adapters directly in the DR runtime. Rejected because it violates AGENTS.md and constitution boundaries.
- Add a cloud-specific DR provider. Rejected because managed backup/cloud operations are a separate target gate.

## Decision: DR Failures Produce Existing Ops Failure/Recovery Records

Use `FailureRecord` and `RecoveryAction` for missing refs, unresolved refs, data loss, unsafe recovery, and failed phase validation.

**Rationale**: `docs/07-data-contracts.md` already defines ops failures and recovery actions as the canonical incident surface. DR should not invent a separate failure model.

**Alternatives considered**:

- Store failures only inside `DRRestoreReport.missing_ref_fields`. Rejected because operators need typed failure/recovery refs.
- Treat all negative cases as `needs_review`. Rejected because deterministic missing refs and unsafe recovery are acceptance failures.

## Decision: No-Runtime Is Needs-Review, Not Fail

When live operational infrastructure is not provided, the DR gate returns `needs_review` with contract-only refs.

**Rationale**: This matches prior operational adapter gates: missing live runtime means the feature cannot claim operational pass, but the contract path itself is not a broken implementation.

**Alternatives considered**:

- Fail no-runtime. Rejected because no-runtime is a review state used to prevent false pass claims while preserving contract validation.

## Decision: CLI-First Runner For This Slice

Expose `veracrawl-dr run` for deterministic fixture execution and live gate validation.

**Rationale**: The current target slices are CLI-first and write `.veracrawl-test-runs/` reports. A production dashboard frontend is explicitly out of scope.

**Alternatives considered**:

- Add a web UI or API endpoint. Rejected because UI and production observability are separate target gates.
