"""Runtime publication contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    OutputTypeCoverageFailureType,
    PublishedOutputStatus,
    ResultPublicationExportFailureType,
    TargetOutputType,
)

TARGET_OUTPUT_TYPES: frozenset[TargetOutputType] = frozenset(TargetOutputType)

_REQUIRED_TYPE_SPECIFIC_REFS: dict[TargetOutputType, frozenset[str]] = {
    TargetOutputType.RECORD: frozenset({"record_schema_ref", "required_field_refs"}),
    TargetOutputType.TABLE: frozenset({"table_structure_ref", "row_refs", "cell_anchor_refs"}),
    TargetOutputType.DOCUMENT_METADATA: frozenset(
        {"document_artifact_ref", "metadata_field_refs", "section_anchor_refs"}
    ),
    TargetOutputType.DOCUMENT: frozenset(
        {"document_artifact_ref", "normalized_document_ref", "section_anchor_refs"}
    ),
    TargetOutputType.FILE: frozenset(
        {"file_artifact_hash_ref", "mime_type_ref", "privacy_lifecycle_ref"}
    ),
    TargetOutputType.DATASET: frozenset(
        {"dataset_manifest_ref", "dataset_item_refs", "dataset_item_evidence_refs"}
    ),
    TargetOutputType.FACT: frozenset(
        {"fact_key_ref", "fact_verification_ref", "temporal_context_ref"}
    ),
}


class OutputManifest(TimestampedModel):
    id: str
    published_output_ref: Ref
    output_version: str
    schema_refs: list[Ref] = Field(default_factory=list)
    field_evidence_refs: dict[str, Ref] = Field(default_factory=dict)
    evidence_coverage_ref: Ref
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    publication_policy_decision_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    export_lifecycle_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    manifest_hash: str

    @model_validator(mode="after")
    def validate_manifest(self) -> OutputManifest:
        if not self.schema_refs or not self.field_evidence_refs:
            raise ValueError("output manifest requires schema and field evidence refs")
        if not self.verification_decision_refs or not self.publication_policy_decision_refs:
            raise ValueError("output manifest requires verification and publication decisions")
        if not self.manifest_hash:
            raise ValueError("output manifest requires manifest_hash")
        return self


class PublishedOutput(TimestampedModel):
    id: str
    run_ref: Ref
    candidate_ref: Ref
    verification_decision_ref: Ref
    output_manifest_ref: Ref
    status: PublishedOutputStatus = PublishedOutputStatus.PUBLISHED

    @model_validator(mode="after")
    def validate_publication(self) -> PublishedOutput:
        if self.status == PublishedOutputStatus.PUBLISHED and not self.output_manifest_ref:
            raise ValueError("published output requires output_manifest_ref")
        return self


class ResultApiSnapshot(TimestampedModel):
    id: str
    run_ref: Ref
    published_output_refs: list[Ref] = Field(default_factory=list)
    output_manifest_refs: list[Ref] = Field(default_factory=list)
    response_artifact_ref: Ref
    response_schema_ref: Ref
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    response_hash: str

    @model_validator(mode="after")
    def validate_result_api_snapshot(self) -> ResultApiSnapshot:
        if not self.published_output_refs or not self.output_manifest_refs:
            raise ValueError("result API snapshot requires output and manifest refs")
        if not self.response_artifact_ref or not self.response_schema_ref:
            raise ValueError("result API snapshot requires response artifact and schema refs")
        if not self.privacy_lifecycle_refs:
            raise ValueError("result API snapshot requires privacy lifecycle refs")
        if not self.replay_bundle_ref or not self.response_hash:
            raise ValueError("result API snapshot requires replay and hash refs")
        return self


class PublicationReport(TimestampedModel):
    id: str
    run_ref: Ref
    candidate_ref: Ref
    evidence_packet_ref: Ref | None = None
    evidence_manifest_ref: Ref | None = None
    coverage_result_ref: Ref | None = None
    verification_decision_ref: Ref | None = None
    review_decision_ref: Ref | None = None
    publication_policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    published_output_ref: Ref | None = None
    output_manifest_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> PublicationReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "evidence_packet_ref": self.evidence_packet_ref,
                "evidence_manifest_ref": self.evidence_manifest_ref,
                "coverage_result_ref": self.coverage_result_ref,
                "verification_decision_ref": self.verification_decision_ref,
                "review_decision_ref": self.review_decision_ref,
                "publication_policy_decision_refs": self.publication_policy_decision_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "published_output_ref": self.published_output_ref,
                "output_manifest_ref": self.output_manifest_ref,
                "artifact_refs": self.artifact_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing publication report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS:
            if self.published_output_ref or self.output_manifest_ref:
                raise ValueError("non-pass publication report cannot include output refs")
            if not (self.failure_report_refs or self.missing_ref_fields):
                raise ValueError("non-pass publication report requires failures or missing refs")
        return self


class ResultPublicationExportRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    live_evidence_runtime_report_ref: Ref | None = None
    extraction_candidate_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_manifest_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    review_decision_refs: list[Ref] = Field(default_factory=list)
    publication_report_refs: list[Ref] = Field(default_factory=list)
    published_output_refs: list[Ref] = Field(default_factory=list)
    output_manifest_refs: list[Ref] = Field(default_factory=list)
    result_api_snapshot_refs: list[Ref] = Field(default_factory=list)
    export_target_spec_refs: list[Ref] = Field(default_factory=list)
    export_job_refs: list[Ref] = Field(default_factory=list)
    export_attempt_refs: list[Ref] = Field(default_factory=list)
    delivery_receipt_refs: list[Ref] = Field(default_factory=list)
    withdrawal_job_refs: list[Ref] = Field(default_factory=list)
    withdrawal_attempt_refs: list[Ref] = Field(default_factory=list)
    correction_record_refs: list[Ref] = Field(default_factory=list)
    destination_object_mapping_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    direct_export_bypass_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ResultPublicationExportFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_publication_export_report(
        self,
    ) -> ResultPublicationExportRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_evidence_runtime_report_ref": self.live_evidence_runtime_report_ref,
                "extraction_candidate_refs": self.extraction_candidate_refs,
                "evidence_coverage_refs": self.evidence_coverage_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "evidence_manifest_refs": self.evidence_manifest_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "review_decision_refs": self.review_decision_refs,
                "publication_report_refs": self.publication_report_refs,
                "published_output_refs": self.published_output_refs,
                "output_manifest_refs": self.output_manifest_refs,
                "result_api_snapshot_refs": self.result_api_snapshot_refs,
                "export_target_spec_refs": self.export_target_spec_refs,
                "export_job_refs": self.export_job_refs,
                "export_attempt_refs": self.export_attempt_refs,
                "delivery_receipt_refs": self.delivery_receipt_refs,
                "withdrawal_job_refs": self.withdrawal_job_refs,
                "withdrawal_attempt_refs": self.withdrawal_attempt_refs,
                "correction_record_refs": self.correction_record_refs,
                "destination_object_mapping_refs": self.destination_object_mapping_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.direct_export_bypass_refs
            ):
                raise ValueError(
                    f"passing result publication/export report invalid refs: {missing}"
                )
        else:
            if self.failure_type is None:
                raise ValueError("non-pass result publication/export report requires failure type")
            if not (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.direct_export_bypass_refs
            ):
                raise ValueError("non-pass result publication/export report requires diagnostics")
        return self


class OutputTypeCoverageRecord(TimestampedModel):
    id: str
    run_ref: Ref
    output_type: TargetOutputType
    candidate_ref: Ref
    published_output_ref: Ref | None = None
    output_manifest_ref: Ref | None = None
    evidence_packet_ref: Ref | None = None
    evidence_coverage_ref: Ref | None = None
    verification_decision_ref: Ref | None = None
    publication_policy_refs: list[Ref] = Field(default_factory=list)
    source_evidence_refs: list[Ref] = Field(default_factory=list)
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    type_specific_refs: dict[str, Ref] = Field(default_factory=dict)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    diagnostic_graph_refs: list[Ref] = Field(default_factory=list)
    diagnostic_memory_refs: list[Ref] = Field(default_factory=list)
    diagnostic_agent_reasoning_refs: list[Ref] = Field(default_factory=list)
    diagnostic_temporal_kg_refs: list[Ref] = Field(default_factory=list)
    derived_context_as_evidence_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_output_type_coverage(self) -> OutputTypeCoverageRecord:
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "published_output_ref": self.published_output_ref,
                "output_manifest_ref": self.output_manifest_ref,
                "evidence_packet_ref": self.evidence_packet_ref,
                "evidence_coverage_ref": self.evidence_coverage_ref,
                "verification_decision_ref": self.verification_decision_ref,
                "publication_policy_refs": self.publication_policy_refs,
                "source_evidence_refs": self.source_evidence_refs,
                "field_evidence_refs": self.field_evidence_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "artifact_refs": self.artifact_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            required_type_refs = _REQUIRED_TYPE_SPECIFIC_REFS[self.output_type]
            missing.extend(
                sorted(
                    ref_name
                    for ref_name in required_type_refs
                    if ref_name not in self.type_specific_refs
                )
            )
            if (
                missing
                or self.derived_context_as_evidence_refs
                or self.missing_ref_fields
            ):
                raise ValueError(f"passing output type coverage missing refs: {missing}")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not self.missing_ref_fields:
                raise ValueError("needs-review output coverage requires missing refs")
        elif not (self.derived_context_as_evidence_refs or self.missing_ref_fields):
            raise ValueError("failed output coverage requires failure details")
        return self


class OutputTypePublicationGateReport(TimestampedModel):
    id: str
    run_ref: Ref
    coverage_record_refs: list[Ref] = Field(default_factory=list)
    covered_output_types: list[TargetOutputType] = Field(default_factory=list)
    missing_output_types: list[TargetOutputType] = Field(default_factory=list)
    unsupported_output_type_refs: list[Ref] = Field(default_factory=list)
    derived_context_as_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_type_specific_refs: list[Ref] = Field(default_factory=list)
    missing_replay_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    failure_type: OutputTypeCoverageFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_output_type_report(self) -> OutputTypePublicationGateReport:
        if self.completion_result == CompletenessResult.PASS:
            covered = set(self.covered_output_types)
            required: dict[str, object] = {
                "coverage_record_refs": self.coverage_record_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or covered != TARGET_OUTPUT_TYPES
                or self.missing_output_types
                or self.unsupported_output_type_refs
                or self.derived_context_as_evidence_refs
                or self.missing_type_specific_refs
                or self.missing_replay_refs
                or self.missing_ref_fields
                or self.failure_type is not None
            ):
                raise ValueError(f"passing output type report missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review output type report requires review refs")
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_output_types
                or self.unsupported_output_type_refs
                or self.derived_context_as_evidence_refs
                or self.missing_type_specific_refs
                or self.missing_replay_refs
                or self.missing_ref_fields
            )
        ):
            raise ValueError("failed output type report requires typed failure details")
        return self


class OutputTypeCoverageFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: OutputTypeCoverageFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_output_coverage_fixture(self) -> OutputTypeCoverageFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("output coverage fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative output coverage fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self


class ResultPublicationExportFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    schema_ref: Ref
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ResultPublicationExportFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_publication_fixture(self) -> ResultPublicationExportFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("result publication fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("result publication fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative result publication fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative result publication fixture requires failure type")
        return self
