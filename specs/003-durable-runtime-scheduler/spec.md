# Feature Specification: VeraCrawl Durable Runtime Persistence and Scheduler Foundation

**Feature Branch**: `003-durable-runtime-scheduler`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Durable Runtime Persistence and Scheduler Foundation：將目前 Target Core Runtime Spine 從 deterministic in-memory profile 推進到可替換 durable persistence、append-only event store、outbox、artifact store adapter boundary、scheduler/frontier/queue lease contracts、idempotent command handling、crash-resume/replay recovery、fixture/oracle 測試基礎。必須遵守 docs/07、09、10、11、constitution 與 AGENTS.md；不得實作成單站 scraper；core 不得耦合任何 storage、queue、browser、model SDK 或 agent framework。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature gives VeraCrawl durable runtime and scheduling foundations for many websites, source families, schemas, crawl objectives, and replay scenarios. It does not introduce site-specific scraping logic or one-off extraction assumptions.
- **Target/V1 boundary**: This is target architecture dependency sequencing. It advances the target runtime spine toward durable state, queueing, crash-resume, and recovery foundations governed by `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: The feature affects command results, append-only events, event cursors, outbox records, artifact refs, scheduler leases, frontier state, replay recovery reports, and fixture oracles. Replay-critical refs must remain complete and deterministic.
- **Safety and policy impact**: Scheduler and persistence gates must preserve source scope, credential isolation, prompt-injection isolation, privacy lifecycle refs, retention refs, and publication safety. Blocked or unauthorized sources must be recorded and recoverable, not bypassed.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persist Runtime State Through Ports (Priority: P1)

As a VeraCrawl operator, I need objective, run, command, event, artifact, and replay state to be written through durable contracts and replaceable ports so a crawler run can be resumed or audited without relying on in-memory process state.

**Why this priority**: Durable state is the baseline for a real general-purpose crawler runtime. Without it, scheduling, replay, recovery, and future production adapters cannot be trusted.

**Independent Test**: Run a deterministic durable persistence fixture that commits commands and events through the durable profile, reloads a new repository instance from the same backing store, and proves all runtime refs and replay cursors are recoverable.

**Acceptance Scenarios**:

1. **Given** an approved runtime objective and plan, **When** durable command handling commits source and processing mutations, **Then** command results, event records, outbox records, artifact refs, and replay cursors are persisted through ports.
2. **Given** a restarted runtime process using the same durable fixture backing store, **When** it reloads the run state, **Then** objective, run, command result, event cursor, outbox, artifact, and replay refs are still available.
3. **Given** a duplicate command with the same idempotency key, **When** the command handler receives it again, **Then** the durable profile returns the prior command result without appending duplicate events or outbox records.

---

### User Story 2 - Schedule Frontier Work With Leases (Priority: P2)

As a VeraCrawl scheduler, I need frontier items and queue leases to be durable, owner-controlled, idempotent, and replay-visible so crawler workers can claim work fairly and safely.

**Why this priority**: General-purpose crawling needs scheduling and frontier coordination before adding real source adapters, browser workers, or graph-informed prioritization.

**Independent Test**: Run scheduler contract and unit tests that enqueue frontier items, lease the next available item, heartbeat or release leases, expire stale leases, and verify event/outbox records are emitted without direct adapter coupling.

**Acceptance Scenarios**:

1. **Given** frontier items for multiple source refs, **When** the scheduler leases work, **Then** the highest-priority eligible item receives a lease token and emits a lease event.
2. **Given** a leased item with a valid lease token, **When** the worker completes it, **Then** the item transitions to completed and the lease cannot be reused.
3. **Given** a lease past its expiry, **When** the scheduler checks for recovery, **Then** the item becomes eligible for retry and recovery events are written.

---

### User Story 3 - Recover From Crash And Replay Gaps (Priority: P3)

As an operator reviewing a run, I need crash-resume and replay recovery reports to identify missing event, outbox, artifact, lease, and command refs so incomplete runs can fail visibly or resume safely.

**Why this priority**: Recovery behavior must be explicit before production adapters or distributed workers exist, otherwise failures can silently corrupt crawl output.

**Independent Test**: Run crash-resume and replay-gap fixtures that simulate unflushed outbox records, missing artifact refs, event sequence gaps, stale leases, and duplicate commands; verify typed recovery reports and no false publication.

**Acceptance Scenarios**:

1. **Given** an event sequence gap, **When** replay recovery validates the durable run, **Then** a recovery report identifies the missing event cursor and marks replay incomplete.
2. **Given** an outbox record committed but not dispatched, **When** recovery scans the durable outbox, **Then** the record is visible as pending and can be marked dispatched idempotently.
3. **Given** a stale lease after a simulated crash, **When** recovery runs, **Then** the scheduler emits a retry-visible recovery report and the work item can be leased again.

---

### User Story 4 - Preserve Adapter-Neutral Durable Boundaries (Priority: P4)

As a VeraCrawl developer, I need persistence, scheduler, artifact, queue, browser, model, and agent framework dependencies to remain behind ports so target architecture can add real adapters without core coupling.

**Why this priority**: The durable foundation must not become a concrete database, queue, browser, SDK, or framework script hidden inside core runtime.

**Independent Test**: Contract and import-boundary tests prove core packages expose protocols and deterministic fixture adapters only; they do not import concrete storage, queue, browser, model SDK, or agent framework dependencies.

**Acceptance Scenarios**:

1. **Given** durable runtime and scheduler modules, **When** import-boundary tests inspect core packages, **Then** no forbidden concrete dependency imports are present.
2. **Given** deterministic fixture adapters, **When** production adapter placeholders are replaced later, **Then** core contracts, commands, events, and replay reports remain unchanged.

### Edge Cases

- Duplicate commands with the same idempotency key must return the original command result and must not append duplicate events or outbox records.
- Event sequence gaps must fail replay recovery and must identify the missing cursor range.
- Outbox records may be pending, dispatched, or failed; dispatch state must be idempotent and replay-visible.
- Artifact refs may be missing, redacted, tombstoned, or legally held; recovery must report the lifecycle state and block unsafe publication.
- Queue leases may expire, be heartbeated, be completed, or be released; invalid lease tokens must be rejected.
- Scheduler retry limits and dead-letter outcomes must be visible to operators and replay.
- Crash-resume must never mark a run complete when required command, event, outbox, artifact, lease, or replay refs are missing.
- Durable fixture storage must be deterministic and replaceable by production adapters without changing core domain behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define durable UnitOfWork, runtime repository, event store, outbox, artifact store, scheduler repository, and queue lease ports with typed command/result semantics.
- **FR-002**: System MUST provide a deterministic durable fixture profile that persists runtime state across repository instances within a fixture run.
- **FR-003**: System MUST make command handling idempotent by idempotency key and target aggregate, returning the prior CommandResult for duplicate commands without appending duplicate events.
- **FR-004**: System MUST persist append-only events with contiguous per-run sequence enforcement and event cursor generation.
- **FR-005**: System MUST persist outbox records for command/event side effects and expose pending, dispatched, and failed dispatch states.
- **FR-006**: System MUST define scheduler frontier item, queue lease, retry/dead-letter, and scheduler recovery report contracts.
- **FR-007**: System MUST allow the scheduler to enqueue, lease, heartbeat, complete, release, expire, retry, and dead-letter frontier items through owner-service commands.
- **FR-008**: System MUST validate lease tokens for all leased work mutations and reject wrong-token or expired-token mutations.
- **FR-009**: System MUST build durable replay recovery reports that validate command refs, event cursors, outbox refs, artifact refs, lease refs, and replay refs.
- **FR-010**: System MUST block completion or publication when durable replay recovery reports missing required refs or failed recovery gates.
- **FR-011**: System MUST keep durable persistence, queueing, artifact, browser, model SDK, storage client, and agent framework implementations behind replaceable adapters or deterministic fixture adapters.
- **FR-012**: System MUST register durable runtime, outbox, scheduler, lease, recovery, command, event, and fixture/oracle contracts in the executable registry.
- **FR-013**: System MUST include deterministic success and negative fixtures for durable persistence, duplicate command, event gap, pending outbox, stale lease recovery, and invalid lease token.
- **FR-014**: System MUST emit operator-visible diagnostics for event gaps, missing artifacts, pending outbox records, duplicate commands, invalid leases, expired leases, retry exhaustion, and dead letters.
- **FR-015**: System MUST preserve the current target runtime spine behavior while adding durable profile capability.
- **FR-016**: System MUST document which durable capabilities are implemented and which production adapters remain non-goals for this slice.
- **FR-017**: System MUST keep all durable foundations general-purpose across websites, source types, schemas, and crawler objectives.
- **FR-018**: System MUST ensure fixture/oracle acceptance proves no false claim of full production crawler, full browser capability, full graph/memory capability, or production scale readiness.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **UnitOfWork**: A transaction boundary for durable command handling, event append, outbox append, and repository writes.
- **DurableCommandRecord**: A durable idempotency and command-result record keyed by idempotency key, target aggregate, and command type.
- **OutboxRecord**: A durable dispatchable side-effect record linked to command results and events.
- **EventCursorRecord**: A per-run event range that proves contiguous replay coverage.
- **FrontierItem**: A durable scheduler work item representing source or processing work.
- **QueueLease**: A durable claim on a frontier item with token, owner, expiry, heartbeat, and completion state.
- **SchedulerRecoveryReport**: A typed report for expired leases, retryable items, dead letters, and invalid lease mutations.
- **DurableReplayRecoveryReport**: A typed report for command, event, outbox, artifact, lease, and replay completeness.
- **DurableFixtureManifest**: A deterministic fixture/oracle descriptor for durable persistence and scheduler recovery scenarios.

### Non-Goals *(mandatory)*

- This feature does not add production Postgres, Redis, Kafka, object storage, browser, graph database, vector store, export connector, model SDK, or agent framework dependencies.
- This feature does not implement distributed workers, production migrations, production queue tuning, or production-scale crawl throughput.
- This feature does not implement full browser crawling, graph intelligence, memory intelligence, export connectors, or site-specific scrapers.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A durable success fixture reloads state from a new repository instance and recovers objective, run, command result, event cursor, outbox, artifact, and replay refs with zero missing required refs.
- **SC-002**: Duplicate command tests prove exactly one committed event and one outbox record exist for repeated command submissions with the same idempotency key.
- **SC-003**: Scheduler tests prove enqueue, lease, heartbeat, complete, release, expire, retry, and dead-letter transitions with typed lease-token validation.
- **SC-004**: Negative fixtures for event gap, pending outbox, stale lease, invalid lease token, and missing artifact produce typed non-success recovery reports and no false publication.
- **SC-005**: Registry validation includes every durable runtime, outbox, scheduler, lease, recovery, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core durable runtime and scheduler packages do not import concrete storage, queue, browser, model SDK, or agent framework dependencies.
- **SC-007**: The full local gate of registry validation, runtime fixture validation, durable fixture validation, ruff, mypy, and pytest completes within 30 seconds in the deterministic fixture profile.
- **SC-008**: Documentation clearly states the durable foundation capability and explicitly avoids claiming full production crawler or production persistence readiness.

## Assumptions

- Deterministic durable fixture storage is acceptable for this slice if it exercises the same ports and contracts that production adapters will implement later.
- Production database and queue adapters will be introduced in later specs after contracts, idempotency, event cursor, outbox, and scheduler semantics are stable.
- The existing Target Core Runtime Spine remains the source of objective-to-output runtime behavior; this feature adds durable and scheduler foundations around it.
- All state and reports are represented as VeraCrawl contracts and refs; concrete adapter-native state is never canonical.
