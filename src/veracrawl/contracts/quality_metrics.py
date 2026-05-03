"""Precision/recall quality metric contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityMetricConfusionClass,
    QualityMetricFailureType,
    QualityMetricSliceDimension,
)


class QualityMetricThresholds(TimestampedModel):
    id: str
    version_ref: Ref = "quality-thresholds:v1"
    min_precision: float = 0.98
    min_recall: float = 0.90
    min_f1: float = 0.94
    min_critical_field_precision: float = 0.99

    @model_validator(mode="after")
    def validate_thresholds(self) -> QualityMetricThresholds:
        for name in [
            "min_precision",
            "min_recall",
            "min_f1",
            "min_critical_field_precision",
        ]:
            value = getattr(self, name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be between 0 and 1")
        return self


class FieldConfusionRecord(TimestampedModel):
    id: str
    field_evaluation_ref: Ref
    schema_ref: Ref
    website_pattern_ref: Ref
    source_type_ref: Ref
    rendering_mode_ref: Ref
    confidence_bucket_ref: Ref
    confusion_class: QualityMetricConfusionClass
    critical_field: bool = False
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    model_only_evidence: bool = False
    publication_bypass: bool = False
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_confusion(self) -> FieldConfusionRecord:
        required = {
            "evidence_packet_refs": self.evidence_packet_refs,
            "publication_gate_refs": self.publication_gate_refs,
            "artifact_refs": self.artifact_refs,
            "content_hash_refs": self.content_hash_refs,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"field confusion record missing refs: {missing}")
        if self.confusion_class == QualityMetricConfusionClass.TRUE_POSITIVE and (
            self.model_only_evidence or self.publication_bypass
        ):
            raise ValueError("unsafe field confusion record cannot be true positive")
        return self


class PrecisionRecallSliceMetric(TimestampedModel):
    id: str
    dimension: QualityMetricSliceDimension
    slice_ref: Ref
    true_positive_count: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    true_negative_count: int = 0
    abstain_count: int = 0
    unsupported_count: int = 0
    needs_review_count: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    abstention_rate: float = 0.0
    unsupported_rate: float = 0.0
    needs_review_rate: float = 0.0
    field_confusion_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_slice(self) -> PrecisionRecallSliceMetric:
        counts = [
            self.true_positive_count,
            self.false_positive_count,
            self.false_negative_count,
            self.true_negative_count,
            self.abstain_count,
            self.unsupported_count,
            self.needs_review_count,
        ]
        if any(value < 0 for value in counts):
            raise ValueError("quality metric counts cannot be negative")
        for name in [
            "precision",
            "recall",
            "f1",
            "false_positive_rate",
            "false_negative_rate",
            "abstention_rate",
            "unsupported_rate",
            "needs_review_rate",
        ]:
            value = getattr(self, name)
            if value < 0 or value > 1:
                raise ValueError(f"{name} must be between 0 and 1")
        return self


class PrecisionRecallQualityReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    thresholds_ref: Ref
    corpus_metric_ref: Ref | None = None
    slice_metric_refs: list[Ref] = Field(default_factory=list)
    field_confusion_refs: list[Ref] = Field(default_factory=list)
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    critical_field_precision: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    abstention_rate: float = 0.0
    unsupported_rate: float = 0.0
    needs_review_rate: float = 0.0
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: QualityMetricFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> PrecisionRecallQualityReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "corpus_metric_ref": self.corpus_metric_ref,
                "slice_metric_refs": self.slice_metric_refs,
                "field_confusion_refs": self.field_confusion_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "publication_gate_refs": self.publication_gate_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing quality metric report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass quality metric report requires diagnostics")
        return self


class QualityMetricManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    generated_true_positive_count: int = 250
    generated_false_positive_count: int = 2
    generated_false_negative_count: int = 10
    generated_true_negative_count: int = 40
    generated_abstain_count: int = 5
    generated_unsupported_count: int = 4
    generated_needs_review_count: int = 3
    critical_true_positive_count: int = 200
    critical_false_positive_count: int = 1
    thresholds: QualityMetricThresholds = Field(
        default_factory=lambda: QualityMetricThresholds(id="quality-thresholds:default")
    )
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: QualityMetricFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> QualityMetricManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("quality metric manifest must support quality profile")
        if not self.required_ref_types:
            raise ValueError("quality metric manifest requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative quality metric fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative quality metric fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive quality metric fixture must expect pass")
        return self
