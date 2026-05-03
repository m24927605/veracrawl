# Data Model: Field-Level Oracle Extraction Benchmark

## FieldOracleSchema

Declares a general-purpose output schema.

- `id`, `schema_name`, `output_type_ref`
- `field_specs`
- `normalization_rule_refs`, `evidence_requirement_refs`

Validation: schemas require at least one field spec.

## FieldOracleFieldSpec

Declares one field path and matching rule.

- `id`, `schema_ref`, `field_path`, `value_type`, `match_mode`
- `required`, `normalization_rule_ref`

Validation: required fields must have normalization and evidence requirements.

## ExpectedFieldValue

Defines one oracle field value.

- `id`, `schema_ref`, `field_path`, `expected_value`,
  `normalized_expected_value`
- `source_anchor_ref`, `artifact_ref`, `content_hash_ref`,
  `evidence_packet_ref`, `verification_decision_ref`

Validation: expected values must be source-backed and cannot use model output as
evidence.

## FieldEvaluationRecord

Records one extracted candidate against one expected field.

- candidate value and normalized value
- match result, accepted flag, diagnostics
- source anchors, artifacts, content hashes, normalized value refs, evidence
  packets, verification decisions
- model/agent/tool/context refs when a candidate was proposed by AI
- policy, command, event cursor, outbox, replay refs

Validation: accepted records require all source evidence and replay refs.
LLM-only evidence records fail or are rejected.

## FieldOracleBenchmarkReport

Aggregates schema and field-level quality.

- schema count, expected/evaluated/accepted/rejected counts
- exact, normalized, partial, missing, false-positive, false-negative,
  ambiguous, needs-review counts
- field evaluation refs, expected field refs, schema refs, evidence refs,
  verification refs, policy refs, command/event/outbox refs, replay refs
- failure type and diagnostics

Validation: pass requires at least 8 schemas and 200 expected fields evaluated,
with accepted fields fully source-backed.
