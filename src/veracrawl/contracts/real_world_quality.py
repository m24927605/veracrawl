"""Expanded real-world public corpus quality benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldQualityCorpusFailureType,
)
from veracrawl.contracts.real_world_benchmark import RealWorldBenchmarkSiteSpec


class RealWorldQualityTargetSpec(RealWorldBenchmarkSiteSpec):
    pattern_family_refs: list[Ref] = Field(default_factory=list)
    quality_tier: str = "quality"
    expected_quality_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_quality_target(self) -> RealWorldQualityTargetSpec:
        if not self.pattern_family_refs:
            raise ValueError("quality target requires pattern_family_refs")
        if self.quality_tier not in {"smoke", "quality", "release"}:
            raise ValueError("quality_tier must be smoke, quality, or release")
        if not set(self.pattern_refs).intersection(self.pattern_family_refs):
            raise ValueError("quality target pattern refs must overlap pattern family refs")
        return self


class RealWorldQualitySiteObservation(TimestampedModel):
    id: str
    target_spec_ref: Ref
    site_observation_ref: Ref | None = None
    target_url: str
    pattern_family_refs: list[Ref] = Field(default_factory=list)
    matched_observation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldQualityCorpusFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_quality_observation(self) -> RealWorldQualitySiteObservation:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "site_observation_ref": self.site_observation_ref,
                "pattern_family_refs": self.pattern_family_refs,
                "matched_observation_refs": self.matched_observation_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(
                    f"passing real-world quality observation missing refs: {missing}"
                )
        elif not (self.failure_type and self.failure_report_refs and self.diagnostics):
            raise ValueError("non-pass real-world quality observation requires diagnostics")
        return self


class RealWorldQualityPatternCoverageRecord(TimestampedModel):
    id: str
    pattern_family_ref: Ref
    declared_target_refs: list[Ref] = Field(default_factory=list)
    passing_target_refs: list[Ref] = Field(default_factory=list)
    failed_target_refs: list[Ref] = Field(default_factory=list)
    site_observation_refs: list[Ref] = Field(default_factory=list)
    quality_observation_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_pattern_coverage(self) -> RealWorldQualityPatternCoverageRecord:
        if not self.declared_target_refs:
            raise ValueError("pattern coverage requires declared targets")
        if self.completion_result == CompletenessResult.PASS and not self.passing_target_refs:
            raise ValueError("passing pattern coverage requires passing targets")
        if self.completion_result != CompletenessResult.PASS and not self.diagnostics:
            raise ValueError("non-pass pattern coverage requires diagnostics")
        return self


class RealWorldQualityCorpusReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    real_world_benchmark_run_report_ref: Ref | None = None
    quality_observation_refs: list[Ref] = Field(default_factory=list)
    pattern_coverage_refs: list[Ref] = Field(default_factory=list)
    site_observation_refs: list[Ref] = Field(default_factory=list)
    passing_target_count: int = 0
    declared_target_count: int = 0
    origin_count: int = 0
    pattern_family_count: int = 0
    policy_denied_count: int = 0
    network_unavailable_count: int = 0
    drift_count: int = 0
    replay_missing_count: int = 0
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldQualityCorpusFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_quality_report(self) -> RealWorldQualityCorpusReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "real_world_benchmark_run_report_ref": self.real_world_benchmark_run_report_ref,
                "quality_observation_refs": self.quality_observation_refs,
                "pattern_coverage_refs": self.pattern_coverage_refs,
                "site_observation_refs": self.site_observation_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type
                or self.failure_report_refs
                or self.replay_missing_count
            ):
                raise ValueError(f"passing real-world quality report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass real-world quality report requires diagnostics")
        return self


class RealWorldQualityCorpusManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    target_specs: list[RealWorldQualityTargetSpec] = Field(default_factory=list)
    allowed_origin_refs: list[Ref] = Field(default_factory=list)
    rate_budget_ref: Ref
    minimum_target_count: int = 40
    minimum_origin_count: int = 15
    minimum_pattern_family_count: int = 10
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: RealWorldQualityCorpusFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_quality_manifest(self) -> RealWorldQualityCorpusManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("real-world quality corpus must support quality profile")
        if not self.target_specs:
            raise ValueError("real-world quality corpus requires target specs")
        if not self.allowed_origin_refs:
            raise ValueError("real-world quality corpus requires allowed origins")
        if self.minimum_target_count < 40:
            raise ValueError("quality profile minimum_target_count must be at least 40")
        if self.minimum_origin_count < 15:
            raise ValueError("quality profile minimum_origin_count must be at least 15")
        if self.minimum_pattern_family_count < 10:
            raise ValueError(
                "quality profile minimum_pattern_family_count must be at least 10"
            )
        allowed = set(self.allowed_origin_refs)
        missing_origins = [
            target.allowed_origin
            for target in self.target_specs
            if target.allowed_origin not in allowed
        ]
        if missing_origins:
            raise ValueError(f"quality target origins missing from allowlist: {missing_origins}")
        if not self.required_ref_types:
            raise ValueError("real-world quality corpus requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative real-world quality corpus cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative real-world quality corpus requires failure type")
        return self
