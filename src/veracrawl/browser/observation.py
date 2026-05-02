"""Browser observation runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.browser import BrowserInteractionStep, BrowserSandboxPolicy
from veracrawl.contracts.enums import (
    AdapterType,
    BrowserSideEffectClass,
    BrowserStepStatus,
    CompletenessResult,
    NetworkFailureType,
)
from veracrawl.contracts.network import NetworkAcquisitionReport
from veracrawl.fetch.acquisition import execute_source_acquisition
from veracrawl.ports.browser import BrowserObservationResult, BrowserSourceAdapterPort


@dataclass(frozen=True)
class BrowserAcquisitionOutcome:
    report: NetworkAcquisitionReport
    browser_result: BrowserObservationResult | None = None


def build_browser_sandbox_policy(*, fixture_id: str, origin: str) -> BrowserSandboxPolicy:
    return BrowserSandboxPolicy(
        id=f"browser-sandbox:{fixture_id}",
        allowed_origin_refs=[f"origin:{origin}"],
        egress_allowlist=[origin],
        private_network_denylist=["private", "link_local", "multicast", "unspecified"],
        max_runtime_ms=1000,
        max_dom_bytes=65536,
        max_screenshot_bytes=65536,
        max_network_log_bytes=65536,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
        capture_dom=True,
        capture_screenshot=True,
        capture_network_log=True,
    )


def browser_policy_failure(
    *,
    side_effect_class: BrowserSideEffectClass,
    sandbox_policy: BrowserSandboxPolicy,
) -> NetworkFailureType | None:
    if side_effect_class not in sandbox_policy.allowed_side_effect_classes:
        return NetworkFailureType.UNSAFE_BROWSER_SIDE_EFFECT
    return None


def _blocked_step(
    *,
    fixture_id: str,
    target_url: str,
    side_effect_class: BrowserSideEffectClass,
    sandbox_policy: BrowserSandboxPolicy,
    failure_type: NetworkFailureType,
) -> BrowserInteractionStep:
    return BrowserInteractionStep(
        id=f"browser-step:{fixture_id}:blocked",
        run_ref=f"run:{fixture_id}",
        source_ref=target_url,
        target_url=target_url,
        step_number=1,
        action_type="observe",
        side_effect_class=side_effect_class,
        sandbox_policy_ref=sandbox_policy.id,
        policy_decision_refs=[f"policy:{fixture_id}:browser"],
        status=BrowserStepStatus.BLOCKED,
        failure_report_ref=f"network-failure:{fixture_id}:{failure_type.value}",
    )


def execute_browser_observation_acquisition(
    *,
    fixture_id: str,
    scenario: str,
    target_url: str,
    adapter: BrowserSourceAdapterPort,
    sandbox_policy: BrowserSandboxPolicy,
    side_effect_class: BrowserSideEffectClass,
) -> BrowserAcquisitionOutcome:
    policy_refs = [f"policy:{fixture_id}:browser"]
    failure = browser_policy_failure(
        side_effect_class=side_effect_class,
        sandbox_policy=sandbox_policy,
    )
    if failure is not None or scenario == "browser-unsafe-side-effect":
        failure_type = failure or NetworkFailureType.UNSAFE_BROWSER_SIDE_EFFECT
        step = _blocked_step(
            fixture_id=fixture_id,
            target_url=target_url,
            side_effect_class=side_effect_class,
            sandbox_policy=sandbox_policy,
            failure_type=failure_type,
        )
        report = NetworkAcquisitionReport(
            id=f"network-acquisition:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            browser_step_ref=step.id,
            policy_decision_refs=policy_refs,
            failure_report_refs=[step.failure_report_ref or f"network-failure:{fixture_id}"],
            missing_ref_fields=[failure_type.value],
            operator_status=failure_type.value,
            completion_result=CompletenessResult.FAIL,
        )
        return BrowserAcquisitionOutcome(report=report)

    source_outcome = execute_source_acquisition(
        fixture_id=fixture_id,
        adapter_type=AdapterType.BROWSER_SNAPSHOT,
        scenario="browser-readonly",
        adapter=adapter,
    )
    browser_result = adapter.last_result
    if browser_result is None:
        report = NetworkAcquisitionReport(
            id=f"network-acquisition:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            source_acquisition_report_ref=source_outcome.report.id,
            policy_decision_refs=policy_refs,
            failure_report_refs=[
                f"network-failure:{fixture_id}:{NetworkFailureType.MISSING_NETWORK_ARTIFACT.value}"
            ],
            missing_ref_fields=[NetworkFailureType.MISSING_NETWORK_ARTIFACT.value],
            operator_status=NetworkFailureType.MISSING_NETWORK_ARTIFACT.value,
            completion_result=CompletenessResult.FAIL,
        )
        return BrowserAcquisitionOutcome(report=report)

    report = NetworkAcquisitionReport(
        id=f"network-acquisition:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        network_request_ref=f"browser-request:{fixture_id}",
        browser_step_ref=browser_result.step.id,
        source_acquisition_report_ref=source_outcome.report.id,
        artifact_refs=sorted(
            set(source_outcome.report.artifact_refs + browser_result.artifact_refs)
        ),
        policy_decision_refs=sorted(set(policy_refs + source_outcome.report.policy_decision_refs)),
        command_record_refs=source_outcome.report.command_record_refs,
        event_cursor_refs=source_outcome.report.event_cursor_refs,
        outbox_refs=source_outcome.report.outbox_refs,
        recovery_report_refs=source_outcome.report.recovery_report_refs,
        operator_status="browser_observed",
        completion_result=CompletenessResult.PASS,
    )
    return BrowserAcquisitionOutcome(report=report, browser_result=browser_result)
