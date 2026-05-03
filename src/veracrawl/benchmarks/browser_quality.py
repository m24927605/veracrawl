"""JavaScript browser crawl quality benchmark runtime."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from veracrawl.browser.observation import execute_browser_observation_acquisition
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.browser_quality import (
    BrowserQualityCorpusManifest,
    BrowserQualityDeltaRecord,
    BrowserQualityObservation,
    BrowserQualityReport,
    BrowserQualityTargetSpec,
)
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    BrowserQualityFailureType,
    BrowserSideEffectClass,
    CompletenessResult,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.ports.browser import BrowserObservationResult, BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort

NetworkAdapterFactory = Callable[
    [str, BrowserQualityTargetSpec], NetworkSourceAdapterPort
]
BrowserAdapterFactory = Callable[
    [str, BrowserQualityTargetSpec, BrowserSandboxPolicy],
    BrowserSourceAdapterPort | None,
]


@dataclass(frozen=True)
class BrowserQualityCorpusResult:
    report: BrowserQualityReport
    observations: list[BrowserQualityObservation]
    deltas: list[BrowserQualityDeltaRecord]


_DIRECT_FAILURES: dict[str, tuple[BrowserQualityFailureType, str]] = {
    "browser-quality-unsafe-action": (
        BrowserQualityFailureType.UNSAFE_ACTION,
        "browser_step_ref",
    ),
    "browser-quality-prompt-taint": (
        BrowserQualityFailureType.PROMPT_TAINT_BYPASS,
        "prompt_taint_boundary_refs",
    ),
    "browser-quality-missing-artifact": (
        BrowserQualityFailureType.MISSING_ARTIFACT,
        "dom_artifact_refs",
    ),
    "browser-quality-budget-exceeded": (
        BrowserQualityFailureType.BUDGET_EXCEEDED,
        "browser_budget_ref",
    ),
    "browser-quality-replay-mismatch": (
        BrowserQualityFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_browser_quality_corpus(
    *,
    manifest: BrowserQualityCorpusManifest,
    profile: str,
    store: ProductionPersistenceStore,
    http_adapter_factory: NetworkAdapterFactory,
    browser_adapter_factory: BrowserAdapterFactory,
) -> BrowserQualityCorpusResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"browser quality corpus {manifest.id} does not support {profile}")

    observations: list[BrowserQualityObservation] = []
    deltas: list[BrowserQualityDeltaRecord] = []
    for target in manifest.target_specs:
        observation, delta = _run_target(
            manifest=manifest,
            target=target,
            profile=profile,
            store=store,
            http_adapter_factory=http_adapter_factory,
            browser_adapter_factory=browser_adapter_factory,
        )
        if delta is not None:
            delta = _record_delta_event(manifest.id, delta, store)
            deltas.append(delta)
            observation = observation.model_copy(update={"delta_record_ref": delta.id})
        observation = _record_observation_event(manifest.id, observation, store)
        observations.append(observation)

    report = _build_report(manifest=manifest, observations=observations, deltas=deltas)
    store.save_canonical_model("browser_quality_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("browser_quality_reports", report.id, report)
    return BrowserQualityCorpusResult(report=report, observations=observations, deltas=deltas)


def _run_target(
    *,
    manifest: BrowserQualityCorpusManifest,
    target: BrowserQualityTargetSpec,
    profile: str,
    store: ProductionPersistenceStore,
    http_adapter_factory: NetworkAdapterFactory,
    browser_adapter_factory: BrowserAdapterFactory,
) -> tuple[BrowserQualityObservation, BrowserQualityDeltaRecord | None]:
    target_run_id = f"{manifest.id}:{target.id}"
    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=failure,
                missing=[missing],
                diagnostics=[f"browser quality blocked by scenario: {failure.value}"],
            ),
            None,
        )

    sandbox = _sandbox_policy(target_run_id, target)
    try:
        http_adapter = http_adapter_factory(target_run_id, target)
        live = execute_live_http_acquisition(
            fixture_id=f"{target_run_id}:http",
            scenario="success",
            target_url=target.target_url,
            store=store,
            adapter=http_adapter,
            profile=profile,
            egress_allowlist=[target.allowed_origin],
            allow_private_network=False,
            size_budget_bytes=131072,
            timeout_ms=target.max_runtime_ms,
        )
    except Exception as exc:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.ADAPTER_UNAVAILABLE,
                missing=["live_http_acquisition_report_ref"],
                diagnostics=[f"HTTP adapter failed for {target.id}: {exc}"],
            ),
            None,
        )
    if (
        live.report.completion_result != CompletenessResult.PASS
        or live.network_outcome is None
        or live.network_outcome.network_result is None
    ):
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.POLICY_DENIED,
                missing=live.report.missing_ref_fields or ["network_response_ref"],
                diagnostics=live.report.diagnostics
                or [f"HTTP prerequisite failed for {target.id}"],
                live_http_ref=live.report.id,
                policy_refs=live.report.policy_decision_refs,
                failure_refs=live.report.failure_report_refs,
            ),
            None,
    )

    http_result = live.network_outcome.network_result
    http_content_hash = http_result.response.content_digest
    if http_content_hash is None:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.MISSING_ARTIFACT,
                missing=["http_content_hash_refs"],
                diagnostics=[f"HTTP response missing content hash for {target.id}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                policy_refs=live.report.policy_decision_refs,
            ),
            None,
        )
    http_present = [
        fragment for fragment in target.http_absent_fragments if fragment in http_result.body_text
    ]
    if http_present:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.HTTP_ORACLE_NOT_MISSING,
                missing=["http_absent_fragments"],
                diagnostics=[
                    f"HTTP-only evidence already contained browser-required fragments: "
                    f"{http_present}"
                ],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                policy_refs=live.report.policy_decision_refs,
            ),
            None,
        )

    try:
        browser_adapter = browser_adapter_factory(target_run_id, target, sandbox)
        if browser_adapter is None:
            raise ValueError("browser adapter factory returned None")
        browser = execute_browser_observation_acquisition(
            fixture_id=f"{target_run_id}:browser",
            scenario="browser-readonly",
            target_url=target.target_url,
            adapter=browser_adapter,
            sandbox_policy=sandbox,
            side_effect_class=target.side_effect_class,
        )
    except Exception as exc:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.ADAPTER_UNAVAILABLE,
                missing=["browser_step_ref"],
                diagnostics=[f"browser adapter failed for {target.id}: {exc}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                policy_refs=live.report.policy_decision_refs,
            ),
            None,
        )
    if browser.report.completion_result != CompletenessResult.PASS:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.POLICY_DENIED,
                missing=browser.report.missing_ref_fields or ["browser_step_ref"],
                diagnostics=browser.report.missing_ref_fields
                or [f"browser observation failed for {target.id}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                policy_refs=live.report.policy_decision_refs + browser.report.policy_decision_refs,
                failure_refs=browser.report.failure_report_refs,
            ),
            None,
        )
    browser_result = browser.browser_result
    if browser_result is None:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.MISSING_ARTIFACT,
                missing=["browser_result"],
                diagnostics=[f"browser observation returned no result for {target.id}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                policy_refs=live.report.policy_decision_refs + browser.report.policy_decision_refs,
            ),
            None,
        )
    missing_browser_fragments = [
        fragment
        for fragment in target.browser_required_fragments
        if fragment not in browser_result.dom_text
    ]
    if missing_browser_fragments:
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.BROWSER_ORACLE_NOT_RECOVERED,
                missing=["browser_required_fragments"],
                diagnostics=[
                    f"browser DOM did not recover required fragments: "
                    f"{missing_browser_fragments}"
                ],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                browser_result=browser_result,
                policy_refs=live.report.policy_decision_refs + browser.report.policy_decision_refs,
            ),
            None,
        )
    if (
        browser_result.wall_time_ms > target.max_runtime_ms
        or browser_result.network_request_count > target.max_network_request_count
    ):
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.BUDGET_EXCEEDED,
                missing=["browser_budget_ref"],
                diagnostics=[f"browser budget exceeded for {target.id}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                browser_result=browser_result,
                policy_refs=live.report.policy_decision_refs + browser.report.policy_decision_refs,
            ),
            None,
        )

    artifact_parts = _browser_artifact_parts(browser_result)
    if any(not refs for refs in artifact_parts.values()):
        return (
            _failure_observation(
                manifest_id=manifest.id,
                target=target,
                failure=BrowserQualityFailureType.MISSING_ARTIFACT,
                missing=[name for name, refs in artifact_parts.items() if not refs],
                diagnostics=[f"browser artifact refs missing for {target.id}"],
                live_http_ref=live.report.id,
                network_response_ref=http_result.response.id,
                http_artifacts=http_result.artifact_refs,
                http_hashes=[http_content_hash],
                browser_result=browser_result,
                policy_refs=live.report.policy_decision_refs + browser.report.policy_decision_refs,
            ),
            None,
        )

    http_missing_refs = [
        _fragment_ref("http-missing", target.id, item)
        for item in target.http_absent_fragments
    ]
    recovered_refs = [
        _fragment_ref("browser-recovered", target.id, item)
        for item in target.browser_required_fragments
    ]
    anchor_refs = [
        _fragment_ref("source-anchor", target.id, item)
        for item in target.browser_required_fragments
    ]
    rendered_hash = browser_result.dom_content_hash or stable_hash(browser_result.dom_text)
    content_hash_refs = [http_content_hash, rendered_hash]
    delta = BrowserQualityDeltaRecord(
        id=f"browser-quality-delta:{manifest.id}:{target.id}",
        target_spec_ref=target.id,
        http_missing_fragment_refs=http_missing_refs,
        browser_recovered_fragment_refs=recovered_refs,
        source_anchor_refs=anchor_refs,
        content_hash_refs=content_hash_refs,
        quality_gain_count=len(recovered_refs),
        completion_result=CompletenessResult.PASS,
    )
    observation = BrowserQualityObservation(
        id=f"browser-quality-observation:{manifest.id}:{target.id}",
        target_spec_ref=target.id,
        target_url=target.target_url,
        live_http_acquisition_report_ref=live.report.id,
        network_response_ref=http_result.response.id,
        http_artifact_refs=http_result.artifact_refs,
        http_content_hash_refs=[http_content_hash],
        browser_step_ref=browser_result.step.id,
        dom_artifact_refs=artifact_parts["dom_artifact_refs"],
        screenshot_artifact_refs=artifact_parts["screenshot_artifact_refs"],
        network_trace_refs=artifact_parts["network_trace_refs"],
        console_log_refs=artifact_parts["console_log_refs"],
        timing_refs=artifact_parts["timing_refs"],
        rendered_content_hash_refs=[rendered_hash],
        browser_artifact_refs=browser_result.artifact_refs,
        http_missing_fragment_refs=http_missing_refs,
        recovered_fragment_refs=recovered_refs,
        source_anchor_refs=anchor_refs,
        delta_record_ref=delta.id,
        sandbox_policy_ref=sandbox.id,
        browser_budget_ref=target.browser_budget_ref,
        prompt_taint_boundary_refs=[f"prompt-taint-boundary:{target_run_id}:rendered-dom"],
        policy_decision_refs=sorted(
            set(live.report.policy_decision_refs + browser.report.policy_decision_refs)
        ),
        command_record_refs=sorted(
            set(live.report.command_record_refs + browser.report.command_record_refs)
        ),
        event_cursor_refs=sorted(
            set(live.report.event_cursor_refs + browser.report.event_cursor_refs)
        ),
        outbox_refs=sorted(set(live.report.outbox_refs + browser.report.outbox_refs)),
        replay_bundle_ref=f"replay-bundle:{target_run_id}:browser-quality",
        browser_wall_time_ms=browser_result.wall_time_ms,
        browser_network_request_count=browser_result.network_request_count,
        browser_blocked_request_count=browser_result.blocked_request_count,
        browser_cost_units=max(1, browser_result.wall_time_ms // 1000 + 1),
        completion_result=CompletenessResult.PASS,
    )
    return observation, delta


def _sandbox_policy(
    target_run_id: str,
    target: BrowserQualityTargetSpec,
) -> BrowserSandboxPolicy:
    del target_run_id
    return BrowserSandboxPolicy(
        id=target.sandbox_policy_ref,
        allowed_origin_refs=[f"origin:{target.allowed_origin}"],
        egress_allowlist=[target.allowed_origin],
        private_network_denylist=["private", "link_local", "multicast", "unspecified"],
        max_runtime_ms=target.max_runtime_ms,
        max_dom_bytes=262144,
        max_screenshot_bytes=524288,
        max_network_log_bytes=262144,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
        capture_dom=True,
        capture_screenshot=True,
        capture_network_log=True,
    )


def _failure_observation(
    *,
    manifest_id: str,
    target: BrowserQualityTargetSpec,
    failure: BrowserQualityFailureType,
    missing: list[str],
    diagnostics: list[str],
    live_http_ref: Ref | None = None,
    network_response_ref: Ref | None = None,
    http_artifacts: list[Ref] | None = None,
    http_hashes: list[Ref] | None = None,
    browser_result: BrowserObservationResult | None = None,
    policy_refs: list[Ref] | None = None,
    failure_refs: list[Ref] | None = None,
) -> BrowserQualityObservation:
    artifacts = _browser_artifact_parts(browser_result) if browser_result else {}
    return BrowserQualityObservation(
        id=f"browser-quality-observation:{manifest_id}:{target.id}",
        target_spec_ref=target.id,
        target_url=target.target_url,
        live_http_acquisition_report_ref=live_http_ref,
        network_response_ref=network_response_ref,
        http_artifact_refs=http_artifacts or [],
        http_content_hash_refs=http_hashes or [],
        browser_step_ref=browser_result.step.id if browser_result else None,
        dom_artifact_refs=artifacts.get("dom_artifact_refs", []),
        screenshot_artifact_refs=artifacts.get("screenshot_artifact_refs", []),
        network_trace_refs=artifacts.get("network_trace_refs", []),
        console_log_refs=artifacts.get("console_log_refs", []),
        timing_refs=artifacts.get("timing_refs", []),
        rendered_content_hash_refs=[browser_result.dom_content_hash]
        if browser_result and browser_result.dom_content_hash
        else [],
        browser_artifact_refs=browser_result.artifact_refs if browser_result else [],
        sandbox_policy_ref=target.sandbox_policy_ref,
        browser_budget_ref=target.browser_budget_ref,
        policy_decision_refs=sorted(set(policy_refs or [f"policy:{manifest_id}:browser-quality"])),
        failure_report_refs=failure_refs or [f"failure:{manifest_id}:{target.id}:{failure.value}"],
        missing_ref_fields=sorted(set(missing)),
        failure_type=failure,
        diagnostics=diagnostics,
        browser_wall_time_ms=browser_result.wall_time_ms if browser_result else 0,
        browser_network_request_count=browser_result.network_request_count if browser_result else 0,
        browser_blocked_request_count=browser_result.blocked_request_count if browser_result else 0,
        browser_cost_units=max(0, (browser_result.wall_time_ms // 1000) + 1)
        if browser_result
        else 0,
        completion_result=CompletenessResult.FAIL,
    )


def _browser_artifact_parts(
    browser_result: BrowserObservationResult | None,
) -> dict[str, list[Ref]]:
    if browser_result is None:
        return {}
    step = browser_result.step
    return {
        "dom_artifact_refs": [step.dom_artifact_ref] if step.dom_artifact_ref else [],
        "screenshot_artifact_refs": [step.screenshot_artifact_ref]
        if step.screenshot_artifact_ref
        else [],
        "network_trace_refs": [step.network_log_ref] if step.network_log_ref else [],
        "console_log_refs": [
            ref for ref in browser_result.artifact_refs if ":console:" in ref
        ],
        "timing_refs": [ref for ref in browser_result.artifact_refs if ":timing:" in ref],
    }


def _fragment_ref(kind: str, target_id: str, fragment: str) -> Ref:
    return f"{kind}:{target_id}:{stable_hash(fragment)[:12]}"


def _build_report(
    *,
    manifest: BrowserQualityCorpusManifest,
    observations: list[BrowserQualityObservation],
    deltas: list[BrowserQualityDeltaRecord],
) -> BrowserQualityReport:
    passing = [item for item in observations if item.completion_result == CompletenessResult.PASS]
    failure_type, diagnostics, missing = _report_failure(manifest, observations, len(passing))
    completion = CompletenessResult.FAIL if failure_type else CompletenessResult.PASS
    return BrowserQualityReport(
        id=f"browser-quality-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        observation_refs=[item.id for item in observations],
        delta_record_refs=[item.id for item in deltas],
        target_count=len(manifest.target_specs),
        browser_required_pass_count=len(passing),
        recovered_fragment_count=sum(len(item.recovered_fragment_refs) for item in passing),
        http_only_missing_count=sum(len(item.http_missing_fragment_refs) for item in passing),
        budget_exceeded_count=_count_failure(
            observations, BrowserQualityFailureType.BUDGET_EXCEEDED
        ),
        unsafe_blocked_count=_count_failure(
            observations, BrowserQualityFailureType.UNSAFE_ACTION
        ),
        prompt_taint_blocked_count=_count_failure(
            observations, BrowserQualityFailureType.PROMPT_TAINT_BYPASS
        ),
        artifact_missing_count=_count_failure(
            observations, BrowserQualityFailureType.MISSING_ARTIFACT
        ),
        replay_missing_count=_count_failure(
            observations, BrowserQualityFailureType.REPLAY_MISMATCH
        ),
        dom_artifact_refs=_collect("dom_artifact_refs", passing),
        screenshot_artifact_refs=_collect("screenshot_artifact_refs", passing),
        network_trace_refs=_collect("network_trace_refs", passing),
        console_log_refs=_collect("console_log_refs", passing),
        timing_refs=_collect("timing_refs", passing),
        content_hash_refs=sorted(
            set(
                _collect("http_content_hash_refs", passing)
                + _collect("rendered_content_hash_refs", passing)
            )
        ),
        source_anchor_refs=_collect("source_anchor_refs", passing),
        browser_budget_refs=_collect_one("browser_budget_ref", passing),
        prompt_taint_boundary_refs=_collect("prompt_taint_boundary_refs", passing),
        policy_decision_refs=_collect("policy_decision_refs", observations),
        command_record_refs=_collect("command_record_refs", observations),
        event_cursor_refs=_collect("event_cursor_refs", observations),
        outbox_refs=_collect("outbox_refs", observations),
        replay_bundle_refs=_collect_one("replay_bundle_ref", passing),
        failure_report_refs=sorted(
            {ref for item in observations for ref in item.failure_report_refs}
        )
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "browser_quality_completed",
        completion_result=completion,
    )


def _report_failure(
    manifest: BrowserQualityCorpusManifest,
    observations: list[BrowserQualityObservation],
    passing_count: int,
) -> tuple[BrowserQualityFailureType | None, list[str], list[str]]:
    failed = [item for item in observations if item.completion_result != CompletenessResult.PASS]
    if failed:
        first = failed[0].failure_type or BrowserQualityFailureType.MISSING_ARTIFACT
        diagnostics = [diagnostic for item in failed for diagnostic in item.diagnostics]
        missing = sorted({field for item in failed for field in item.missing_ref_fields})
        return first, diagnostics, missing
    if passing_count < manifest.minimum_browser_required_count:
        return (
            BrowserQualityFailureType.INSUFFICIENT_BROWSER_REQUIRED_TARGETS,
            [
                f"browser-required passing targets {passing_count} below minimum "
                f"{manifest.minimum_browser_required_count}"
            ],
            ["browser_required_pass_count"],
        )
    return None, [], []


def _count_failure(
    observations: Iterable[BrowserQualityObservation],
    failure_type: BrowserQualityFailureType,
) -> int:
    return sum(1 for item in observations if item.failure_type == failure_type)


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})


def _record_observation_event(
    manifest_id: str,
    observation: BrowserQualityObservation,
    store: ProductionPersistenceStore,
) -> BrowserQualityObservation:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:{observation.target_spec_ref}:browser-quality-observation",
        command_type="record_browser_quality_observation",
        target_aggregate_type="BrowserQualityObservation",
        target_aggregate_id=observation.id,
        event_type="browser_quality_observed",
        output_refs=[observation.id],
        policy_decision_refs=observation.policy_decision_refs,
        store=store,
    )
    updated = observation.model_copy(
        update={
            "command_record_refs": sorted(set(observation.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(observation.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(observation.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("browser_quality_observations", updated.id, updated)
    return updated


def _record_delta_event(
    manifest_id: str,
    delta: BrowserQualityDeltaRecord,
    store: ProductionPersistenceStore,
) -> BrowserQualityDeltaRecord:
    _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:{delta.target_spec_ref}:browser-quality-delta",
        command_type="record_browser_quality_delta",
        target_aggregate_type="BrowserQualityDeltaRecord",
        target_aggregate_id=delta.id,
        event_type="browser_quality_delta_recorded",
        output_refs=[delta.id],
        policy_decision_refs=[],
        store=store,
    )
    store.save_canonical_model("browser_quality_deltas", delta.id, delta)
    return delta


def _record_report_event(
    manifest_id: str,
    report: BrowserQualityReport,
    store: ProductionPersistenceStore,
) -> BrowserQualityReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:browser-quality-report",
        command_type="record_browser_quality_report",
        target_aggregate_type="BrowserQualityReport",
        target_aggregate_id=report.id,
        event_type="browser_quality_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:browser-quality-benchmark",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{command_id}:dispatched",
    )
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id
