"""Fetch and raw source artifact contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    FetchAttemptStatus,
    FetchResultStatus,
    SourceAdapterResultType,
)


class FetchAttempt(TimestampedModel):
    id: str
    run_ref: Ref
    frontier_item_ref: Ref
    lease_ref: Ref
    adapter_spec_ref: Ref
    source_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    attempt_number: int
    status: FetchAttemptStatus = FetchAttemptStatus.PLANNED
    retry_after_ref: Ref | None = None
    failure_report_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_attempt(self) -> FetchAttempt:
        if self.attempt_number < 1:
            raise ValueError("fetch attempt number must be positive")
        if self.status != FetchAttemptStatus.SUCCEEDED and not (
            self.failure_report_ref or self.retry_after_ref or self.policy_decision_refs
        ):
            raise ValueError("non-success fetch attempt requires policy, retry, or failure refs")
        return self


class FetchResult(TimestampedModel):
    id: str
    attempt_ref: Ref
    source_ref: Ref
    status: FetchResultStatus
    result_type: SourceAdapterResultType
    raw_artifact_refs: list[Ref] = Field(default_factory=list)
    metadata_refs: list[Ref] = Field(default_factory=list)
    failure_report_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_result(self) -> FetchResult:
        if self.status == FetchResultStatus.SUCCEEDED and not self.raw_artifact_refs:
            raise ValueError("successful fetch result requires raw artifact refs")
        if self.status != FetchResultStatus.SUCCEEDED and not self.failure_report_ref:
            raise ValueError("non-success fetch result requires failure_report_ref")
        return self


class PageSnapshot(TimestampedModel):
    id: str
    fetch_result_ref: Ref
    source_ref: Ref
    raw_artifact_ref: Ref
    content_digest: str
    content_type: str
    canonical_ref: Ref
    privacy_classification_ref: Ref

    @model_validator(mode="after")
    def validate_snapshot(self) -> PageSnapshot:
        if not self.raw_artifact_ref or not self.content_digest:
            raise ValueError("page snapshot requires raw artifact and digest")
        return self


class DocumentArtifact(TimestampedModel):
    id: str
    fetch_result_ref: Ref
    source_ref: Ref
    raw_artifact_ref: Ref
    document_type: str
    content_digest: str
    metadata_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_document(self) -> DocumentArtifact:
        if not self.document_type or not self.raw_artifact_ref or not self.content_digest:
            raise ValueError("document artifact requires type, raw artifact, and digest")
        return self
