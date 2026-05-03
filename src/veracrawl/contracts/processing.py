"""Runtime normalization and extraction contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ExtractionCandidateStatus,
    LinkProvenanceStatus,
    LiveNormalizationFailureType,
    PageType,
)


class NormalizedDocument(TimestampedModel):
    id: str
    run_ref: Ref
    source_adapter_result_ref: Ref
    raw_artifact_ref: Ref
    normalized_artifact_ref: Ref
    anchor_map_ref: Ref
    normalization_manifest_ref: Ref
    language_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_refs(self) -> NormalizedDocument:
        if not self.raw_artifact_ref or not self.normalized_artifact_ref or not self.anchor_map_ref:
            raise ValueError("normalized document requires raw, normalized, and anchor refs")
        return self


class ExtractionCandidate(TimestampedModel):
    id: str
    run_ref: Ref
    schema_ref: Ref
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    field_values: dict[str, object] = Field(default_factory=dict)
    field_anchor_refs: dict[str, Ref] = Field(default_factory=dict)
    confidence_refs: list[Ref] = Field(default_factory=list)
    strategy_ref: Ref
    agent_recommendation_ref: Ref | None = None
    status: ExtractionCandidateStatus = ExtractionCandidateStatus.CANDIDATE

    @model_validator(mode="after")
    def validate_candidate(self) -> ExtractionCandidate:
        if not self.normalized_document_refs:
            raise ValueError("extraction candidate requires normalized document refs")
        missing_anchors = [
            field for field in self.field_values if field not in self.field_anchor_refs
        ]
        if missing_anchors:
            raise ValueError(f"candidate fields missing anchors: {missing_anchors}")
        return self


class NormalizationManifest(TimestampedModel):
    id: str
    run_ref: Ref
    raw_artifact_ref: Ref
    normalized_artifact_ref: Ref
    anchor_map_ref: Ref
    parser_ref: Ref
    transformation_version: str
    input_digest: str
    output_digest: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> NormalizationManifest:
        if not self.input_digest or not self.output_digest:
            raise ValueError("normalization manifest requires input and output digests")
        if not self.policy_decision_refs:
            raise ValueError("normalization manifest requires policy decision refs")
        return self


class TextAnchor(TimestampedModel):
    id: str
    normalized_document_ref: Ref
    raw_artifact_ref: Ref
    label: str
    text: str
    normalized_start: int
    normalized_end: int
    selector_ref: Ref

    @model_validator(mode="after")
    def validate_anchor(self) -> TextAnchor:
        if self.normalized_start < 0 or self.normalized_end <= self.normalized_start:
            raise ValueError("text anchor span must be positive")
        if not self.text:
            raise ValueError("text anchor requires text")
        return self


class AnchorMap(TimestampedModel):
    id: str
    normalized_document_ref: Ref
    raw_artifact_ref: Ref
    anchor_refs: list[Ref] = Field(default_factory=list)
    content_digest: str

    @model_validator(mode="after")
    def validate_anchor_map(self) -> AnchorMap:
        if not self.anchor_refs:
            raise ValueError("anchor map requires anchors")
        if not self.content_digest:
            raise ValueError("anchor map requires content digest")
        return self


class LinkProvenance(TimestampedModel):
    id: str
    normalized_document_ref: Ref
    source_url_ref: Ref
    href: str
    anchor_text: str
    anchor_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: LinkProvenanceStatus = LinkProvenanceStatus.DISCOVERED

    @model_validator(mode="after")
    def validate_link(self) -> LinkProvenance:
        if not self.href or not self.anchor_ref:
            raise ValueError("link provenance requires href and anchor")
        if not self.policy_decision_refs:
            raise ValueError("link provenance requires policy refs")
        return self


class PageTypeClassification(TimestampedModel):
    id: str
    normalized_document_ref: Ref
    page_type: PageType
    signal_refs: list[Ref] = Field(default_factory=list)
    confidence_ref: Ref

    @model_validator(mode="after")
    def validate_page_type(self) -> PageTypeClassification:
        if not self.signal_refs or not self.confidence_ref:
            raise ValueError("page type classification requires signals and confidence")
        return self


class SiteModel(TimestampedModel):
    id: str
    run_ref: Ref
    page_type_refs: list[Ref] = Field(default_factory=list)
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    summary_ref: Ref

    @model_validator(mode="after")
    def validate_site_model(self) -> SiteModel:
        if not self.page_type_refs or not self.summary_ref:
            raise ValueError("site model requires page type refs and summary")
        return self


class ExtractionStrategy(TimestampedModel):
    id: str
    run_ref: Ref
    schema_ref: Ref
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    field_names: list[str] = Field(default_factory=list)
    strategy_type: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_strategy(self) -> ExtractionStrategy:
        if not self.normalized_document_refs or not self.field_names:
            raise ValueError("extraction strategy requires docs and fields")
        if not self.policy_decision_refs:
            raise ValueError("extraction strategy requires policy refs")
        return self


class NormalizeExtractReport(TimestampedModel):
    id: str
    run_ref: Ref
    network_acquisition_report_ref: Ref | None = None
    normalized_document_ref: Ref | None = None
    normalization_manifest_ref: Ref | None = None
    anchor_map_ref: Ref | None = None
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    page_type_classification_ref: Ref | None = None
    site_model_ref: Ref | None = None
    extraction_strategy_ref: Ref | None = None
    extraction_candidate_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> NormalizeExtractReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "network_acquisition_report_ref": self.network_acquisition_report_ref,
                "normalized_document_ref": self.normalized_document_ref,
                "normalization_manifest_ref": self.normalization_manifest_ref,
                "anchor_map_ref": self.anchor_map_ref,
                "page_type_classification_ref": self.page_type_classification_ref,
                "site_model_ref": self.site_model_ref,
                "extraction_strategy_ref": self.extraction_strategy_ref,
                "extraction_candidate_ref": self.extraction_candidate_ref,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing process report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError("non-pass process report requires failures or missing refs")
        return self


class LiveNormalizationRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    live_http_acquisition_report_ref: Ref | None = None
    structured_source_adapters_runtime_report_ref: Ref | None = None
    browser_snapshot_runtime_report_ref: Ref | None = None
    normalized_document_refs: list[Ref] = Field(default_factory=list)
    normalization_manifest_refs: list[Ref] = Field(default_factory=list)
    anchor_map_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    link_analysis_refs: list[Ref] = Field(default_factory=list)
    page_type_classification_refs: list[Ref] = Field(default_factory=list)
    site_model_refs: list[Ref] = Field(default_factory=list)
    raw_artifact_refs: list[Ref] = Field(default_factory=list)
    normalized_artifact_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    derived_context_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: LiveNormalizationFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_normalization_report(self) -> LiveNormalizationRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_http_acquisition_report_ref": self.live_http_acquisition_report_ref,
                "structured_source_adapters_runtime_report_ref": (
                    self.structured_source_adapters_runtime_report_ref
                ),
                "browser_snapshot_runtime_report_ref": self.browser_snapshot_runtime_report_ref,
                "normalized_document_refs": self.normalized_document_refs,
                "normalization_manifest_refs": self.normalization_manifest_refs,
                "anchor_map_refs": self.anchor_map_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "link_analysis_refs": self.link_analysis_refs,
                "page_type_classification_refs": self.page_type_classification_refs,
                "site_model_refs": self.site_model_refs,
                "raw_artifact_refs": self.raw_artifact_refs,
                "normalized_artifact_refs": self.normalized_artifact_refs,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
                "derived_context_refs": self.derived_context_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing live normalization report missing refs: {missing}"
                )
        elif not (
            self.failure_type and (self.failure_report_refs or self.missing_ref_fields)
        ):
            raise ValueError("failed live normalization report requires typed diagnostics")
        return self


class LiveNormalizationFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: LiveNormalizationFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_normalization_fixture(self) -> LiveNormalizationFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("live normalization fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("live normalization fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative live normalization fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative live normalization fixture requires failure type")
        return self


class ProcessFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ProcessFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("process fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative process fixture must not expect pass")
        return self
