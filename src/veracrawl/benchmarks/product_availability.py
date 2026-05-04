"""Product price and availability benchmark runtime."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib import robotparser

from veracrawl.benchmarks.offer_projection import (
    ProductOfferProjectionResult,
    build_product_offer_projection,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.browser.observation import execute_browser_observation_acquisition
from veracrawl.contracts.agent import (
    AgentActionTrace,
    AgentRunRequest,
    AgentRunResult,
    ContextBundleTrace,
    ModelCallTrace,
    ModelRequest,
    ModelResponse,
    ToolCallTrace,
)
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentRole,
    BrowserSideEffectClass,
    CompletenessResult,
    ProductAvailabilityDecisionType,
    ProductAvailabilityFailureType,
    ProductAvailabilityStatus,
    ToolCallStatus,
)
from veracrawl.contracts.network import LiveHttpAcquisitionReport
from veracrawl.contracts.offer_projection import (
    ProductOfferProjectionReport,
    SortableProductOfferRecord,
)
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkManifest,
    ProductAvailabilityBenchmarkReport,
    ProductAvailabilityFieldEvidence,
    ProductAvailabilitySiteResult,
    ProductAvailabilityTargetSpec,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.fetch.network_acquisition import is_private_network_url, url_origin
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort

NetworkAdapterFactory = Callable[
    [str, ProductAvailabilityTargetSpec],
    NetworkSourceAdapterPort,
]
BrowserAdapterFactory = Callable[
    [str, ProductAvailabilityTargetSpec, BrowserSandboxPolicy],
    BrowserSourceAdapterPort,
]
RobotsFetcher = Callable[[ProductAvailabilityTargetSpec], RobotsFetchResult]
_ContextPayloadSetter = Callable[[str, str], None]
_TokenUsageGetter = Callable[[str], dict[str, int]]


@dataclass(frozen=True)
class ProductAvailabilityModelBinding:
    provider_name: str
    model_id: str
    model_version: str
    runtime_ref: Ref
    port: ModelProviderPort | None = None


@dataclass(frozen=True)
class ProductAvailabilityAgentBinding:
    framework_name: str
    runtime_spec_id: str
    runtime_ref: Ref
    port: AgentRuntimePort | None = None


@dataclass(frozen=True)
class ProductAvailabilityBenchmarkResult:
    report: ProductAvailabilityBenchmarkReport
    site_results: list[ProductAvailabilitySiteResult]
    field_evidence: list[ProductAvailabilityFieldEvidence]
    offer_projection_report: ProductOfferProjectionReport
    offer_records: list[SortableProductOfferRecord]
    model_requests: list[ModelRequest]
    model_responses: list[ModelResponse]
    model_call_traces: list[ModelCallTrace]
    agent_run_requests: list[AgentRunRequest]
    agent_run_results: list[AgentRunResult]
    agent_action_traces: list[AgentActionTrace]
    tool_call_traces: list[ToolCallTrace]
    context_bundle_traces: list[ContextBundleTrace]


@dataclass(frozen=True)
class _FieldCandidate:
    raw_text: str
    normalized_value: str
    amount: float | None = None
    currency: str | None = None


@dataclass(frozen=True)
class _DeliveryCandidate:
    raw_text: str
    normalized_value: str
    min_days: int
    max_days: int


@dataclass(frozen=True)
class _DecisionBundle:
    model_request: ModelRequest
    model_response: ModelResponse
    model_call_trace: ModelCallTrace
    agent_run_request: AgentRunRequest
    agent_run_result: AgentRunResult
    agent_action_trace: AgentActionTrace
    tool_call_trace: ToolCallTrace
    context_bundle_trace: ContextBundleTrace


@dataclass(frozen=True)
class _SourceSelection:
    body: str
    artifact_refs: list[Ref]
    content_hash_refs: list[Ref]
    canonical_url_refs: list[Ref]
    source_observation_refs: list[Ref]
    field_artifact_ref: Ref
    field_content_hash_ref: Ref
    policy_decision_refs: list[Ref]
    command_record_refs: list[Ref]
    event_cursor_refs: list[Ref]
    outbox_refs: list[Ref]
    recovered_by_browser: bool = False


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(" ".join(self._parts).split())


_DECISION_ROLES: dict[ProductAvailabilityDecisionType, AgentRole] = {
    ProductAvailabilityDecisionType.PRODUCT_IDENTITY: AgentRole.SITE_UNDERSTANDING,
    ProductAvailabilityDecisionType.PRICE_CANDIDATE: AgentRole.EXTRACTOR,
    ProductAvailabilityDecisionType.AVAILABILITY_CANDIDATE: AgentRole.EXTRACTOR,
    ProductAvailabilityDecisionType.VERIFICATION: AgentRole.VERIFIER,
}


def run_product_availability_benchmark(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    profile: str,
    store: ProductionPersistenceStore,
    adapter_factory: NetworkAdapterFactory,
    robots_fetcher: RobotsFetcher,
    model_binding: ProductAvailabilityModelBinding,
    agent_binding: ProductAvailabilityAgentBinding,
    browser_adapter_factory: BrowserAdapterFactory | None = None,
    browser_source_required: bool = False,
) -> ProductAvailabilityBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    site_results: list[ProductAvailabilitySiteResult] = []
    field_evidence: list[ProductAvailabilityFieldEvidence] = []
    model_requests: list[ModelRequest] = []
    model_responses: list[ModelResponse] = []
    model_call_traces: list[ModelCallTrace] = []
    agent_run_requests: list[AgentRunRequest] = []
    agent_run_results: list[AgentRunResult] = []
    agent_action_traces: list[AgentActionTrace] = []
    tool_call_traces: list[ToolCallTrace] = []
    context_bundle_traces: list[ContextBundleTrace] = []

    for target in manifest.target_specs:
        target_run_ref = f"{manifest.id}:{target.id}"
        policy_failure = _target_policy_failure(manifest, target)
        if policy_failure is not None:
            failure, diagnostics = policy_failure
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=failure,
                    missing_field="target_url",
                    diagnostics=diagnostics,
                )
            )
            continue

        robots = _check_robots(target=target, robots_fetcher=robots_fetcher)
        if robots.failure_type is not None:
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=robots.failure_type,
                    missing_field=robots.missing_field,
                    diagnostics=list(robots.diagnostics),
                    policy_decision_refs=[robots.policy_ref],
                )
            )
            continue

        live_result = execute_live_http_acquisition(
            fixture_id=target_run_ref,
            scenario="success",
            target_url=target.target_url,
            store=store,
            adapter=adapter_factory(target_run_ref, target),
            profile=profile,
            egress_allowlist=[target.allowed_origin],
            allow_private_network=False,
            size_budget_bytes=target.size_budget_bytes,
            timeout_ms=target.timeout_ms,
        )
        live_report = live_result.report
        network_result = (
            live_result.network_outcome.network_result
            if live_result.network_outcome is not None
            else None
        )
        if live_report.completion_result != CompletenessResult.PASS or network_result is None:
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=_live_failure(live_report.operator_status),
                    missing_field=live_report.operator_status,
                    diagnostics=live_report.diagnostics or [live_report.operator_status],
                    live_http_report_ref=live_report.id,
                    policy_decision_refs=live_report.policy_decision_refs,
                    command_record_refs=live_report.command_record_refs,
                    event_cursor_refs=live_report.event_cursor_refs,
                    outbox_refs=live_report.outbox_refs,
                )
            )
            continue

        source = _http_source_selection(live_report=live_report, body=network_result.body_text)
        body = source.body
        required_terms = set(manifest.required_identity_terms + target.required_identity_terms)
        identity_terms = _matched_identity_terms(target, manifest, body)
        price = _extract_price(body)
        availability = _extract_availability(body)
        if (
            browser_adapter_factory is not None
            and not manifest.negative_case
            and (
                browser_source_required
                or _needs_browser_source_recovery(
                    identity_terms=identity_terms,
                    required_terms=required_terms,
                    price=price,
                    availability=availability,
                )
            )
        ):
            browser_source = _browser_source_selection(
                manifest=manifest,
                target=target,
                target_run_ref=target_run_ref,
                live_source=source,
                browser_adapter_factory=browser_adapter_factory,
            )
            if browser_source is not None:
                source = browser_source
                body = source.body
                identity_terms = _matched_identity_terms(target, manifest, body)
                price = _extract_price(body)
                availability = _extract_availability(body)
            elif browser_source_required:
                site_results.append(
                    _failure_site_result(
                        manifest=manifest,
                        target=target,
                        failure=ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED,
                        missing_field="browser_dom_source",
                        diagnostics=[
                            "required browser render did not produce source-backed DOM evidence"
                        ],
                        live_http_report_ref=live_report.id,
                        network_response_ref=network_result.response.id,
                        policy_decision_refs=source.policy_decision_refs,
                        command_record_refs=source.command_record_refs,
                        event_cursor_refs=source.event_cursor_refs,
                        outbox_refs=source.outbox_refs,
                        artifact_refs=source.artifact_refs,
                        content_hash_refs=source.content_hash_refs,
                        canonical_url_refs=source.canonical_url_refs,
                    )
                )
                continue
        if manifest.scenario == "product-availability-wrong-identity":
            identity_terms = []
        if len(identity_terms) < len(required_terms):
            failure = ProductAvailabilityFailureType.PRODUCT_IDENTITY_MISMATCH
            missing_field = "required_identity_terms"
            diagnostics = ["product page did not contain all required identity terms"]
            if _is_javascript_app_shell(body):
                failure = ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED
                missing_field = "source_backed_product_identity"
                diagnostics = [
                    "live HTML was a JavaScript application shell without "
                    "source-backed product identity"
                ]
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=failure,
                    missing_field=missing_field,
                    diagnostics=diagnostics,
                    live_http_report_ref=live_report.id,
                    network_response_ref=network_result.response.id,
                    policy_decision_refs=source.policy_decision_refs,
                    command_record_refs=source.command_record_refs,
                    event_cursor_refs=source.event_cursor_refs,
                    outbox_refs=source.outbox_refs,
                    artifact_refs=source.artifact_refs,
                    content_hash_refs=source.content_hash_refs,
                    canonical_url_refs=source.canonical_url_refs,
                )
            )
            continue

        if manifest.scenario == "product-availability-missing-price":
            price = None
        if manifest.scenario == "product-availability-missing-availability":
            availability = None
        missing_failure = _missing_field_failure(price=price, availability=availability)
        if missing_failure is not None:
            failure, missing_field = missing_failure
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=failure,
                    missing_field=missing_field,
                    diagnostics=[
                        f"{missing_field} was not source-backed in accepted source artifact"
                    ],
                    live_http_report_ref=live_report.id,
                    network_response_ref=network_result.response.id,
                    policy_decision_refs=source.policy_decision_refs,
                    command_record_refs=source.command_record_refs,
                    event_cursor_refs=source.event_cursor_refs,
                    outbox_refs=source.outbox_refs,
                    artifact_refs=source.artifact_refs,
                    content_hash_refs=source.content_hash_refs,
                    canonical_url_refs=source.canonical_url_refs,
                )
            )
            continue
        assert price is not None
        assert availability is not None
        delivery_eta = _extract_delivery_eta(body)
        shipping_fee = _extract_shipping_fee(body, price.currency)

        scenario_failure = _scenario_failure(manifest.scenario)
        if scenario_failure is not None:
            failure, missing_field = scenario_failure
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=failure,
                    missing_field=missing_field,
                    diagnostics=[f"negative scenario failed intentionally: {failure.value}"],
                    live_http_report_ref=live_report.id,
                    network_response_ref=network_result.response.id,
                    policy_decision_refs=source.policy_decision_refs,
                    command_record_refs=source.command_record_refs,
                    event_cursor_refs=source.event_cursor_refs,
                    outbox_refs=source.outbox_refs,
                    artifact_refs=source.artifact_refs,
                    content_hash_refs=source.content_hash_refs,
                    canonical_url_refs=source.canonical_url_refs,
                )
            )
            continue

        if model_binding.port is None or agent_binding.port is None:
            site_results.append(
                _failure_site_result(
                    manifest=manifest,
                    target=target,
                    failure=ProductAvailabilityFailureType.ADAPTER_UNAVAILABLE,
                    missing_field="adapter_runtime_refs",
                    diagnostics=["model provider or agent runtime adapter unavailable"],
                    live_http_report_ref=live_report.id,
                    network_response_ref=network_result.response.id,
                    policy_decision_refs=source.policy_decision_refs,
                    command_record_refs=source.command_record_refs,
                    event_cursor_refs=source.event_cursor_refs,
                    outbox_refs=source.outbox_refs,
                    artifact_refs=source.artifact_refs,
                    content_hash_refs=source.content_hash_refs,
                    canonical_url_refs=source.canonical_url_refs,
                )
            )
            continue

        decision_bundles = {
            decision: _build_decision_bundle(
                manifest=manifest,
                target=target,
                live_http_report_ref=live_report.id,
                artifact_refs=source.artifact_refs,
                content_hash_refs=source.content_hash_refs,
                decision_type=decision,
                model_binding=model_binding,
                agent_binding=agent_binding,
                model_port=model_binding.port,
                agent_port=agent_binding.port,
            )
            for decision in ProductAvailabilityDecisionType
        }
        for bundle in decision_bundles.values():
            model_requests.append(bundle.model_request)
            model_responses.append(bundle.model_response)
            model_call_traces.append(bundle.model_call_trace)
            agent_run_requests.append(bundle.agent_run_request)
            agent_run_results.append(bundle.agent_run_result)
            agent_action_traces.append(bundle.agent_action_trace)
            tool_call_traces.append(bundle.tool_call_trace)
            context_bundle_traces.append(bundle.context_bundle_trace)

        site_field_evidence = _build_field_evidence(
            manifest=manifest,
            target=target,
            identity_terms=identity_terms,
            price=price,
            availability=availability,
            delivery_eta=delivery_eta,
            shipping_fee=shipping_fee,
            live_http_report_ref=live_report.id,
            network_response_ref=network_result.response.id,
            artifact_ref=source.field_artifact_ref,
            content_hash_ref=source.field_content_hash_ref,
            canonical_url_ref=source.canonical_url_refs[0],
            policy_decision_refs=source.policy_decision_refs,
            command_record_refs=source.command_record_refs,
            event_cursor_refs=source.event_cursor_refs,
            outbox_refs=source.outbox_refs,
            decision_bundles=decision_bundles,
        )
        field_evidence.extend(site_field_evidence)
        site_results.append(
            _success_site_result(
                manifest=manifest,
                target=target,
                live_http_report_ref=live_report.id,
                network_response_ref=network_result.response.id,
                status_code=network_result.response.status_code,
                content_type=network_result.response.content_type or "application/octet-stream",
                body_size_bytes=network_result.response.body_size_bytes,
                content_digest=source.field_content_hash_ref,
                source_observation_refs=source.source_observation_refs,
                artifact_refs=source.artifact_refs,
                content_hash_refs=source.content_hash_refs,
                canonical_url_refs=source.canonical_url_refs,
                identity_terms=identity_terms,
                evidence=site_field_evidence,
                price=price,
                availability=availability,
                delivery_eta=delivery_eta,
                shipping_fee=shipping_fee,
                decision_bundles=decision_bundles,
                policy_decision_refs=source.policy_decision_refs,
                command_record_refs=source.command_record_refs,
                event_cursor_refs=source.event_cursor_refs,
                outbox_refs=source.outbox_refs,
            )
        )

    offer_projection = build_product_offer_projection(
        fixture_id=manifest.id,
        product_name=manifest.product_name,
        run_ref=f"run:{manifest.id}",
        site_results=site_results,
        field_evidence=field_evidence,
    )
    report = _build_report(
        manifest=manifest,
        site_results=site_results,
        evidence=field_evidence,
        offer_projection=offer_projection,
    )
    return ProductAvailabilityBenchmarkResult(
        report=report,
        site_results=site_results,
        field_evidence=field_evidence,
        offer_projection_report=offer_projection.report,
        offer_records=offer_projection.offer_records,
        model_requests=model_requests,
        model_responses=model_responses,
        model_call_traces=model_call_traces,
        agent_run_requests=agent_run_requests,
        agent_run_results=agent_run_results,
        agent_action_traces=agent_action_traces,
        tool_call_traces=tool_call_traces,
        context_bundle_traces=context_bundle_traces,
    )


@dataclass(frozen=True)
class _RobotsCheck:
    policy_ref: Ref
    failure_type: ProductAvailabilityFailureType | None = None
    missing_field: str = ""
    diagnostics: tuple[str, ...] = ()


def _target_policy_failure(
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
) -> tuple[ProductAvailabilityFailureType, list[str]] | None:
    allowed = {spec.allowed_origin for spec in manifest.target_specs}
    if target.allowed_origin not in allowed or url_origin(target.target_url) not in allowed:
        return (
            ProductAvailabilityFailureType.LIVE_HTTP_FAILED,
            [f"{target.target_url} is outside benchmark allowlist"],
        )
    if is_private_network_url(target.target_url) or is_private_network_url(target.robots_url):
        return (
            ProductAvailabilityFailureType.LIVE_HTTP_FAILED,
            ["product availability benchmark denied private-network target"],
        )
    return None


def _check_robots(
    *,
    target: ProductAvailabilityTargetSpec,
    robots_fetcher: RobotsFetcher,
) -> _RobotsCheck:
    policy_ref = f"policy:{target.id}:robots"
    try:
        robots = robots_fetcher(target)
    except OSError as exc:
        return _RobotsCheck(
            policy_ref=policy_ref,
            failure_type=ProductAvailabilityFailureType.NETWORK_UNAVAILABLE,
            missing_field="robots_url",
            diagnostics=(f"robots preflight failed: {exc}",),
        )
    if robots.status_code not in target.allowed_robots_status_codes:
        return _RobotsCheck(
            policy_ref=f"{policy_ref}:{robots.status_code}",
            failure_type=ProductAvailabilityFailureType.ROBOTS_DENIED,
            missing_field="robots_status_code",
            diagnostics=(f"robots status {robots.status_code} is not allowed",),
        )
    if robots.status_code == 200:
        parser = robotparser.RobotFileParser()
        parser.set_url(target.robots_url)
        parser.parse(robots.body_text.splitlines())
        if not parser.can_fetch("VeraCrawl-real-benchmark/1", target.target_url):
            return _RobotsCheck(
                policy_ref=f"{policy_ref}:deny",
                failure_type=ProductAvailabilityFailureType.ROBOTS_DENIED,
                missing_field="robots_policy",
                diagnostics=(f"robots policy disallows {target.target_url}",),
            )
    return _RobotsCheck(policy_ref=f"{policy_ref}:allow:{robots.status_code}")


def _http_source_selection(
    *,
    live_report: LiveHttpAcquisitionReport,
    body: str,
) -> _SourceSelection:
    artifact_refs = list(live_report.artifact_refs)
    content_hash_refs = list(live_report.content_hash_refs)
    canonical_url_refs = list(live_report.canonical_url_refs)
    return _SourceSelection(
        body=body,
        artifact_refs=artifact_refs,
        content_hash_refs=content_hash_refs,
        canonical_url_refs=canonical_url_refs,
        source_observation_refs=list(live_report.source_observation_refs),
        field_artifact_ref=artifact_refs[0],
        field_content_hash_ref=content_hash_refs[0],
        policy_decision_refs=list(live_report.policy_decision_refs),
        command_record_refs=list(live_report.command_record_refs),
        event_cursor_refs=list(live_report.event_cursor_refs),
        outbox_refs=list(live_report.outbox_refs),
    )


def _needs_browser_source_recovery(
    *,
    identity_terms: list[str],
    required_terms: set[str],
    price: _FieldCandidate | None,
    availability: _FieldCandidate | None,
) -> bool:
    return len(identity_terms) < len(required_terms) or price is None or availability is None


def _browser_source_selection(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
    target_run_ref: str,
    live_source: _SourceSelection,
    browser_adapter_factory: BrowserAdapterFactory,
) -> _SourceSelection | None:
    browser_fixture_ref = f"{target_run_ref}:browser-render"
    sandbox = _product_browser_sandbox_policy(fixture_id=browser_fixture_ref, target=target)
    try:
        browser_outcome = execute_browser_observation_acquisition(
            fixture_id=browser_fixture_ref,
            scenario="browser-readonly",
            target_url=target.target_url,
            adapter=browser_adapter_factory(browser_fixture_ref, target, sandbox),
            sandbox_policy=sandbox,
            side_effect_class=BrowserSideEffectClass.READ_ONLY,
        )
    except Exception:
        return None
    if (
        browser_outcome.report.completion_result != CompletenessResult.PASS
        or browser_outcome.browser_result is None
        or not browser_outcome.browser_result.dom_text
        or browser_outcome.browser_result.dom_content_hash is None
    ):
        return None

    browser = browser_outcome.browser_result
    if _is_access_control_page(browser.dom_text):
        return None
    browser_content_hash_ref = browser.dom_content_hash
    if browser_content_hash_ref is None:
        return None
    browser_step_ref = browser.step.id
    artifact_refs = sorted(set(live_source.artifact_refs + browser.artifact_refs))
    content_hash_refs = sorted(set(live_source.content_hash_refs + [browser_content_hash_ref]))
    policy_decision_refs = sorted(
        set(live_source.policy_decision_refs + browser_outcome.report.policy_decision_refs)
    )
    command_record_refs = sorted(
        set(live_source.command_record_refs + browser_outcome.report.command_record_refs)
    )
    event_cursor_refs = sorted(
        set(live_source.event_cursor_refs + browser_outcome.report.event_cursor_refs)
    )
    outbox_refs = sorted(set(live_source.outbox_refs + browser_outcome.report.outbox_refs))
    return _SourceSelection(
        body=browser.dom_text,
        artifact_refs=artifact_refs,
        content_hash_refs=content_hash_refs,
        canonical_url_refs=live_source.canonical_url_refs,
        source_observation_refs=sorted(
            set(live_source.source_observation_refs + [browser_step_ref])
        ),
        field_artifact_ref=browser.step.dom_artifact_ref or browser.artifact_refs[0],
        field_content_hash_ref=browser_content_hash_ref,
        policy_decision_refs=policy_decision_refs,
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
        recovered_by_browser=True,
    )


def _product_browser_sandbox_policy(
    *,
    fixture_id: str,
    target: ProductAvailabilityTargetSpec,
) -> BrowserSandboxPolicy:
    return BrowserSandboxPolicy(
        id=f"browser-sandbox:{fixture_id}",
        allowed_origin_refs=[f"origin:{target.allowed_origin}"],
        egress_allowlist=[target.allowed_origin],
        private_network_denylist=["private", "link_local", "multicast", "unspecified"],
        max_runtime_ms=target.timeout_ms,
        max_dom_bytes=target.size_budget_bytes * 2,
        max_screenshot_bytes=target.size_budget_bytes * 2,
        max_network_log_bytes=target.size_budget_bytes,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
        capture_dom=True,
        capture_screenshot=True,
        capture_network_log=True,
    )


def _matched_identity_terms(
    target: ProductAvailabilityTargetSpec,
    manifest: ProductAvailabilityBenchmarkManifest,
    body: str,
) -> list[str]:
    folded = body.casefold()
    terms = list(dict.fromkeys(manifest.required_identity_terms + target.required_identity_terms))
    rejected = manifest.rejected_identity_terms + target.rejected_identity_terms
    if any(term.casefold() in folded for term in rejected):
        return []
    return [term for term in terms if term.casefold() in folded]


def _is_javascript_app_shell(body: str) -> bool:
    folded = body.casefold()
    if "please enable javascript" in folded:
        return True
    return bool(
        re.search(
            r"<div\b[^>]*\bid\s*=\s*([\"'])(?:app|main|root)\1[^>]*>\s*</div>",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def _is_access_control_page(body: str) -> bool:
    folded = body.casefold()
    markers = (
        "robot or human",
        "confirm that you're human",
        "confirm that you are human",
        "captcha",
        "access denied",
        "request blocked",
    )
    return any(marker in folded for marker in markers)


def _extract_price(body: str) -> _FieldCandidate | None:
    for candidate in _jsonld_price_candidates(body):
        return candidate
    for candidate in _meta_price_candidates(body):
        return candidate
    patterns = [
        r'<span class="a-offscreen">\s*([^<]*?(?:TWD|US\s*\$|\$)[^<]*?\d[^<]*?)\s*</span>',
        r'data-pricetopay-label="\{priceToPay\}"[^>]*>\s*([^<]*?\d[^<]*?)\s*</span>',
        r'"priceString"\s*:\s*"(\$[0-9][0-9,]*(?:\.[0-9]{2})?)"',
        r"(TWD\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        r"(NT\s*\$[0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        r"(US\s*\$[0-9][0-9,]*(?:\.[0-9]{2})?)",
        r"(\$[0-9][0-9,]*(?:\.[0-9]{2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _price_candidate_from_raw(html.unescape(match.group(1)).strip())
    return None


def _jsonld_price_candidates(body: str) -> list[_FieldCandidate]:
    candidates: list[_FieldCandidate] = []
    for payload in _jsonld_payloads(body):
        for product in _walk_jsonld_products(payload):
            offers = product.get("offers")
            offer_items = offers if isinstance(offers, list) else [offers]
            for offer in offer_items:
                if not isinstance(offer, dict):
                    continue
                price = offer.get("price")
                currency = offer.get("priceCurrency")
                if isinstance(price, int | float | str):
                    raw = f"{currency or ''} {price}".strip()
                    candidates.append(
                        _FieldCandidate(
                            raw_text=raw,
                            normalized_value=str(price),
                            amount=_parse_amount(str(price)),
                            currency=str(currency) if currency else None,
                        )
                    )
    return candidates


def _meta_price_candidates(body: str) -> list[_FieldCandidate]:
    amount = _meta_content(
        body,
        (
            "product:price:amount",
            "og:price:amount",
            "price:amount",
            "price",
        ),
    )
    if amount is None:
        return []
    currency = _meta_content(
        body,
        (
            "product:price:currency",
            "og:price:currency",
            "price:currency",
            "currency",
        ),
    )
    raw = f"{currency or ''} {amount}".strip()
    candidate = _price_candidate_from_raw(raw)
    return [candidate] if candidate is not None else []


def _extract_availability(body: str) -> _FieldCandidate | None:
    for payload in _jsonld_payloads(body):
        for product in _walk_jsonld_products(payload):
            offers = product.get("offers")
            offer_items = offers if isinstance(offers, list) else [offers]
            for offer in offer_items:
                if not isinstance(offer, dict):
                    continue
                availability = offer.get("availability")
                if isinstance(availability, str):
                    status = _normalize_availability(availability)
                    if status is not None:
                        return _FieldCandidate(
                            raw_text=availability,
                            normalized_value=status.value,
                        )
    meta_availability = _meta_content(
        body,
        (
            "product:availability",
            "og:availability",
            "availability",
        ),
    )
    if meta_availability is not None:
        status = _normalize_availability(meta_availability)
        if status is not None:
            return _FieldCandidate(
                raw_text=meta_availability,
                normalized_value=status.value,
            )
    patterns = [
        (r'"availabilityStatus"\s*:\s*"IN_STOCK"', ProductAvailabilityStatus.IN_STOCK),
        (r'"availabilityStatus"\s*:\s*"OUT_OF_STOCK"', ProductAvailabilityStatus.OUT_OF_STOCK),
        (
            r"\bOnly\s+\d+\s+left\s+in\s+stock\b[^.\n]*\.?",
            ProductAvailabilityStatus.LIMITED,
        ),
        (r"\b\d+\s+left\s+in\s+stock\b", ProductAvailabilityStatus.LIMITED),
        (r"\bIn Stock\b", ProductAvailabilityStatus.IN_STOCK),
        (r"\bAdd to Cart\b", ProductAvailabilityStatus.IN_STOCK),
        (
            r'class="[^"]*primary-availability-message[^"]*"[^>]*>\s*In Stock\s*<',
            ProductAvailabilityStatus.IN_STOCK,
        ),
        (r">\s*Out of stock\s*<", ProductAvailabilityStatus.OUT_OF_STOCK),
        (r">\s*Currently unavailable\.?\s*<", ProductAvailabilityStatus.UNAVAILABLE),
        (r"(\d+)\s+available", ProductAvailabilityStatus.LIMITED),
    ]
    for text in ("熱銷一空", "已售完", "售完", "缺貨", "補貨通知", "可訂購時通知", "貨到通知"):
        patterns.append((re.escape(text), ProductAvailabilityStatus.OUT_OF_STOCK))
    for text in ("加入購物車", "直接購買", "立即購買", "可訂購", "現貨", "有庫存"):
        patterns.append((re.escape(text), ProductAvailabilityStatus.IN_STOCK))
    for pattern, status in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _FieldCandidate(
                raw_text=html.unescape(match.group(0)),
                normalized_value=status.value,
            )
    return None


def _extract_delivery_eta(body: str) -> _DeliveryCandidate | None:
    meta_delivery = _meta_content(
        body,
        (
            "product:delivery_time",
            "og:delivery_time",
            "shipping:delivery_time",
            "delivery_time",
            "delivery",
        ),
    )
    if meta_delivery is not None:
        candidate = _delivery_candidate_from_raw(meta_delivery)
        if candidate is not None:
            return candidate
    for payload in _jsonld_payloads(body):
        for value in _walk_jsonld_strings(payload):
            candidate = _delivery_candidate_from_raw(value)
            if candidate is not None:
                return candidate
    source_text = _source_text(body)
    phrase_patterns = [
        r"(?:最快)?(?:今天|今日).{0,20}(?:到貨|送達|配達|出貨)",
        r"(?:最快)?(?:明天|隔日|翌日|次日).{0,20}(?:到貨|送達|配達|出貨)",
        r"(?:24\s*(?:小時|hours?)|二十四小時).{0,20}(?:到貨|送達|配達|出貨|delivery)",
        r"(?:到貨|送達|配達|出貨|arrives?|delivers?|delivery|ships).{0,40}?"
        r"\d+\s*(?:[-~]|到|至)\s*\d+\s*(?:天|日|days?|business days?)",
        r"\d+\s*(?:[-~]|到|至)\s*\d+\s*(?:天|日|days?|business days?).{0,40}?"
        r"(?:到貨|送達|配達|出貨|arrives?|delivers?|delivery|ships)",
        r"(?:within|in)\s+\d+\s*(?:days?|business days?).{0,30}?"
        r"(?:arrives?|delivers?|delivery)",
        r"(?:到貨|送達|配達|出貨|arrives?|delivers?|delivery|ships).{0,40}?"
        r"\d+\s*(?:天|日|days?|business days?)",
        r"\d+\s*(?:天|日|days?|business days?).{0,40}?"
        r"(?:到貨|送達|配達|出貨|arrives?|delivers?|delivery|ships)",
    ]
    for pattern in phrase_patterns:
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match:
            candidate = _delivery_candidate_from_raw(match.group(0))
            if candidate is not None:
                return candidate
    return None


def _extract_shipping_fee(
    body: str,
    fallback_currency: str | None,
) -> _FieldCandidate | None:
    amount = _meta_content(
        body,
        (
            "product:shipping:amount",
            "shipping:amount",
            "shipping_fee",
            "shipping:price",
        ),
    )
    if amount is not None:
        currency = _meta_content(
            body,
            (
                "product:shipping:currency",
                "shipping:currency",
                "shipping_currency",
            ),
        )
        candidate = _price_candidate_from_raw(f"{currency or fallback_currency or ''} {amount}")
        return _with_fallback_currency(candidate, fallback_currency)

    source_text = _source_text(body)
    free_shipping = re.search(
        r"(免運|免運費|free shipping)",
        source_text,
        flags=re.IGNORECASE,
    )
    if free_shipping:
        currency = fallback_currency or _parse_currency(source_text)
        if currency is None:
            return None
        return _FieldCandidate(
            raw_text=free_shipping.group(0),
            normalized_value=f"{currency} 0.0",
            amount=0.0,
            currency=currency,
        )
    shipping_patterns = [
        r"(?:運費|配送費|宅配|shipping|delivery fee)\s*(?:NT\s*\$|TWD|US\s*\$|\$)?\s*"
        r"[0-9][0-9,]*(?:\.[0-9]{1,2})?",
        r"(?:NT\s*\$|TWD|US\s*\$|\$)\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?\s*"
        r"(?:運費|配送費|shipping|delivery fee)",
    ]
    for pattern in shipping_patterns:
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = _price_candidate_from_raw(match.group(0))
        candidate = _with_fallback_currency(candidate, fallback_currency)
        if candidate is not None:
            return candidate
    return None


def _meta_content(body: str, names: tuple[str, ...]) -> str | None:
    wanted = {name.casefold() for name in names}
    for match in re.finditer(r"<meta\b[^>]*>", body, flags=re.IGNORECASE | re.DOTALL):
        tag = match.group(0)
        name = _html_attr(tag, "name") or _html_attr(tag, "property")
        if name is None or name.casefold() not in wanted:
            continue
        content = _html_attr(tag, "content")
        if content is not None:
            return html.unescape(content).strip()
    return None


def _html_attr(tag: str, attr: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(attr)}\s*=\s*([\"'])(.*?)\1",
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(2) if match else None


def _jsonld_payloads(body: str) -> list[object]:
    payloads: list[object] = []
    for match in re.finditer(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        text = html.unescape(match.group(1)).strip()
        try:
            payloads.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return payloads


def _walk_jsonld_products(payload: object) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if isinstance(payload, dict):
        kind = payload.get("@type")
        if kind == "Product" or (isinstance(kind, list) and "Product" in kind):
            found.append(payload)
        for value in payload.values():
            found.extend(_walk_jsonld_products(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_walk_jsonld_products(item))
    return found


def _walk_jsonld_strings(payload: object) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            folded_key = key.casefold()
            if isinstance(value, str) and (
                "delivery" in folded_key or "shipping" in folded_key or "transit" in folded_key
            ):
                found.append(value)
            else:
                found.extend(_walk_jsonld_strings(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_walk_jsonld_strings(item))
    return found


def _price_candidate_from_raw(raw: str) -> _FieldCandidate | None:
    amount = _parse_amount(raw)
    currency = _parse_currency(raw)
    if amount is None:
        return None
    return _FieldCandidate(
        raw_text=raw,
        normalized_value=f"{currency or ''} {amount}".strip(),
        amount=amount,
        currency=currency,
    )


def _parse_amount(raw: str) -> float | None:
    match = re.search(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)", raw)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _parse_currency(raw: str) -> str | None:
    normalized = raw.replace("\xa0", " ").upper()
    if "TWD" in normalized or "NT$" in normalized or "新台幣" in raw or "台幣" in raw:
        return "TWD"
    if "US $" in normalized or "$" in normalized:
        return "USD"
    if "元" in raw:
        return "TWD"
    currency_match = re.search(r"\b([A-Z]{3})\b", normalized)
    return currency_match.group(1) if currency_match else None


def _with_fallback_currency(
    candidate: _FieldCandidate | None,
    fallback_currency: str | None,
) -> _FieldCandidate | None:
    if candidate is None:
        return None
    if candidate.currency is not None:
        return candidate
    if fallback_currency is None:
        return None
    return _FieldCandidate(
        raw_text=candidate.raw_text,
        normalized_value=f"{fallback_currency} {candidate.amount}",
        amount=candidate.amount,
        currency=fallback_currency,
    )


def _delivery_candidate_from_raw(raw: str) -> _DeliveryCandidate | None:
    normalized = " ".join(html.unescape(raw).split())
    folded = normalized.casefold()
    if any(text in normalized for text in ("今天", "今日")) or "same day" in folded:
        return _DeliveryCandidate(
            raw_text=normalized,
            normalized_value="0-0 days",
            min_days=0,
            max_days=0,
        )
    if (
        any(text in normalized for text in ("明天", "隔日", "翌日", "次日"))
        or "tomorrow" in folded
        or "next day" in folded
        or re.search(r"\b24\s*hours?\b", folded)
        or "24小時" in normalized
    ):
        return _DeliveryCandidate(
            raw_text=normalized,
            normalized_value="1-1 days",
            min_days=1,
            max_days=1,
        )
    range_match = re.search(
        r"(\d+)\s*(?:[-~]|到|至)\s*(\d+)\s*(?:天|日|days?|business days?)",
        normalized,
        flags=re.IGNORECASE,
    )
    if range_match:
        min_days = int(range_match.group(1))
        max_days = int(range_match.group(2))
        if min_days <= max_days:
            return _DeliveryCandidate(
                raw_text=normalized,
                normalized_value=f"{min_days}-{max_days} days",
                min_days=min_days,
                max_days=max_days,
            )
    single_match = re.search(
        r"(?:within|in)?\s*(\d+)\s*(?:天|日|days?|business days?)",
        normalized,
        flags=re.IGNORECASE,
    )
    if single_match:
        days = int(single_match.group(1))
        return _DeliveryCandidate(
            raw_text=normalized,
            normalized_value=f"{days}-{days} days",
            min_days=days,
            max_days=days,
        )
    return None


def _source_text(body: str) -> str:
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def _normalize_availability(value: str) -> ProductAvailabilityStatus | None:
    folded = value.casefold()
    if any(
        text in value
        for text in ("熱銷一空", "已售完", "售完", "缺貨", "補貨通知", "可訂購時通知", "貨到通知")
    ):
        return ProductAvailabilityStatus.OUT_OF_STOCK
    if any(
        text in value for text in ("加入購物車", "直接購買", "立即購買", "可訂購", "現貨", "有庫存")
    ):
        return ProductAvailabilityStatus.IN_STOCK
    if "left in stock" in folded:
        return ProductAvailabilityStatus.LIMITED
    if "instock" in folded or "in_stock" in folded or "in stock" in folded:
        return ProductAvailabilityStatus.IN_STOCK
    if "outofstock" in folded or "out_of_stock" in folded or "out of stock" in folded:
        return ProductAvailabilityStatus.OUT_OF_STOCK
    if "unavailable" in folded:
        return ProductAvailabilityStatus.UNAVAILABLE
    if "limited" in folded:
        return ProductAvailabilityStatus.LIMITED
    return None


def _missing_field_failure(
    *,
    price: _FieldCandidate | None,
    availability: _FieldCandidate | None,
) -> tuple[ProductAvailabilityFailureType, str] | None:
    if price is None:
        return ProductAvailabilityFailureType.PRICE_NOT_FOUND, "price"
    if availability is None:
        return ProductAvailabilityFailureType.AVAILABILITY_NOT_FOUND, "availability"
    return None


def _scenario_failure(
    scenario: str,
) -> tuple[ProductAvailabilityFailureType, str] | None:
    if scenario == "product-availability-llm-output-as-evidence":
        return ProductAvailabilityFailureType.LLM_OUTPUT_AS_EVIDENCE, "llm_output_evidence_refs"
    if scenario == "product-availability-missing-replay":
        return ProductAvailabilityFailureType.MISSING_REPLAY_REFS, "replay_bundle_refs"
    return None


def _build_decision_bundle(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
    live_http_report_ref: Ref,
    artifact_refs: list[Ref],
    content_hash_refs: list[Ref],
    decision_type: ProductAvailabilityDecisionType,
    model_binding: ProductAvailabilityModelBinding,
    agent_binding: ProductAvailabilityAgentBinding,
    model_port: ModelProviderPort,
    agent_port: AgentRuntimePort,
) -> _DecisionBundle:
    decision_slug = decision_type.value
    role = _DECISION_ROLES[decision_type]
    run_id = f"run:{manifest.id}:{target.id}:{decision_slug}"
    policy_refs = [
        f"policy:{manifest.id}:{target.id}:source-scope",
        f"policy:{manifest.id}:{target.id}:prompt-context",
        f"policy:{manifest.id}:{target.id}:product-field-verification",
    ]
    context_trace = ContextBundleTrace(
        id=f"context-bundle-trace:{manifest.id}:{target.id}:{decision_slug}",
        run_id=run_id,
        agent_id=f"agent:{manifest.id}:{target.id}:{role.value}",
        context_ref_schema=f"schema:{manifest.id}:product-availability-context",
        included_context_refs=sorted(
            set([live_http_report_ref, *artifact_refs, *content_hash_refs])
        ),
        sanitized_context_ref=f"sanitized-context:{manifest.id}:{target.id}:{decision_slug}",
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
        credential_exposure_check_ref=f"credential-exposure-check:{manifest.id}:{target.id}:none",
        evidence_refs=artifact_refs,
    )
    agent_request = AgentRunRequest(
        id=f"agent-run-request:{manifest.id}:{target.id}:{decision_slug}",
        run_id=run_id,
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        objective_ref=f"objective:{manifest.id}:product-price-availability",
        context_bundle_id=context_trace.id,
        allowed_tool_spec_refs=[f"tool-spec:{manifest.id}:{decision_slug}:source-read"],
        required_output_schema_ref=f"schema:{manifest.id}:{decision_slug}:output",
        loop_budget_ref=f"loop-budget:{manifest.id}:{target.id}:{decision_slug}",
        policy_decision_refs=policy_refs,
    )
    model_request = ModelRequest(
        id=f"model-request:{manifest.id}:{target.id}:{decision_slug}:{_slug(model_binding.provider_name)}",
        agent_run_request_id=agent_request.id,
        provider_name=model_binding.provider_name,
        model_id=model_binding.model_id,
        prompt_template_ref=f"prompt-template:{manifest.id}:{decision_slug}",
        prompt_template_version="1",
        context_bundle_id=context_trace.id,
        tool_schema_refs=agent_request.allowed_tool_spec_refs,
        response_schema_ref=agent_request.required_output_schema_ref,
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
    )
    context_payload = (
        f"fixture={manifest.id}; product={manifest.product_name}; "
        f"site={target.site_name}; target={target.target_url}; "
        f"decision={decision_type.value}; source_refs={context_trace.included_context_refs}. "
        "Recommend product identity, price, availability, or verification only. "
        "Do not treat model output as evidence."
    )
    context_setter = getattr(model_port, "set_context_payload", None)
    if callable(context_setter):
        setter: _ContextPayloadSetter = context_setter
        setter(model_request.id, context_payload)
    model_response = model_port.complete(model_request)
    agent_result = agent_port.run(agent_request)
    token_usage = {"prompt_ref_tokens": 1, "completion_ref_tokens": 1}
    token_usage_getter_attr = getattr(model_port, "token_usage_for", None)
    if callable(token_usage_getter_attr):
        token_getter: _TokenUsageGetter = token_usage_getter_attr
        token_usage = token_getter(model_request.id) or token_usage
    model_call_trace = ModelCallTrace(
        id=f"model-call-trace:{manifest.id}:{target.id}:{decision_slug}:{_slug(model_binding.provider_name)}",
        run_id=run_id,
        agent_action_trace_id=agent_result.agent_action_trace_id,
        provider_name=model_binding.provider_name,
        model_id=model_binding.model_id,
        model_version=model_binding.model_version,
        prompt_template_ref=model_request.prompt_template_ref,
        prompt_template_version=model_request.prompt_template_version,
        context_bundle_trace_id=context_trace.id,
        request_ref=model_request.id,
        response_ref=model_response.id,
        token_usage=token_usage,
        latency_ms=1,
        safety_filter_result_ref=model_response.safety_filter_result_ref,
        redaction_policy_ref=model_request.redaction_policy_ref,
        raw_prompt_persisted=False,
        raw_response_persisted=False,
    )
    tool_trace = ToolCallTrace(
        id=f"tool-call-trace:{manifest.id}:{target.id}:{decision_slug}:source-read",
        run_id=run_id,
        agent_action_trace_id=agent_result.agent_action_trace_id,
        tool_spec_id=agent_request.allowed_tool_spec_refs[0],
        tool_name=f"{decision_slug}_source_read",
        tool_version="1",
        input_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-input",
        output_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-output",
        input_ref=context_trace.sanitized_context_ref,
        output_ref=f"tool-output:{manifest.id}:{target.id}:{decision_slug}",
        command_envelope_id=f"command-envelope:{manifest.id}:{target.id}:{decision_slug}",
        command_result_id=f"command-result:{manifest.id}:{target.id}:{decision_slug}",
        policy_decision_refs=policy_refs,
        status=ToolCallStatus.EXECUTED,
    )
    agent_action_trace = AgentActionTrace(
        id=agent_result.agent_action_trace_id,
        run_id=run_id,
        objective_id=f"objective:{manifest.id}:product-price-availability",
        agent_id=f"agent:{manifest.id}:{target.id}:{role.value}",
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        model_call_trace_refs=[model_call_trace.id],
        context_bundle_trace_id=context_trace.id,
        tool_call_trace_refs=[tool_trace.id],
        command_result_refs=[tool_trace.command_result_id],
        policy_decision_refs=policy_refs,
        input_refs=context_trace.included_context_refs,
        output_refs=[agent_result.output_ref],
        reasoning_summary_ref=f"reasoning-summary:{manifest.id}:{target.id}:{decision_slug}",
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
        retention_policy_ref=f"retention-policy:{manifest.id}:trace-retention",
    )
    return _DecisionBundle(
        model_request=model_request,
        model_response=model_response,
        model_call_trace=model_call_trace,
        agent_run_request=agent_request,
        agent_run_result=agent_result,
        agent_action_trace=agent_action_trace,
        tool_call_trace=tool_trace,
        context_bundle_trace=context_trace,
    )


def _build_field_evidence(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
    identity_terms: list[str],
    price: _FieldCandidate,
    availability: _FieldCandidate,
    delivery_eta: _DeliveryCandidate | None,
    shipping_fee: _FieldCandidate | None,
    live_http_report_ref: Ref,
    network_response_ref: Ref,
    artifact_ref: Ref,
    content_hash_ref: Ref,
    canonical_url_ref: Ref,
    policy_decision_refs: list[Ref],
    command_record_refs: list[Ref],
    event_cursor_refs: list[Ref],
    outbox_refs: list[Ref],
    decision_bundles: dict[ProductAvailabilityDecisionType, _DecisionBundle],
) -> list[ProductAvailabilityFieldEvidence]:
    del live_http_report_ref, network_response_ref
    specs = [
        (
            "identity",
            " ".join(identity_terms),
            ",".join(identity_terms),
            None,
            None,
            ProductAvailabilityDecisionType.PRODUCT_IDENTITY,
        ),
        (
            "price",
            price.raw_text,
            price.normalized_value,
            price.amount,
            price.currency,
            ProductAvailabilityDecisionType.PRICE_CANDIDATE,
        ),
        (
            "availability",
            availability.raw_text,
            availability.normalized_value,
            None,
            None,
            ProductAvailabilityDecisionType.AVAILABILITY_CANDIDATE,
        ),
    ]
    if delivery_eta is not None:
        specs.append(
            (
                "delivery_eta",
                delivery_eta.raw_text,
                delivery_eta.normalized_value,
                None,
                None,
                ProductAvailabilityDecisionType.VERIFICATION,
            )
        )
    if shipping_fee is not None:
        specs.append(
            (
                "shipping_fee",
                shipping_fee.raw_text,
                shipping_fee.normalized_value,
                shipping_fee.amount,
                shipping_fee.currency,
                ProductAvailabilityDecisionType.VERIFICATION,
            )
        )
    evidence: list[ProductAvailabilityFieldEvidence] = []
    for field_name, raw, normalized, amount, currency, decision_type in specs:
        bundle = decision_bundles[decision_type]
        field_ref = f"product-field-evidence:{manifest.id}:{target.id}:{field_name}"
        evidence.append(
            ProductAvailabilityFieldEvidence(
                id=field_ref,
                fixture_id=manifest.id,
                target_spec_ref=target.id,
                site_name=target.site_name,
                target_url=target.target_url,
                field_name=field_name,
                raw_text=raw,
                normalized_value=normalized,
                amount=amount,
                currency=currency,
                source_anchor_ref=f"source-anchor:{manifest.id}:{target.id}:{field_name}",
                artifact_ref=artifact_ref,
                content_hash_ref=content_hash_ref,
                canonical_url_ref=canonical_url_ref,
                model_call_trace_ref=bundle.model_call_trace.id,
                agent_action_trace_ref=bundle.agent_action_trace.id,
                tool_call_trace_refs=[bundle.tool_call_trace.id],
                context_bundle_trace_ref=bundle.context_bundle_trace.id,
                evidence_packet_ref=f"evidence-packet:{manifest.id}:{target.id}:{field_name}",
                evidence_anchor_ref=f"evidence-anchor:{manifest.id}:{target.id}:{field_name}",
                verification_decision_ref=f"verification-decision:{manifest.id}:{target.id}:{field_name}:accepted",
                policy_decision_refs=policy_decision_refs,
                command_record_refs=command_record_refs
                + [f"command:{manifest.id}:{target.id}:{field_name}"],
                event_cursor_refs=event_cursor_refs
                + [f"event-cursor:{manifest.id}:{target.id}:{field_name}"],
                outbox_refs=outbox_refs + [f"outbox:{manifest.id}:{target.id}:{field_name}"],
                replay_bundle_ref=f"replay-bundle:{manifest.id}:{target.id}:{field_name}",
            )
        )
    return evidence


def _success_site_result(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
    live_http_report_ref: Ref,
    network_response_ref: Ref,
    status_code: int,
    content_type: str,
    body_size_bytes: int,
    content_digest: str,
    source_observation_refs: list[Ref],
    artifact_refs: list[Ref],
    content_hash_refs: list[Ref],
    canonical_url_refs: list[Ref],
    identity_terms: list[str],
    evidence: list[ProductAvailabilityFieldEvidence],
    price: _FieldCandidate,
    availability: _FieldCandidate,
    delivery_eta: _DeliveryCandidate | None,
    shipping_fee: _FieldCandidate | None,
    decision_bundles: dict[ProductAvailabilityDecisionType, _DecisionBundle],
    policy_decision_refs: list[Ref],
    command_record_refs: list[Ref],
    event_cursor_refs: list[Ref],
    outbox_refs: list[Ref],
) -> ProductAvailabilitySiteResult:
    evidence_by_field = {item.field_name: item.id for item in evidence}
    total_price_amount = price.amount
    total_price_currency = price.currency
    if shipping_fee is not None:
        if shipping_fee.currency == price.currency and price.amount is not None:
            total_price_amount = price.amount + (shipping_fee.amount or 0.0)
        else:
            total_price_amount = None
            total_price_currency = None
    return ProductAvailabilitySiteResult(
        id=f"product-availability-site-result:{manifest.id}:{target.id}",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        target_url=target.target_url,
        live_http_report_ref=live_http_report_ref,
        network_response_ref=network_response_ref,
        status_code=status_code,
        content_type=content_type,
        body_size_bytes=body_size_bytes,
        content_digest=content_digest,
        source_observation_refs=source_observation_refs,
        artifact_refs=artifact_refs,
        content_hash_refs=content_hash_refs,
        canonical_url_refs=canonical_url_refs,
        identity_terms_matched=identity_terms,
        field_evidence_refs=[item.id for item in evidence],
        identity_evidence_ref=evidence[0].id,
        price_evidence_ref=evidence[1].id,
        availability_evidence_ref=evidence[2].id,
        price_raw_text=price.raw_text,
        price_amount=price.amount,
        price_currency=price.currency,
        availability_status=ProductAvailabilityStatus(availability.normalized_value),
        availability_raw_text=availability.raw_text,
        delivery_evidence_ref=evidence_by_field.get("delivery_eta"),
        delivery_eta_raw_text=delivery_eta.raw_text if delivery_eta is not None else None,
        delivery_eta_min_days=delivery_eta.min_days if delivery_eta is not None else None,
        delivery_eta_max_days=delivery_eta.max_days if delivery_eta is not None else None,
        shipping_fee_evidence_ref=evidence_by_field.get("shipping_fee"),
        shipping_fee_raw_text=shipping_fee.raw_text if shipping_fee is not None else None,
        shipping_fee_amount=shipping_fee.amount if shipping_fee is not None else None,
        shipping_fee_currency=shipping_fee.currency if shipping_fee is not None else None,
        total_price_amount=total_price_amount,
        total_price_currency=total_price_currency,
        model_call_trace_refs=[bundle.model_call_trace.id for bundle in decision_bundles.values()],
        agent_action_trace_refs=[
            bundle.agent_action_trace.id for bundle in decision_bundles.values()
        ],
        tool_call_trace_refs=[bundle.tool_call_trace.id for bundle in decision_bundles.values()],
        context_bundle_trace_refs=[
            bundle.context_bundle_trace.id for bundle in decision_bundles.values()
        ],
        evidence_packet_refs=[item.evidence_packet_ref for item in evidence],
        evidence_anchor_refs=[item.evidence_anchor_ref for item in evidence],
        verification_decision_refs=[item.verification_decision_ref for item in evidence],
        publication_gate_refs=[
            f"publication-gate:{manifest.id}:{target.id}:blocked-real-site-output"
        ],
        policy_decision_refs=policy_decision_refs,
        command_record_refs=command_record_refs
        + [f"command:{manifest.id}:{target.id}:site-result"],
        event_cursor_refs=event_cursor_refs
        + [f"event-cursor:{manifest.id}:{target.id}:site-result"],
        outbox_refs=outbox_refs + [f"outbox:{manifest.id}:{target.id}:site-result"],
        replay_bundle_refs=[
            f"replay-bundle:{manifest.id}:{target.id}:site-result",
            *[item.replay_bundle_ref for item in evidence],
        ],
        completion_result=CompletenessResult.PASS,
    )


def _failure_site_result(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    target: ProductAvailabilityTargetSpec,
    failure: ProductAvailabilityFailureType,
    missing_field: str,
    diagnostics: list[str],
    live_http_report_ref: Ref | None = None,
    network_response_ref: Ref | None = None,
    policy_decision_refs: list[Ref] | None = None,
    command_record_refs: list[Ref] | None = None,
    event_cursor_refs: list[Ref] | None = None,
    outbox_refs: list[Ref] | None = None,
    artifact_refs: list[Ref] | None = None,
    content_hash_refs: list[Ref] | None = None,
    canonical_url_refs: list[Ref] | None = None,
) -> ProductAvailabilitySiteResult:
    completion = (
        CompletenessResult.NEEDS_REVIEW
        if failure
        in {
            ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED,
            ProductAvailabilityFailureType.PRICE_NOT_FOUND,
            ProductAvailabilityFailureType.AVAILABILITY_NOT_FOUND,
        }
        else CompletenessResult.FAIL
    )
    return ProductAvailabilitySiteResult(
        id=f"product-availability-site-result:{manifest.id}:{target.id}",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        target_url=target.target_url,
        live_http_report_ref=live_http_report_ref,
        network_response_ref=network_response_ref,
        artifact_refs=artifact_refs or [],
        content_hash_refs=content_hash_refs or [],
        canonical_url_refs=canonical_url_refs or [],
        policy_decision_refs=policy_decision_refs or [],
        command_record_refs=command_record_refs or [],
        event_cursor_refs=event_cursor_refs or [],
        outbox_refs=outbox_refs or [],
        blocked_source_refs=[f"blocked-source:{manifest.id}:{target.id}:{failure.value}"],
        failure_report_refs=[f"failure:{manifest.id}:{target.id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        diagnostics=diagnostics,
        completion_result=completion,
    )


def _live_failure(operator_status: str) -> ProductAvailabilityFailureType:
    folded = operator_status.casefold()
    if (
        "adapter" in folded
        or "mismatch" in folded
        or "403" in folded
        or "missing_artifact" in folded
        or "missing_network_artifact" in folded
    ):
        return ProductAvailabilityFailureType.SOURCE_ACCESS_DENIED
    return ProductAvailabilityFailureType.LIVE_HTTP_FAILED


def _build_report(
    *,
    manifest: ProductAvailabilityBenchmarkManifest,
    site_results: list[ProductAvailabilitySiteResult],
    evidence: list[ProductAvailabilityFieldEvidence],
    offer_projection: ProductOfferProjectionResult,
) -> ProductAvailabilityBenchmarkReport:
    passing = [item for item in site_results if item.completion_result == CompletenessResult.PASS]
    non_pass = [item for item in site_results if item.completion_result != CompletenessResult.PASS]
    blocked = [ref for item in non_pass for ref in item.blocked_source_refs]
    if len(passing) == len(site_results) and site_results:
        completion = CompletenessResult.PASS
        operator_status = "product_availability_benchmark_completed"
        failure_type = None
        diagnostics: list[str] = []
    elif passing:
        completion = CompletenessResult.NEEDS_REVIEW
        operator_status = "product_availability_partial_sources_blocked"
        failure_type = None
        diagnostics = [diagnostic for item in non_pass for diagnostic in item.diagnostics]
    else:
        completion = CompletenessResult.FAIL
        operator_status = (
            non_pass[0].failure_type.value
            if non_pass and non_pass[0].failure_type
            else ProductAvailabilityFailureType.MISSING_EVIDENCE_REFS.value
        )
        failure_type = (
            non_pass[0].failure_type
            if non_pass and non_pass[0].failure_type
            else ProductAvailabilityFailureType.MISSING_EVIDENCE_REFS
        )
        diagnostics = [diagnostic for item in non_pass for diagnostic in item.diagnostics]
    return ProductAvailabilityBenchmarkReport(
        id=f"product-availability-benchmark-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        product_name=manifest.product_name,
        target_site_count=len(manifest.target_specs),
        site_result_refs=[item.id for item in site_results],
        passing_site_result_refs=[item.id for item in passing],
        blocked_site_result_refs=[item.id for item in non_pass],
        field_evidence_refs=[item.id for item in evidence],
        price_evidence_refs=[item.id for item in evidence if item.field_name == "price"],
        availability_evidence_refs=[
            item.id for item in evidence if item.field_name == "availability"
        ],
        delivery_evidence_refs=[item.id for item in evidence if item.field_name == "delivery_eta"],
        shipping_fee_evidence_refs=[
            item.id for item in evidence if item.field_name == "shipping_fee"
        ],
        offer_projection_report_ref=offer_projection.report.id,
        offer_record_refs=[item.id for item in offer_projection.offer_records],
        model_call_trace_refs=_collect("model_call_trace_refs", site_results),
        agent_action_trace_refs=_collect("agent_action_trace_refs", site_results),
        tool_call_trace_refs=_collect("tool_call_trace_refs", site_results),
        context_bundle_trace_refs=_collect("context_bundle_trace_refs", site_results),
        evidence_packet_refs=_collect("evidence_packet_refs", site_results),
        evidence_anchor_refs=_collect("evidence_anchor_refs", site_results),
        verification_decision_refs=_collect("verification_decision_refs", site_results),
        policy_decision_refs=_collect("policy_decision_refs", site_results),
        command_record_refs=sorted(
            set(_collect("command_record_refs", site_results) + [f"command:{manifest.id}:report"])
        ),
        event_cursor_refs=sorted(
            set(
                _collect("event_cursor_refs", site_results) + [f"event-cursor:{manifest.id}:report"]
            )
        ),
        outbox_refs=sorted(
            set(_collect("outbox_refs", site_results) + [f"outbox:{manifest.id}:report"])
        ),
        replay_bundle_refs=sorted(
            set(
                _collect("replay_bundle_refs", site_results)
                + [f"replay-bundle:{manifest.id}:report"]
            )
        ),
        blocked_source_refs=blocked,
        failure_report_refs=[ref for item in non_pass for ref in item.failure_report_refs],
        missing_ref_fields=[field for item in non_pass for field in item.missing_ref_fields],
        failure_type=failure_type,
        operator_status=operator_status,
        completion_result=completion,
        diagnostics=diagnostics,
    )


def _collect(field_name: str, results: list[ProductAvailabilitySiteResult]) -> list[Ref]:
    refs: list[Ref] = []
    for result in results:
        refs.extend(getattr(result, field_name))
    return sorted(set(refs))


def product_availability_field_replay_passes(
    evidence: ProductAvailabilityFieldEvidence,
) -> bool:
    return bool(
        evidence.source_anchor_ref
        and evidence.artifact_ref
        and evidence.content_hash_ref
        and evidence.replay_bundle_ref
        and evidence.command_record_refs
        and evidence.event_cursor_refs
        and evidence.outbox_refs
    )


def product_availability_site_replay_passes(
    result: ProductAvailabilitySiteResult,
) -> bool:
    if result.completion_result == CompletenessResult.PASS:
        return bool(result.replay_bundle_refs and result.command_record_refs and result.outbox_refs)
    return bool(result.failure_type and result.diagnostics)


def product_availability_report_replay_passes(
    report: ProductAvailabilityBenchmarkReport,
) -> bool:
    return bool(report.replay_bundle_refs and report.command_record_refs and report.outbox_refs)


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-").replace(":", "-")
