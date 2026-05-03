from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    FieldOracleMatchResult,
    FieldOracleValueType,
)
from veracrawl.contracts.field_oracle import (
    ExpectedFieldValue,
    FieldEvaluationRecord,
    FieldOracleBenchmarkManifest,
    FieldOracleBenchmarkReport,
    FieldOracleFieldSpec,
    FieldOracleSchema,
)


def _field_spec() -> FieldOracleFieldSpec:
    return FieldOracleFieldSpec(
        id="schema:field",
        schema_ref="schema:1",
        field_path="$.title",
        value_type=FieldOracleValueType.TEXT,
        normalization_rule_ref="normalization:text",
        evidence_requirement_refs=["evidence:source-anchor"],
    )


def _expected() -> ExpectedFieldValue:
    return ExpectedFieldValue(
        id="expected:1",
        schema_ref="schema:1",
        field_path="$.title",
        expected_value="Hello",
        normalized_expected_value="hello",
        source_target_ref="source:1",
        source_anchor_ref="anchor:1",
        artifact_ref="artifact:1",
        content_hash_ref="hash:1",
        evidence_packet_ref="evidence:1",
        verification_decision_ref="verification:1",
        policy_decision_refs=["policy:1"],
    )


def test_field_oracle_schema_requires_field_specs() -> None:
    schema = FieldOracleSchema(
        id="schema:1",
        schema_name="Schema 1",
        output_type_ref="output-type:record",
        field_specs=[_field_spec()],
        normalization_rule_refs=["normalization:text"],
        evidence_requirement_refs=["evidence:source-anchor"],
    )

    assert schema.field_specs[0].field_path == "$.title"


def test_required_field_spec_requires_evidence_requirement_refs() -> None:
    with pytest.raises(ValidationError):
        FieldOracleFieldSpec(
            id="schema:field",
            schema_ref="schema:1",
            field_path="$.title",
            value_type=FieldOracleValueType.TEXT,
            normalization_rule_ref="normalization:text",
            evidence_requirement_refs=[],
        )


def test_accepted_field_evaluation_requires_source_evidence_and_replay() -> None:
    expected = _expected()
    evaluation = FieldEvaluationRecord(
        id="evaluation:1",
        schema_ref=expected.schema_ref,
        expected_field_ref=expected.id,
        field_path=expected.field_path,
        candidate_value=expected.expected_value,
        normalized_candidate_value=expected.normalized_expected_value,
        normalized_value_ref="normalized:1",
        match_result=FieldOracleMatchResult.EXACT,
        accepted=True,
        source_anchor_refs=[expected.source_anchor_ref],
        artifact_refs=[expected.artifact_ref],
        content_hash_refs=[expected.content_hash_ref],
        evidence_packet_refs=[expected.evidence_packet_ref],
        verification_decision_refs=[expected.verification_decision_ref],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:1",
    )

    assert evaluation.accepted is True


def test_accepted_field_evaluation_cannot_publish_directly() -> None:
    expected = _expected()
    with pytest.raises(ValidationError):
        FieldEvaluationRecord(
            id="evaluation:1",
            schema_ref=expected.schema_ref,
            expected_field_ref=expected.id,
            field_path=expected.field_path,
            candidate_value=expected.expected_value,
            normalized_candidate_value=expected.normalized_expected_value,
            normalized_value_ref="normalized:1",
            match_result=FieldOracleMatchResult.EXACT,
            accepted=True,
            source_anchor_refs=[expected.source_anchor_ref],
            artifact_refs=[expected.artifact_ref],
            content_hash_refs=[expected.content_hash_ref],
            evidence_packet_refs=[expected.evidence_packet_ref],
            verification_decision_refs=[expected.verification_decision_ref],
            publication_refs=["published:1"],
            policy_decision_refs=["policy:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_ref="replay:1",
        )


def test_field_oracle_report_requires_schema_and_field_minimums() -> None:
    report = FieldOracleBenchmarkReport(
        id="report:1",
        fixture_id="field-oracle-quality-corpus",
        run_ref="run:1",
        schema_count=8,
        expected_field_count=200,
        evaluated_field_count=200,
        accepted_field_count=200,
        exact_match_count=200,
        schema_refs=["schema:1"],
        expected_field_refs=["expected:1"],
        field_evaluation_refs=["evaluation:1"],
        source_anchor_refs=["anchor:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["hash:1"],
        normalized_value_refs=["normalized:1"],
        evidence_packet_refs=["evidence:1"],
        verification_decision_refs=["verification:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay:1"],
        operator_status="field_oracle_completed",
        completion_result=CompletenessResult.PASS,
    )

    assert report.accepted_field_count == 200


def test_field_oracle_manifest_supports_generated_quality_corpus() -> None:
    manifest = FieldOracleBenchmarkManifest(
        id="field-oracle-quality-corpus",
        scenario="field-oracle-quality-corpus",
        profile_refs=["quality"],
        generated_schema_count=8,
        generated_fields_per_schema=25,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="field_oracle_completed",
        required_ref_types=["schema", "field"],
    )

    assert manifest.generated_schema_count == 8
