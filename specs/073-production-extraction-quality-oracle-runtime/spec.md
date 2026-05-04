# Feature Specification: Production Extraction Quality And Oracle Runtime

**Feature Branch**: `073-production-extraction-quality-oracle-runtime`  
**Created**: 2026-05-04  
**Status**: Implemented
**Roadmap Row**: 073  
**Input**: Production-grade closure requirement: extraction quality gates must block release and publication, not merely report benchmark numbers.

## Summary

Turn field-level oracles, precision/recall metrics, confidence calibration,
abstention, verification, and publication gating into a production quality
runtime. The runtime must decide whether extracted outputs are releasable and
must block publication when evidence or quality thresholds are insufficient.

## User Scenarios

1. Given a production crawl output, VeraCrawl evaluates every published field
   against source anchors, evidence packets, verification decisions, schema
   validators, freshness, and confidence thresholds.
2. Given a corpus with oracles, VeraCrawl computes precision, recall, F1,
   false-positive, false-negative, unsupported-field, abstention, and
   source-limited rates by schema, site, pattern, and critical field.
3. Given low confidence, stale evidence, contradictory evidence, or source
   limitation, VeraCrawl abstains or escalates to review instead of publishing.

## Functional Requirements

- **FR-001**: System MUST define `ProductionQualityGate`,
  `FieldOracleEvaluation`, `FieldConfusionRecord`, `ConfidenceCalibrationSlice`,
  `AbstentionDecision`, and `PublicationReadinessDecision` contracts.
- **FR-002**: System MUST require source anchors, artifacts, content hashes,
  evidence packets, verification decisions, policy refs, and replay refs for
  every accepted field.
- **FR-003**: System MUST compute quality metrics by corpus, site, source type,
  page pattern, schema, field, criticality, and acquisition mode.
- **FR-004**: System MUST enforce default thresholds of precision >= 0.98,
  recall >= 0.90, F1 >= 0.94, and critical-field precision >= 0.99 unless a
  spec-approved stricter threshold exists.
- **FR-005**: System MUST treat model output, graph data, memory, search
  snippets, and framework-native state as non-evidence.
- **FR-006**: System MUST block publication/release when thresholds, anchors,
  verification, freshness, or replay are missing.

## Required Tests

- Unit/contract tests for quality gates, confusion records, abstention, and
  publication readiness.
- Positive corpus with at least eight schemas and 200 fields.
- Negative cases for wrong values, missing anchors, stale evidence,
  contradictory evidence, LLM-as-evidence, low precision, low recall, low
  critical-field precision, missing replay, and publication bypass.
- Live crawl output quality validation from 072.

## Completion Gate

Production outputs cannot publish or count toward production-grade release until
quality gates pass with source-backed evidence and release-blocking metrics.
