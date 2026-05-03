"""Browser snapshot runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.browser.observation import (
    BrowserAcquisitionOutcome,
    browser_policy_failure,
    execute_browser_observation_acquisition,
)
from veracrawl.contracts.browser import (
    BrowserSandboxPolicy,
    BrowserSnapshotRuntimeReport,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    BrowserSideEffectClass,
    BrowserSnapshotFailureType,
    CompletenessResult,
)
from veracrawl.fetch.network_acquisition import url_origin
from veracrawl.ports.browser import BrowserSourceAdapterPort


@dataclass(frozen=True)
class BrowserSnapshotRuntimeResult:
    report: BrowserSnapshotRuntimeReport
    browser_outcome: BrowserAcquisitionOutcome | None = None


_DIRECT_FAILURES: dict[str, tuple[BrowserSnapshotFailureType, str]] = {
    "browser-snapshot-policy-denied": (
        BrowserSnapshotFailureType.POLICY_DENIED,
        "policy_decision_refs",
    ),
    "browser-snapshot-egress-denied": (
        BrowserSnapshotFailureType.EGRESS_DENIED,
        "network_trace_refs",
    ),
    "browser-snapshot-unsafe-interaction": (
        BrowserSnapshotFailureType.UNSAFE_INTERACTION,
        "browser_step_ref",
    ),
    "browser-snapshot-budget-exceeded": (
        BrowserSnapshotFailureType.BUDGET_EXCEEDED,
        "browser_budget_refs",
    ),
    "browser-snapshot-prompt-tainted-content": (
        BrowserSnapshotFailureType.PROMPT_TAINTED_CONTENT,
        "prompt_taint_boundary_refs",
    ),
    "browser-snapshot-missing-artifact": (
        BrowserSnapshotFailureType.MISSING_ARTIFACT,
        "artifact_refs",
    ),
    "browser-snapshot-replay-mismatch": (
        BrowserSnapshotFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_browser_snapshot_runtime(
    *,
    fixture_id: str,
    scenario: str,
    target_url: str,
    adapter: BrowserSourceAdapterPort | None,
    sandbox_policy: BrowserSandboxPolicy,
    side_effect_class: BrowserSideEffectClass,
    live_http_acquisition_report_ref: Ref,
    structured_source_adapters_runtime_report_ref: Ref,
) -> BrowserSnapshotRuntimeResult:
    policy_refs = [f"policy:{fixture_id}:browser-snapshot", *sandbox_policy.allowed_origin_refs]
    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
        )
    if url_origin(target_url) not in sandbox_policy.egress_allowlist:
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.EGRESS_DENIED,
            missing_field="network_trace_refs",
            policy_refs=policy_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
        )
    if browser_policy_failure(
        side_effect_class=side_effect_class,
        sandbox_policy=sandbox_policy,
    ):
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.UNSAFE_INTERACTION,
            missing_field="browser_step_ref",
            policy_refs=policy_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
        )
    if adapter is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.ADAPTER_UNAVAILABLE,
            missing_field="browser_step_ref",
            policy_refs=policy_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
        )

    outcome = execute_browser_observation_acquisition(
        fixture_id=fixture_id,
        scenario="browser-readonly",
        target_url=target_url,
        adapter=adapter,
        sandbox_policy=sandbox_policy,
        side_effect_class=side_effect_class,
    )
    if outcome.report.completion_result != CompletenessResult.PASS:
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.POLICY_DENIED,
            missing_field=outcome.report.operator_status,
            policy_refs=policy_refs + outcome.report.policy_decision_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_outcome=outcome,
        )

    browser_result = outcome.browser_result
    if browser_result is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.MISSING_ARTIFACT,
            missing_field="browser_result",
            policy_refs=policy_refs + outcome.report.policy_decision_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_outcome=outcome,
        )

    step = browser_result.step
    dom_refs = _present([step.dom_artifact_ref])
    screenshot_refs = _present([step.screenshot_artifact_ref])
    network_refs = _present([step.network_log_ref])
    console_refs = [ref for ref in browser_result.artifact_refs if ":console:" in ref]
    timing_refs = [ref for ref in browser_result.artifact_refs if ":timing:" in ref]
    if not (dom_refs and screenshot_refs and network_refs and console_refs and timing_refs):
        return _failure_result(
            fixture_id=fixture_id,
            failure=BrowserSnapshotFailureType.MISSING_ARTIFACT,
            missing_field="artifact_refs",
            policy_refs=policy_refs + outcome.report.policy_decision_refs,
            sandbox_policy_ref=sandbox_policy.id,
            live_http_acquisition_report_ref=live_http_acquisition_report_ref,
            structured_source_adapters_runtime_report_ref=(
                structured_source_adapters_runtime_report_ref
            ),
            browser_outcome=outcome,
        )

    report = BrowserSnapshotRuntimeReport(
        id=f"browser-snapshot-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        structured_source_adapters_runtime_report_ref=(
            structured_source_adapters_runtime_report_ref
        ),
        network_acquisition_report_ref=outcome.report.id,
        source_acquisition_report_ref=outcome.report.source_acquisition_report_ref,
        sandbox_policy_ref=sandbox_policy.id,
        browser_step_ref=step.id,
        dom_artifact_refs=dom_refs,
        screenshot_artifact_refs=screenshot_refs,
        network_trace_refs=network_refs,
        console_log_refs=console_refs,
        timing_refs=timing_refs,
        browser_budget_refs=[f"budget:{fixture_id}:browser-runtime"],
        prompt_taint_boundary_refs=[f"prompt-taint-boundary:{fixture_id}:rendered-content"],
        artifact_refs=sorted(set(outcome.report.artifact_refs + browser_result.artifact_refs)),
        policy_decision_refs=sorted(set(policy_refs + outcome.report.policy_decision_refs)),
        command_record_refs=outcome.report.command_record_refs,
        event_cursor_refs=outcome.report.event_cursor_refs,
        outbox_refs=outcome.report.outbox_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:browser-snapshot",
        operator_status="browser_snapshot_completed",
        completion_result=CompletenessResult.PASS,
    )
    return BrowserSnapshotRuntimeResult(report=report, browser_outcome=outcome)


def _failure_result(
    *,
    fixture_id: str,
    failure: BrowserSnapshotFailureType,
    missing_field: str,
    policy_refs: list[Ref],
    sandbox_policy_ref: Ref | None,
    live_http_acquisition_report_ref: Ref,
    structured_source_adapters_runtime_report_ref: Ref,
    browser_outcome: BrowserAcquisitionOutcome | None = None,
) -> BrowserSnapshotRuntimeResult:
    report = BrowserSnapshotRuntimeReport(
        id=f"browser-snapshot-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        live_http_acquisition_report_ref=live_http_acquisition_report_ref,
        structured_source_adapters_runtime_report_ref=(
            structured_source_adapters_runtime_report_ref
        ),
        network_acquisition_report_ref=browser_outcome.report.id if browser_outcome else None,
        source_acquisition_report_ref=(
            browser_outcome.report.source_acquisition_report_ref if browser_outcome else None
        ),
        sandbox_policy_ref=sandbox_policy_ref,
        policy_decision_refs=sorted(set(policy_refs)),
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=[f"browser snapshot runtime failed: {failure.value}"],
    )
    return BrowserSnapshotRuntimeResult(report=report, browser_outcome=browser_outcome)


def _present(refs: list[Ref | None]) -> list[Ref]:
    return [ref for ref in refs if ref is not None]
