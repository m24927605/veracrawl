# Feature Specification: Schema Extraction Candidate Runtime

**Feature Branch**: `046-schema-extraction-candidate-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Generate schema-bound extraction strategies and anchored candidates from live
normalization results while keeping candidates separate from evidence,
verification, publication, and exported outputs.

## User Stories

### US1 - Produce Schema-Bound Candidates (P1)

As an extraction runtime, I need a passing live normalization report and
normalized document objects to produce extraction strategy refs, extraction
candidate refs, field anchor refs, schema validation refs, framework-neutral
model/tool trace refs, policy refs, command/event/outbox refs, and replay refs.

**Independent Test**: Run `schema-extraction-record-success` through the CLI and
assert a passing report with every candidate field anchored to source text.

### US2 - Support Approved Exploratory Schemas (P1)

As an operator, I need exploratory schemas to be allowed only when explicitly
approved, and I need their candidates to carry the same anchors, validation,
trace, policy, and replay refs as declared schemas.

**Independent Test**: Run `schema-extraction-exploratory-success` and assert a
passing report with an approved exploratory schema ref and no publication refs.

### US3 - Fail Unsafe Or Incomplete Candidates (P1)

As a reviewer, I need missing live normalization refs, schema validation
failures, missing field anchors, missing model/tool trace refs, direct
publication attempts, drift repair requirements, and replay mismatch to fail or
enter needs-review deterministically with typed diagnostics.

**Independent Test**: Run all negative schema-extraction fixtures and assert
typed failure or needs-review diagnostics with no published outputs.

## Functional Requirements

- **FR-001**: Core schema extraction runtime MUST receive live normalization
  report refs and normalized objects through explicit inputs; it MUST NOT import
  concrete network, browser, source, model, agent framework, storage, queue, or
  site-specific scraper adapters.
- **FR-002**: Passing reports MUST include live normalization refs; normalized
  document refs; source anchor refs; extraction strategy refs; extraction
  candidate refs; candidate field anchor refs; schema refs; schema validation
  refs; framework-neutral model trace refs; framework-neutral tool trace refs;
  confidence refs; policy refs; command/event/outbox refs; and replay refs.
- **FR-003**: Candidates MUST remain intermediate records. Passing reports MUST
  have no `PublishedOutput`, `OutputManifest`, export, delivery receipt, or
  publication refs.
- **FR-004**: Every candidate field value MUST have an anchor ref. Candidate
  anchor gaps MUST fail with typed diagnostics.
- **FR-005**: Declared schemas and explicitly approved exploratory schemas are
  supported. Unapproved, mismatched, or incomplete schema validation MUST fail
  with typed diagnostics.
- **FR-006**: Model/tool trace refs MUST be framework-neutral VeraCrawl refs,
  not provider-native transcripts or framework-native state.
- **FR-007**: Drift and repair scenarios MUST produce drift signal refs,
  rejection refs, repair recommendation refs, and `needs_review` completion
  rather than a false pass.
- **FR-008**: Replay mismatch, missing live normalization refs, missing
  model/tool trace refs, and direct candidate publication attempts MUST fail
  deterministically.

## Dependencies

- Blocks: 047, 049, 054.
- Requires: 045.

## Completion Gate

Candidates carry strategy refs, schema validation refs, source anchors,
framework-neutral model/tool trace refs, rejection or repair refs when needed,
and replay refs. Candidates cannot be published without later evidence and
verification gates.

## Non-Goals

- Does not publish candidate outputs directly.
- Does not build evidence packets or verification decisions.
- Does not allow model-generated content to replace source evidence.
- Does not couple core to model SDKs, agent frameworks, browser engines, HTTP
  clients, storage clients, queues, export destinations, or site-specific
  scraper modules.
