# Research: Field-Level Oracle Extraction Benchmark

## Decision: Generated Schema Oracles For Stable Coverage

Use manifest-declared generated schema counts for the positive quality corpus:
8 schemas with 25 expected fields each. Explicit schema/field specs remain
supported by the contracts, but generation keeps fixture data compact and
deterministic.

Rationale: row 061 must prove field-level mechanics, evidence refs, replay, and
typed diagnostics without turning into a single-site extractor.

## Decision: Accepted Fields Need Source Evidence And Verification

Every accepted `FieldEvaluationRecord` must carry source anchors, artifact refs,
content hash refs, normalized value refs, evidence packet refs, verification
decision refs, policy refs, command/event/outbox refs, and replay refs.

Rejected: allowing model/graph/memory refs to satisfy evidence. They can explain
candidate proposals but cannot replace source-backed evidence.

## Decision: Field Results Are Typed For Later Metrics

Field outcomes use exact, normalized-match, acceptable-partial, missing,
false-positive, false-negative, ambiguous, rejected, and needs-review values.
Row 062 can compute precision/recall from these records without re-running
extraction.

## Decision: Negative Fixtures Fail At Report Level With Typed Diagnostics

Wrong value, missing anchor, schema violation, stale evidence, publication
bypass, and LLM-as-evidence fixtures fail with typed `FieldOracleFailureType`
values and do not emit false pass status.
