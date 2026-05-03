"""Browser observation contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    BrowserSnapshotFailureType,
    BrowserStepStatus,
    CompletenessResult,
)


class BrowserSandboxPolicy(TimestampedModel):
    id: str
    allowed_origin_refs: list[Ref] = Field(default_factory=list)
    egress_allowlist: list[str] = Field(default_factory=list)
    private_network_denylist: list[str] = Field(default_factory=list)
    max_runtime_ms: int
    max_dom_bytes: int
    max_screenshot_bytes: int
    max_network_log_bytes: int
    allowed_side_effect_classes: list[BrowserSideEffectClass] = Field(default_factory=list)
    capture_dom: bool = True
    capture_screenshot: bool = True
    capture_network_log: bool = True

    @model_validator(mode="after")
    def validate_policy(self) -> BrowserSandboxPolicy:
        if not self.allowed_origin_refs or not self.egress_allowlist:
            raise ValueError("browser sandbox policy requires allowed origins and egress allowlist")
        budgets = [
            self.max_runtime_ms,
            self.max_dom_bytes,
            self.max_screenshot_bytes,
            self.max_network_log_bytes,
        ]
        if any(value < 1 for value in budgets):
            raise ValueError("browser sandbox budgets must be positive")
        if BrowserSideEffectClass.READ_ONLY not in self.allowed_side_effect_classes:
            raise ValueError("browser sandbox must allow read-only observation")
        return self


class BrowserInteractionStep(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    target_url: str
    step_number: int
    action_type: str
    side_effect_class: BrowserSideEffectClass
    sandbox_policy_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    dom_artifact_ref: Ref | None = None
    screenshot_artifact_ref: Ref | None = None
    network_log_ref: Ref | None = None
    status: BrowserStepStatus
    failure_report_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_step(self) -> BrowserInteractionStep:
        if self.step_number < 1:
            raise ValueError("browser step number must be positive")
        if not self.policy_decision_refs:
            raise ValueError("browser step requires policy decisions")
        if self.status == BrowserStepStatus.EXECUTED:
            if self.side_effect_class != BrowserSideEffectClass.READ_ONLY:
                raise ValueError("only read-only browser steps can execute in this slice")
            has_artifacts = (
                self.dom_artifact_ref
                and self.screenshot_artifact_ref
                and self.network_log_ref
            )
            if not has_artifacts:
                raise ValueError("executed browser step requires DOM, screenshot, and network refs")
        if self.status in {BrowserStepStatus.BLOCKED, BrowserStepStatus.FAILED}:
            if not self.failure_report_ref:
                raise ValueError("blocked or failed browser step requires failure report ref")
        return self


class BrowserSnapshotRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    live_http_acquisition_report_ref: Ref | None = None
    structured_source_adapters_runtime_report_ref: Ref | None = None
    network_acquisition_report_ref: Ref | None = None
    source_acquisition_report_ref: Ref | None = None
    sandbox_policy_ref: Ref | None = None
    browser_step_ref: Ref | None = None
    dom_artifact_refs: list[Ref] = Field(default_factory=list)
    screenshot_artifact_refs: list[Ref] = Field(default_factory=list)
    network_trace_refs: list[Ref] = Field(default_factory=list)
    console_log_refs: list[Ref] = Field(default_factory=list)
    timing_refs: list[Ref] = Field(default_factory=list)
    browser_budget_refs: list[Ref] = Field(default_factory=list)
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: BrowserSnapshotFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_browser_snapshot_report(self) -> BrowserSnapshotRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_http_acquisition_report_ref": self.live_http_acquisition_report_ref,
                "structured_source_adapters_runtime_report_ref": (
                    self.structured_source_adapters_runtime_report_ref
                ),
                "network_acquisition_report_ref": self.network_acquisition_report_ref,
                "source_acquisition_report_ref": self.source_acquisition_report_ref,
                "sandbox_policy_ref": self.sandbox_policy_ref,
                "browser_step_ref": self.browser_step_ref,
                "dom_artifact_refs": self.dom_artifact_refs,
                "screenshot_artifact_refs": self.screenshot_artifact_refs,
                "network_trace_refs": self.network_trace_refs,
                "console_log_refs": self.console_log_refs,
                "timing_refs": self.timing_refs,
                "browser_budget_refs": self.browser_budget_refs,
                "prompt_taint_boundary_refs": self.prompt_taint_boundary_refs,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
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
            ):
                raise ValueError(
                    f"passing browser snapshot report missing refs: {missing}"
                )
        elif not (
            self.failure_type and (self.failure_report_refs or self.missing_ref_fields)
        ):
            raise ValueError("failed browser snapshot report requires typed diagnostics")
        return self


class BrowserSnapshotFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str = "/browser"
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: BrowserSnapshotFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_browser_snapshot_fixture(self) -> BrowserSnapshotFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("browser snapshot fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("browser snapshot fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative browser snapshot fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative browser snapshot fixture requires failure type")
        return self
