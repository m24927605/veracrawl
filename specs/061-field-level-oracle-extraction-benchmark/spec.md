# Feature Specification: Field-Level Oracle Extraction Benchmark

**Feature Branch**: `061-field-level-oracle-extraction-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Move from coarse extraction candidate existence to field-level quality proof.

## Constitution Alignment

- **General-purpose crawler impact**: Evaluates multiple schemas and website
  patterns without hard-coding per-site extractors.
- **Target/V1 boundary**: Quality benchmark after corpus and deep crawl coverage;
  it does not compute final precision/recall release metrics by itself.
- **Evidence and replay impact**: Every accepted field requires source anchors,
  artifacts, content hashes, normalized value refs, evidence packet refs,
  verification refs, command/event/outbox refs, and replay refs.
- **Safety and policy impact**: Model-generated values are candidate proposals
  only. Publication requires source-backed evidence and verification gates.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`,
  `specs/046-schema-extraction-candidate-runtime/spec.md`,
  `specs/047-live-evidence-verification-runtime/spec.md`,
  `specs/048-result-publication-export-runtime/spec.md`,
  `specs/058-expanded-real-world-corpus-benchmark/spec.md`, and
  `specs/060-multi-page-deep-crawl-frontier-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Evaluate Field-Level Expected Values (Priority: P1)

An operator can compare extracted fields with schema-specific oracle values and
see exact, normalized, partial, missing, and rejected outcomes.

**Independent Test**: Run `veracrawl-field-oracle-benchmark run
tests/fixtures/field-oracle-quality-corpus --profile quality --out
.veracrawl-real-runs/field-oracle-quality-corpus`.

**Acceptance Scenarios**:

1. **Given** a schema with expected fields, **When** extraction runs, **Then**
   every accepted field has an oracle match result and source-backed evidence.
2. **Given** a field value proposed only by a model response, **When** validation
   runs, **Then** the field is rejected as LLM-output-as-evidence.

### User Story 2 - Validate Normalization Rules (Priority: P2)

Maintainers can verify dates, prices, units, counts, URLs, whitespace, and text
normalization consistently.

**Independent Test**: Run normalization mismatch fixtures for each field type.

### User Story 3 - Explain Mismatches (Priority: P3)

Failed fields must produce useful typed diagnostics for later repair specs.

**Independent Test**: Negative fixtures cover wrong value, missing anchor,
ambiguous field, stale evidence, schema violation, and publication bypass.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define field oracle schemas, expected field records,
  field evaluation records, normalized value refs, and field oracle reports.
- **FR-002**: Quality profile MUST include at least 8 schemas and at least 200
  expected field values across public and deterministic fixtures.
- **FR-003**: System MUST classify field results as exact, normalized-match,
  acceptable-partial, missing, false-positive, false-negative, ambiguous,
  rejected, or needs-review.
- **FR-004**: System MUST require source anchors, artifacts, content hashes,
  evidence packet refs, verification decisions, command/event/outbox refs, and
  replay refs for every accepted field.
- **FR-005**: System MUST fail or reject fields whose only support is model,
  graph, memory, or framework-native state.
- **FR-006**: System MUST write field-level JSON reports suitable for precision
  and recall computation in spec 062.

### VeraCrawl Contract Requirements

- **VC-001**: Extraction remains schema-driven and general-purpose, not
  website-specific scraper code.
- **VC-002**: Field evaluation records must have owner-service, command, event,
  typed failure, policy, and replay refs.
- **VC-003**: Publication behavior must remain gated by evidence and
  verification; direct candidate publication is forbidden.
- **VC-004**: Privacy, retention, redaction, prompt-injection, credential, and
  export/withdrawal boundaries must be explicit for field artifacts.
- **VC-005**: Include contract, unit, fixture/oracle, negative, replay,
  import-boundary, focused, full, Docker-backed, and live validation tests.

### Key Entities

- **FieldOracleSchema**: Declares output type, fields, normalization rules,
  matching mode, and evidence requirements.
- **ExpectedFieldValue**: One oracle value with source target, field path,
  normalized expectation, tolerance, and anchor expectation.
- **FieldEvaluationRecord**: One extracted field's candidate value, evidence,
  match result, diagnostics, and replay refs.
- **FieldOracleBenchmarkReport**: Aggregate field-level pass/fail/needs-review
  results for later metrics.

### Non-Goals

- This spec does not define corpus-level precision/recall thresholds, repair
  success, or operational cost/stability gates.
- It does not allow LLM output, graph memory, or screenshots without source
  anchors to become field evidence.

## Success Criteria

- **SC-001**: At least 8 schemas and 200 expected fields are evaluated.
- **SC-002**: 100% of accepted fields have source anchors, artifacts, hashes,
  evidence packets, verification refs, and replay refs.
- **SC-003**: Wrong value, missing anchor, schema violation, stale evidence,
  direct publication, and LLM-as-evidence fail with typed diagnostics.
- **SC-004**: Validation results are recorded in `tasks.md`.

## Assumptions

- Field oracles may include deterministic local fixtures for stable exact values
  and public targets for live drift-aware validation.
