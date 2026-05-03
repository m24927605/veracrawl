"""Production benchmark and release gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionBenchmarkReleaseFailureType,
)


class ProductionBenchmarkReleaseReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    benchmark_manifest_refs: list[Ref] = Field(default_factory=list)
    authorized_corpus_refs: list[Ref] = Field(default_factory=list)
    benchmark_scenario_refs: list[Ref] = Field(default_factory=list)
    target_runtime_report_ref: Ref | None = None
    source_coverage_report_ref: Ref | None = None
    product_acceptance_report_ref: Ref | None = None
    security_privacy_report_ref: Ref | None = None
    result_publication_export_report_ref: Ref | None = None
    worker_orchestration_runtime_report_ref: Ref | None = None
    ops_replay_observability_runtime_report_ref: Ref | None = None
    source_gate_refs: list[Ref] = Field(default_factory=list)
    processing_gate_refs: list[Ref] = Field(default_factory=list)
    evidence_gate_refs: list[Ref] = Field(default_factory=list)
    verification_gate_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    export_gate_refs: list[Ref] = Field(default_factory=list)
    replay_gate_refs: list[Ref] = Field(default_factory=list)
    ops_gate_refs: list[Ref] = Field(default_factory=list)
    scale_gate_refs: list[Ref] = Field(default_factory=list)
    safety_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    benchmark_run_refs: list[Ref] = Field(default_factory=list)
    slo_metric_refs: list[Ref] = Field(default_factory=list)
    release_decision_refs: list[Ref] = Field(default_factory=list)
    audit_report_refs: list[Ref] = Field(default_factory=list)
    failure_type: ProductionBenchmarkReleaseFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_gate_refs: list[Ref] = Field(default_factory=list)
    slo_violation_refs: list[Ref] = Field(default_factory=list)
    release_blocker_refs: list[Ref] = Field(default_factory=list)
    false_ready_refs: list[Ref] = Field(default_factory=list)
    replay_gap_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    release_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_release_report(self) -> ProductionBenchmarkReleaseReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "benchmark_manifest_refs": self.benchmark_manifest_refs,
                "authorized_corpus_refs": self.authorized_corpus_refs,
                "benchmark_scenario_refs": self.benchmark_scenario_refs,
                "target_runtime_report_ref": self.target_runtime_report_ref,
                "source_coverage_report_ref": self.source_coverage_report_ref,
                "product_acceptance_report_ref": self.product_acceptance_report_ref,
                "security_privacy_report_ref": self.security_privacy_report_ref,
                "result_publication_export_report_ref": (
                    self.result_publication_export_report_ref
                ),
                "worker_orchestration_runtime_report_ref": (
                    self.worker_orchestration_runtime_report_ref
                ),
                "ops_replay_observability_runtime_report_ref": (
                    self.ops_replay_observability_runtime_report_ref
                ),
                "source_gate_refs": self.source_gate_refs,
                "processing_gate_refs": self.processing_gate_refs,
                "evidence_gate_refs": self.evidence_gate_refs,
                "verification_gate_refs": self.verification_gate_refs,
                "publication_gate_refs": self.publication_gate_refs,
                "export_gate_refs": self.export_gate_refs,
                "replay_gate_refs": self.replay_gate_refs,
                "ops_gate_refs": self.ops_gate_refs,
                "scale_gate_refs": self.scale_gate_refs,
                "safety_gate_refs": self.safety_gate_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "redaction_map_refs": self.redaction_map_refs,
                "benchmark_run_refs": self.benchmark_run_refs,
                "slo_metric_refs": self.slo_metric_refs,
                "release_decision_refs": self.release_decision_refs,
                "audit_report_refs": self.audit_report_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_gate_refs
                or self.slo_violation_refs
                or self.release_blocker_refs
                or self.false_ready_refs
                or self.replay_gap_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing production release report missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_gate_refs
                or self.slo_violation_refs
                or self.release_blocker_refs
                or self.false_ready_refs
                or self.replay_gap_refs
                or self.missing_ref_fields
            )
        ):
            raise ValueError("non-pass production release report requires diagnostics")
        return self


class ProductionBenchmarkReleaseFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_release_status: str
    expected_failure_type: ProductionBenchmarkReleaseFailureType | None = None
    negative_case: bool = False
    required_gate_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_release_fixture(self) -> ProductionBenchmarkReleaseFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("production release fixture must support target profile")
        if not self.required_gate_refs:
            raise ValueError("production release fixture must declare required gate refs")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative production release fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative production release fixture requires failure type")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
