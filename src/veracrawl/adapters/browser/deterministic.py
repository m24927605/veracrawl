"""Deterministic browser observation adapter."""

from __future__ import annotations

from veracrawl.contracts.browser import BrowserInteractionStep, BrowserSandboxPolicy
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    BrowserSideEffectClass,
    BrowserStepStatus,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.browser import BrowserObservationResult


class DeterministicBrowserObservationAdapter:
    def __init__(
        self,
        *,
        fixture_id: str,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
        side_effect_class: BrowserSideEffectClass = BrowserSideEffectClass.READ_ONLY,
    ) -> None:
        self.fixture_id = fixture_id
        self.target_url = target_url
        self.sandbox_policy = sandbox_policy
        self.side_effect_class = side_effect_class
        self._last_result: BrowserObservationResult | None = None

    @property
    def last_result(self) -> BrowserObservationResult | None:
        return self._last_result

    def observe(
        self,
        *,
        run_ref: Ref,
        source_ref: Ref,
        target_url: str,
        sandbox_policy: BrowserSandboxPolicy,
    ) -> BrowserObservationResult:
        digest = stable_hash({"fixture": self.fixture_id, "url": target_url})
        dom_ref = f"artifact:{self.fixture_id}:dom:{digest[:12]}"
        screenshot_ref = f"artifact:{self.fixture_id}:screenshot:{digest[:12]}"
        network_ref = f"artifact:{self.fixture_id}:browser-network:{digest[:12]}"
        console_ref = f"artifact:{self.fixture_id}:console:{digest[:12]}"
        timing_ref = f"artifact:{self.fixture_id}:timing:{digest[:12]}"
        step = BrowserInteractionStep(
            id=f"browser-step:{self.fixture_id}:1",
            run_ref=run_ref,
            source_ref=source_ref,
            target_url=target_url,
            step_number=1,
            action_type="observe",
            side_effect_class=self.side_effect_class,
            sandbox_policy_ref=sandbox_policy.id,
            policy_decision_refs=[f"policy:{self.fixture_id}:browser"],
            dom_artifact_ref=dom_ref,
            screenshot_artifact_ref=screenshot_ref,
            network_log_ref=network_ref,
            status=BrowserStepStatus.EXECUTED,
        )
        return BrowserObservationResult(
            step=step,
            artifact_refs=[dom_ref, screenshot_ref, network_ref, console_ref, timing_ref],
        )

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        result = self.observe(
            run_ref=f"run:{self.fixture_id}",
            source_ref=command.source_ref,
            target_url=self.target_url,
            sandbox_policy=self.sandbox_policy,
        )
        self._last_result = result
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:browser-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.BROWSER_SNAPSHOT,
            result_type=SourceAdapterResultType.BROWSER_SNAPSHOT,
            output_refs=[result.step.dom_artifact_ref or result.artifact_refs[0]],
            policy_decision_refs=result.step.policy_decision_refs,
            replay_event_refs=[f"event:{command.command_envelope_id}:browser_step_executed"],
            idempotency_key=f"{command.adapter_spec.id}:{self.fixture_id}",
            status=AdapterResultStatus.SUCCEEDED,
        )
