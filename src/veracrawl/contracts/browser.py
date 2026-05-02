"""Browser observation contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import BrowserSideEffectClass, BrowserStepStatus


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
