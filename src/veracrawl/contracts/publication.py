"""Runtime publication contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import PublishedOutputStatus


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
