"""Field-level oracle extraction benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    FieldOracleFailureType,
    FieldOracleMatchResult,
    FieldOracleValueType,
)


class FieldOracleFieldSpec(TimestampedModel):
    id: str
    schema_ref: Ref
    field_path: str
    value_type: FieldOracleValueType
    match_mode: FieldOracleMatchResult = FieldOracleMatchResult.EXACT
    required: bool = True
    normalization_rule_ref: Ref
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_field_spec(self) -> FieldOracleFieldSpec:
        if not self.field_path:
            raise ValueError("field oracle field_path is required")
        if self.required and not self.evidence_requirement_refs:
            raise ValueError("required field oracle fields need evidence requirements")
        return self


class FieldOracleSchema(TimestampedModel):
    id: str
    schema_name: str
    output_type_ref: Ref
    field_specs: list[FieldOracleFieldSpec] = Field(default_factory=list)
    normalization_rule_refs: list[Ref] = Field(default_factory=list)
    evidence_requirement_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_schema(self) -> FieldOracleSchema:
        if not self.field_specs:
            raise ValueError("field oracle schema requires field specs")
        if not self.normalization_rule_refs or not self.evidence_requirement_refs:
            raise ValueError("field oracle schema requires normalization and evidence refs")
        return self


class ExpectedFieldValue(TimestampedModel):
    id: str
    schema_ref: Ref
    field_path: str
    expected_value: str
    normalized_expected_value: str
    source_target_ref: Ref
    source_anchor_ref: Ref
    artifact_ref: Ref
    content_hash_ref: Ref
    evidence_packet_ref: Ref
    verification_decision_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_expected_value(self) -> ExpectedFieldValue:
        if not self.expected_value or not self.normalized_expected_value:
            raise ValueError("expected field values require raw and normalized values")
        if not self.policy_decision_refs:
            raise ValueError("expected field values require policy refs")
        return self


class FieldEvaluationRecord(TimestampedModel):
    id: str
    schema_ref: Ref
    expected_field_ref: Ref
    field_path: str
    candidate_value: str | None = None
    normalized_candidate_value: str | None = None
    normalized_value_ref: Ref | None = None
    match_result: FieldOracleMatchResult
    accepted: bool = False
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    model_call_refs: list[Ref] = Field(default_factory=list)
    agent_action_refs: list[Ref] = Field(default_factory=list)
    tool_call_refs: list[Ref] = Field(default_factory=list)
    context_bundle_refs: list[Ref] = Field(default_factory=list)
    graph_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)
    publication_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: FieldOracleFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_evaluation(self) -> FieldEvaluationRecord:
        if self.accepted:
            required: dict[str, object] = {
                "candidate_value": self.candidate_value,
                "normalized_candidate_value": self.normalized_candidate_value,
                "normalized_value_ref": self.normalized_value_ref,
                "source_anchor_refs": self.source_anchor_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"accepted field evaluation missing refs: {missing}")
            if self.publication_refs:
                raise ValueError("field oracle evaluation cannot publish directly")
        elif self.completion_result == CompletenessResult.FAIL and not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("failed field evaluation requires typed diagnostics")
        return self


class FieldOracleBenchmarkReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    schema_count: int = 0
    expected_field_count: int = 0
    evaluated_field_count: int = 0
    accepted_field_count: int = 0
    rejected_field_count: int = 0
    exact_match_count: int = 0
    normalized_match_count: int = 0
    acceptable_partial_count: int = 0
    missing_count: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    ambiguous_count: int = 0
    needs_review_count: int = 0
    minimum_schema_count: int = 8
    minimum_expected_field_count: int = 200
    schema_refs: list[Ref] = Field(default_factory=list)
    expected_field_refs: list[Ref] = Field(default_factory=list)
    field_evaluation_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    normalized_value_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    ai_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: FieldOracleFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> FieldOracleBenchmarkReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "schema_refs": self.schema_refs,
                "expected_field_refs": self.expected_field_refs,
                "field_evaluation_refs": self.field_evaluation_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "normalized_value_refs": self.normalized_value_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing field oracle report missing refs: {missing}")
            if self.schema_count < self.minimum_schema_count:
                raise ValueError("field oracle report below schema minimum")
            if self.expected_field_count < self.minimum_expected_field_count:
                raise ValueError("field oracle report below field minimum")
            if self.evaluated_field_count != self.expected_field_count:
                raise ValueError("field oracle report has unevaluated expected fields")
            if self.accepted_field_count != self.expected_field_count:
                raise ValueError("field oracle report has unaccepted expected fields")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass field oracle report requires diagnostics")
        return self


class FieldOracleBenchmarkManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    schema_specs: list[FieldOracleSchema] = Field(default_factory=list)
    expected_fields: list[ExpectedFieldValue] = Field(default_factory=list)
    generated_schema_count: int = 0
    generated_fields_per_schema: int = 0
    minimum_schema_count: int = 8
    minimum_expected_field_count: int = 200
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: FieldOracleFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> FieldOracleBenchmarkManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("field oracle manifest must support quality profile")
        if not self.schema_specs and self.generated_schema_count < 1:
            raise ValueError("field oracle manifest requires schemas or generated schemas")
        if self.generated_schema_count and self.generated_schema_count < 8:
            raise ValueError("generated field oracle manifests require at least 8 schemas")
        if self.generated_fields_per_schema and self.generated_fields_per_schema < 25:
            raise ValueError("generated field oracle manifests require 25 fields per schema")
        if not self.required_ref_types:
            raise ValueError("field oracle manifest requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative field oracle fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative field oracle fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive field oracle fixture must expect pass")
        return self
