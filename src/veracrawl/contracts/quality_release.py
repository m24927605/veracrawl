"""Cost, latency, stability quality release contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityReleaseDecision,
    QualityReleaseFailureType,
    QualityReleaseGateType,
)


class QualityReleaseThresholds(TimestampedModel):
    id: str
    version_ref: Ref = "quality-release-thresholds:v1"
    required_quality_gate_count: int = 6
    min_stability_run_count: int = 3
    max_total_cost_usd: float = 2.50
    max_p95_latency_ms: int = 5000
    min_throughput_pages_per_minute: float = 30.0
    max_retry_rate: float = 0.10
    max_token_count: int = 250000
    max_model_call_count: int = 500
    max_stability_variance: float = 0.05

    @model_validator(mode="after")
    def validate_thresholds(self) -> QualityReleaseThresholds:
        if self.required_quality_gate_count < 1 or self.min_stability_run_count < 1:
            raise ValueError("quality release count thresholds must be positive")
        for name in [
            "max_total_cost_usd",
            "min_throughput_pages_per_minute",
            "max_retry_rate",
            "max_stability_variance",
        ]:
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.max_p95_latency_ms < 1:
            raise ValueError("max_p95_latency_ms must be positive")
        return self


class QualityReleaseGateRef(TimestampedModel):
    id: str
    gate_type: QualityReleaseGateType
    report_ref: Ref
    completion_result: CompletenessResult
    replay_bundle_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_gate_ref(self) -> QualityReleaseGateRef:
        required = {
            "report_ref": self.report_ref,
            "replay_bundle_ref": self.replay_bundle_ref,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"quality release gate ref missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS:
            raise ValueError("quality release gate ref must reference a passing gate")
        return self


class QualityReleaseStabilityRun(TimestampedModel):
    id: str
    run_ref: Ref
    total_cost_usd: float
    p95_latency_ms: int
    throughput_pages_per_minute: float
    retry_rate: float
    token_count: int
    model_call_count: int
    successful: bool = True
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    slo_metric_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_stability_run(self) -> QualityReleaseStabilityRun:
        if (
            self.total_cost_usd < 0
            or self.p95_latency_ms < 0
            or self.throughput_pages_per_minute < 0
            or self.retry_rate < 0
            or self.token_count < 0
            or self.model_call_count < 0
        ):
            raise ValueError("quality release stability metrics cannot be negative")
        required = {
            "run_ref": self.run_ref,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "slo_metric_refs": self.slo_metric_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"quality release stability run missing refs: {missing}")
        return self


class QualityReleaseReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    thresholds_ref: Ref
    quality_gate_refs: list[Ref] = Field(default_factory=list)
    stability_run_refs: list[Ref] = Field(default_factory=list)
    required_quality_gate_count: int = 0
    observed_quality_gate_count: int = 0
    stability_run_count: int = 0
    total_cost_usd: float = 0.0
    p95_latency_ms: int = 0
    throughput_pages_per_minute: float = 0.0
    retry_rate: float = 0.0
    token_count: int = 0
    model_call_count: int = 0
    stability_variance: float = 0.0
    gate_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    slo_metric_refs: list[Ref] = Field(default_factory=list)
    audit_report_refs: list[Ref] = Field(default_factory=list)
    release_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: QualityReleaseFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    release_decision: QualityReleaseDecision
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> QualityReleaseReport:
        for name in ["total_cost_usd", "throughput_pages_per_minute", "retry_rate"]:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "quality_gate_refs": self.quality_gate_refs,
                "stability_run_refs": self.stability_run_refs,
                "gate_report_refs": self.gate_report_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "slo_metric_refs": self.slo_metric_refs,
                "audit_report_refs": self.audit_report_refs,
                "release_decision_refs": self.release_decision_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.release_decision != QualityReleaseDecision.RELEASE_READY
            ):
                raise ValueError(f"passing quality release report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass quality release report requires diagnostics")
        return self


class QualityReleaseManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    thresholds: QualityReleaseThresholds = Field(
        default_factory=lambda: QualityReleaseThresholds(
            id="quality-release-thresholds:default"
        )
    )
    expected_completion_result: CompletenessResult
    expected_release_decision: QualityReleaseDecision
    expected_failure_type: QualityReleaseFailureType | None = None
    negative_case: bool = False
    required_gate_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> QualityReleaseManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("quality release manifest must support quality profile")
        if not self.required_gate_refs:
            raise ValueError("quality release manifest requires prior gate refs")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative quality release fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative quality release fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive quality release fixture must expect pass")
        return self
