# Feature Specification: Precision Recall Quality Benchmark

**Feature Branch**: `062-precision-recall-quality-benchmark`  
**Created**: 2026-05-03  
**Status**: Planned  
**Roadmap Source**: `specs/057-production-quality-benchmark-roadmap/spec.md`  
**Input**: Compute crawl/extraction precision, recall, F1, and error taxonomy from field-level oracles.

## Constitution Alignment

- **General-purpose crawler impact**: Measures quality across schemas, website
  patterns, and source types instead of optimizing one site.
- **Target/V1 boundary**: Metric layer after field-level oracle extraction; it
  does not run repairs or final operational release by itself.
- **Evidence and replay impact**: Metrics must link back to field evaluations,
  evidence packets, publication gates, artifacts, command/event/outbox refs, and
  replay bundles.
- **Safety and policy impact**: Metrics must not reward unsafe publication,
  policy bypass, model-only evidence, or hidden false positives.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, and
  `specs/061-field-level-oracle-extraction-benchmark/spec.md`.

## User Scenarios & Testing

### User Story 1 - Compute Corpus Precision Recall F1 (Priority: P1)

An operator can run one metric command and receive corpus-level and per-pattern
precision, recall, F1, abstention, unsupported-field, false-positive, and
false-negative metrics.

**Independent Test**: Run `veracrawl-quality-metrics run
tests/fixtures/precision-recall-quality --profile quality --out
.veracrawl-real-runs/precision-recall-quality`.

**Acceptance Scenarios**:

1. **Given** field-level benchmark reports, **When** metrics run, **Then** the
   report computes TP, FP, FN, TN/abstention where applicable, precision, recall,
   F1, and confidence calibration by schema and pattern.
2. **Given** a false-positive publication, **When** metrics run, **Then** it is
   counted and cannot be hidden by abstention or needs-review labels.

### User Story 2 - Enforce Release-Blocking Thresholds (Priority: P2)

Maintainers can fail the benchmark when quality falls below thresholds.

**Independent Test**: Threshold fixtures cover global and per-pattern failures.

### User Story 3 - Preserve Abstention Honesty (Priority: P3)

The crawler should be allowed to abstain on unsupported or uncertain fields, but
that must be visible and bounded.

**Independent Test**: Abstention fixtures verify unsupported, low-confidence,
missing-evidence, and policy-denied outcomes.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `QualityMetricManifest`,
  `QualityMetricThresholds`, `FieldConfusionRecord`, and
  `PrecisionRecallQualityReport`.
- **FR-002**: System MUST compute precision, recall, F1, false-positive rate,
  false-negative rate, abstention rate, unsupported-field rate, and
  needs-review rate.
- **FR-003**: Default quality thresholds MUST require corpus precision >= 0.98,
  corpus recall >= 0.90, corpus F1 >= 0.94, and per-critical-field precision >=
  0.99 unless amended by a spec change.
- **FR-004**: System MUST report metrics by schema, website pattern, source
  type, rendering mode, and confidence bucket.
- **FR-005**: System MUST link every metric component to field evaluation refs,
  evidence refs, publication gate refs, command/event/outbox refs, and replay
  refs.
- **FR-006**: System MUST fail if direct publication, LLM-as-evidence,
  evidence-missing, or replay-missing cases are included as true positives.

### VeraCrawl Contract Requirements

- **VC-001**: Metrics are evaluator contracts and must not encode one-site
  parsing assumptions.
- **VC-002**: Metric reports must have owner-service, command, event, outbox,
  policy, typed failure, and replay refs.
- **VC-003**: Publication correctness is evaluated only through evidence-backed
  field outputs.
- **VC-004**: Privacy and redaction must protect source excerpts while preserving
  anchor/hash references for audit.
- **VC-005**: Include metric math unit tests, fixture/oracle tests, negative
  threshold tests, replay tests, focused/full/Docker validation.

### Key Entities

- **FieldConfusionRecord**: Maps a field evaluation to TP/FP/FN/abstain/
  unsupported/needs-review with supporting refs.
- **PrecisionRecallQualityReport**: Aggregates metrics and threshold decisions.
- **QualityMetricThresholds**: Versioned thresholds used by release gates.

### Non-Goals

- This spec does not perform repairs, crawl more pages, or change extraction
  behavior. It evaluates reports from earlier specs.
- Metrics must not be tuned by silently dropping hard cases.

## Success Criteria

- **SC-001**: Quality metric reports compute global and per-slice precision,
  recall, F1, false-positive, false-negative, abstention, unsupported, and
  needs-review metrics.
- **SC-002**: Default thresholds fail below 0.98 precision, 0.90 recall, or 0.94
  F1 unless amended.
- **SC-003**: Metric components are fully traceable to evidence, publication,
  command/event/outbox, and replay refs.
- **SC-004**: Validation results are recorded in `tasks.md`.

## Assumptions

- Thresholds may evolve only through explicit spec amendments with recorded
  rationale; runtime code cannot silently lower them.
