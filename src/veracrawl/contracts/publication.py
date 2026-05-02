"""Runtime publication contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, PublishedOutputStatus


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
