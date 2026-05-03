# Feature Specification: Repair Success Rate Benchmark

**Feature Branch**: `063-repair-success-rate-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Measure AI-assisted crawl, extraction, verification, drift, and replay repair success.

## Constitution Alignment

- **General-purpose crawler impact**: Tests repair across failure families rather
  than one brittle selector or single website.
- **Target/V1 boundary**: Quality benchmark after extraction metrics; it does
  not complete cost/latency/stability release by itself.
- **Evidence and replay impact**: Every repair needs before/after evidence,
  model/agent/tool/context traces where AI is used, owner-service command refs,
  rollback/escalation refs, event/outbox refs, and replay refs.
- **Safety and policy impact**: Repairs cannot bypass robots, source scope,
  credential scope, evidence gates, verification gates, or publication gates.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/06-agent-system-design.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`,
  `specs/050-multi-agent-orchestration-repair-runtime/spec.md`,
  `specs/061-field-level-oracle-extraction-benchmark/spec.md`, and
  `specs/062-precision-recall-quality-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Run Seeded Repair Cases (Priority: P1)

An operator can run a repair benchmark containing seeded crawl, extraction,
verification, drift, and replay failures and receive repair success metrics.

**Independent Test**: Run `veracrawl-repair-quality-benchmark run
tests/fixtures/repair-quality-corpus --profile quality --out
.veracrawl-real-runs/repair-quality-corpus`.

**Acceptance Scenarios**:

1. **Given** a seeded extraction drift, **When** repair runs, **Then** the repair
   either produces source-backed corrected fields or escalates with typed
   diagnostics.
2. **Given** a policy-denied target, **When** repair runs, **Then** it does not
   attempt bypass and records a non-repairable policy outcome.

### User Story 2 - Measure Repair Safety And Cost (Priority: P2)

Maintainers can see repair attempts, success rate, model/tool calls, token usage,
latency, rollback, and unresolved escalation.

**Independent Test**: Validate metric reports for attempts, success, failure,
rollback, cost, and escalation refs.

### User Story 3 - Block Unsafe Repair Bypass (Priority: P3)

Unsafe repairs must fail even if they would increase apparent recall.

**Independent Test**: Negative fixtures cover owner-service bypass, direct
publication, model-only evidence, missing rollback, policy bypass, missing
replay, and unresolved conflict.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define repair benchmark manifests, seeded failure
  records, repair attempt traces, repair outcome records, and repair quality
  reports.
- **FR-002**: Quality profile MUST include at least 30 seeded repair cases across
  crawl planning, fetch/browser, normalization, extraction, verification,
  publication, drift, and replay failure families.
- **FR-003**: Default quality thresholds MUST require repair success rate >=
  0.80 for repairable cases, unsafe bypass rate = 0, and unresolved critical
  repair rate = 0.
- **FR-004**: Every AI-assisted repair MUST include model call, agent action,
  tool call, context bundle, policy, command/event/outbox, before/after evidence,
  rollback/escalation, and replay refs.
- **FR-005**: Repairs MUST be classified as repaired, non-repairable-policy,
  escalated, rollback-applied, failed-safe, or failed-unsafe.
- **FR-006**: System MUST fail any repair that treats model/agent output as
  source evidence or bypasses owner-service commands.

### VeraCrawl Contract Requirements

- **VC-001**: Repair logic must remain general and failure-family based, not
  hard-coded to one website.
- **VC-002**: Owner services, commands, events, policy decisions, rollback,
  outbox, typed failures, and replay refs are mandatory.
- **VC-003**: Repaired outputs must pass evidence and verification gates before
  publication.
- **VC-004**: Credential, prompt-injection, privacy, retention, and export/
  withdrawal boundaries must be preserved during repairs.
- **VC-005**: Include seeded positive/negative repair fixtures, replay tests,
  import-boundary tests, focused/full/Docker validation.

### Key Entities

- **SeededRepairCase**: Declares failure family, input refs, expected repairable
  status, policy constraints, and oracle outcome.
- **RepairAttemptTrace**: One repair attempt with AI/tool/owner-service traces,
  cost, latency, evidence, rollback, and replay refs.
- **RepairQualityReport**: Aggregates success rate, unsafe bypass rate, cost,
  latency, escalation, and replay status.

### Non-Goals

- This spec does not bypass policy to improve metrics.
- This spec does not optimize prompts privately; prompt/model changes must be
  traceable through the framework-neutral abstraction.

## Success Criteria

- **SC-001**: At least 30 seeded repair cases run across the required failure
  families.
- **SC-002**: Repairable-case success rate is >= 0.80, unsafe bypass rate is 0,
  and unresolved critical repair rate is 0.
- **SC-003**: 100% of AI-assisted repairs include full model/agent/tool/context,
  policy, command/event/outbox, evidence, rollback/escalation, and replay refs.
- **SC-004**: Validation results are recorded in `tasks.md`.

## Assumptions

- Public website drift cases may be supplemented by deterministic fixtures to
  keep failure injection stable and ethically low impact.
