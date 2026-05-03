"""JavaScript browser crawl quality benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    BrowserQualityFailureType,
    BrowserSideEffectClass,
    CompletenessResult,
)


class BrowserQualityTargetSpec(TimestampedModel):
    id: str
    target_url: str
    allowed_origin: str
    robots_url: str | None = None
    http_absent_fragments: list[str] = Field(default_factory=list)
    browser_required_fragments: list[str] = Field(default_factory=list)
    pattern_refs: list[Ref] = Field(default_factory=list)
    sandbox_policy_ref: Ref
    browser_budget_ref: Ref
    max_runtime_ms: int = 5000
    max_network_request_count: int = 40
    side_effect_class: BrowserSideEffectClass = BrowserSideEffectClass.READ_ONLY
    expected_quality_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_target(self) -> BrowserQualityTargetSpec:
        if not self.target_url.startswith(("http://", "https://")):
            raise ValueError("browser quality target_url must be http or https")
        if not self.allowed_origin.startswith(("http://", "https://")):
            raise ValueError("browser quality allowed_origin must be http or https")
        if not self.http_absent_fragments:
            raise ValueError("browser quality target requires HTTP-absent fragments")
        if not self.browser_required_fragments:
            raise ValueError("browser quality target requires browser fragments")
        if not self.pattern_refs:
            raise ValueError("browser quality target requires pattern refs")
        if self.max_runtime_ms < 1 or self.max_network_request_count < 1:
            raise ValueError("browser quality budgets must be positive")
        return self


class BrowserQualityDeltaRecord(TimestampedModel):
    id: str
    target_spec_ref: Ref
    http_missing_fragment_refs: list[Ref] = Field(default_factory=list)
    browser_recovered_fragment_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    quality_gain_count: int = 0
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_delta(self) -> BrowserQualityDeltaRecord:
        if self.quality_gain_count < 0:
            raise ValueError("quality_gain_count cannot be negative")
        if self.completion_result == CompletenessResult.PASS:
            if not (
                self.http_missing_fragment_refs
                and self.browser_recovered_fragment_refs
                and self.source_anchor_refs
                and self.content_hash_refs
                and self.quality_gain_count > 0
            ):
                raise ValueError("passing browser quality delta requires recovered refs")
        elif not self.diagnostics:
            raise ValueError("non-pass browser quality delta requires diagnostics")
        return self


class BrowserQualityObservation(TimestampedModel):
    id: str
    target_spec_ref: Ref
    target_url: str
    live_http_acquisition_report_ref: Ref | None = None
    network_response_ref: Ref | None = None
    http_artifact_refs: list[Ref] = Field(default_factory=list)
    http_content_hash_refs: list[Ref] = Field(default_factory=list)
    browser_step_ref: Ref | None = None
    dom_artifact_refs: list[Ref] = Field(default_factory=list)
    screenshot_artifact_refs: list[Ref] = Field(default_factory=list)
    network_trace_refs: list[Ref] = Field(default_factory=list)
    console_log_refs: list[Ref] = Field(default_factory=list)
    timing_refs: list[Ref] = Field(default_factory=list)
    rendered_content_hash_refs: list[Ref] = Field(default_factory=list)
    browser_artifact_refs: list[Ref] = Field(default_factory=list)
    http_missing_fragment_refs: list[Ref] = Field(default_factory=list)
    recovered_fragment_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    delta_record_ref: Ref | None = None
    sandbox_policy_ref: Ref | None = None
    browser_budget_ref: Ref | None = None
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    browser_wall_time_ms: int = 0
    browser_network_request_count: int = 0
    browser_blocked_request_count: int = 0
    browser_cost_units: int = 0
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: BrowserQualityFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_observation(self) -> BrowserQualityObservation:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_http_acquisition_report_ref": self.live_http_acquisition_report_ref,
                "network_response_ref": self.network_response_ref,
                "http_artifact_refs": self.http_artifact_refs,
                "http_content_hash_refs": self.http_content_hash_refs,
                "browser_step_ref": self.browser_step_ref,
                "dom_artifact_refs": self.dom_artifact_refs,
                "screenshot_artifact_refs": self.screenshot_artifact_refs,
                "network_trace_refs": self.network_trace_refs,
                "console_log_refs": self.console_log_refs,
                "timing_refs": self.timing_refs,
                "rendered_content_hash_refs": self.rendered_content_hash_refs,
                "browser_artifact_refs": self.browser_artifact_refs,
                "http_missing_fragment_refs": self.http_missing_fragment_refs,
                "recovered_fragment_refs": self.recovered_fragment_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "delta_record_ref": self.delta_record_ref,
                "sandbox_policy_ref": self.sandbox_policy_ref,
                "browser_budget_ref": self.browser_budget_ref,
                "prompt_taint_boundary_refs": self.prompt_taint_boundary_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.browser_wall_time_ms < 1
                or self.browser_network_request_count < 1
                or self.browser_cost_units < 1
            ):
                raise ValueError(
                    f"passing browser quality observation missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass browser quality observation requires diagnostics")
        return self


class BrowserQualityReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    observation_refs: list[Ref] = Field(default_factory=list)
    delta_record_refs: list[Ref] = Field(default_factory=list)
    target_count: int = 0
    browser_required_pass_count: int = 0
    recovered_fragment_count: int = 0
    http_only_missing_count: int = 0
    budget_exceeded_count: int = 0
    unsafe_blocked_count: int = 0
    prompt_taint_blocked_count: int = 0
    artifact_missing_count: int = 0
    replay_missing_count: int = 0
    dom_artifact_refs: list[Ref] = Field(default_factory=list)
    screenshot_artifact_refs: list[Ref] = Field(default_factory=list)
    network_trace_refs: list[Ref] = Field(default_factory=list)
    console_log_refs: list[Ref] = Field(default_factory=list)
    timing_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    browser_budget_refs: list[Ref] = Field(default_factory=list)
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: BrowserQualityFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> BrowserQualityReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "observation_refs": self.observation_refs,
                "delta_record_refs": self.delta_record_refs,
                "dom_artifact_refs": self.dom_artifact_refs,
                "screenshot_artifact_refs": self.screenshot_artifact_refs,
                "network_trace_refs": self.network_trace_refs,
                "console_log_refs": self.console_log_refs,
                "timing_refs": self.timing_refs,
                "content_hash_refs": self.content_hash_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "browser_budget_refs": self.browser_budget_refs,
                "prompt_taint_boundary_refs": self.prompt_taint_boundary_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing browser quality report missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass browser quality report requires diagnostics")
        return self


class BrowserQualityCorpusManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    target_specs: list[BrowserQualityTargetSpec] = Field(default_factory=list)
    minimum_browser_required_count: int = 8
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: BrowserQualityFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> BrowserQualityCorpusManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("browser quality corpus must support quality profile")
        if not self.target_specs:
            raise ValueError("browser quality corpus requires targets")
        if self.minimum_browser_required_count < 8:
            raise ValueError("browser quality minimum must be at least 8")
        if not self.required_ref_types:
            raise ValueError("browser quality corpus requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative browser quality corpus cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative browser quality corpus requires failure type")
        return self
