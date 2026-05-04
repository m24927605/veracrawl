"""Query-driven product discovery benchmark runtime."""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib import robotparser
from urllib.parse import urljoin, urlparse

from veracrawl.benchmarks.product_availability import (
    ProductAvailabilityAgentBinding,
    ProductAvailabilityBenchmarkResult,
    ProductAvailabilityModelBinding,
    run_product_availability_benchmark,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
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
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    AgentRole,
    CompletenessResult,
    ProductDiscoveryDecisionType,
    ProductDiscoveryFailureType,
    ToolCallStatus,
)
from veracrawl.contracts.network import LiveHttpAcquisitionReport
from veracrawl.contracts.offer_projection import SortableProductOfferRecord
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkManifest,
    ProductAvailabilityTargetSpec,
)
from veracrawl.contracts.product_discovery import (
    ProductDiscoveryBenchmarkManifest,
    ProductDiscoveryCandidate,
    ProductDiscoveryRunReport,
    ProductDiscoverySourceSpec,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.fetch.live_http import execute_live_http_acquisition
from veracrawl.fetch.network_acquisition import is_private_network_url, url_origin
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort
from veracrawl.ports.network import NetworkSourceAdapterPort

DiscoveryNetworkAdapterFactory = Callable[
    [str, ProductDiscoverySourceSpec],
    NetworkSourceAdapterPort,
]
ProductNetworkAdapterFactory = Callable[
    [str, ProductAvailabilityTargetSpec],
    NetworkSourceAdapterPort,
]
DiscoveryRobotsFetcher = Callable[[ProductDiscoverySourceSpec], RobotsFetchResult]
ProductRobotsFetcher = Callable[[ProductAvailabilityTargetSpec], RobotsFetchResult]
_ContextPayloadSetter = Callable[[str, str], None]
_TokenUsageGetter = Callable[[str], dict[str, int]]


@dataclass(frozen=True)
class ProductDiscoveryBenchmarkResult:
    report: ProductDiscoveryRunReport
    candidates: list[ProductDiscoveryCandidate]
    derived_product_availability_manifest: ProductAvailabilityBenchmarkManifest | None
    product_availability_result: ProductAvailabilityBenchmarkResult | None
    ranked_offers: list[SortableProductOfferRecord]
    model_requests: list[ModelRequest]
    model_responses: list[ModelResponse]
    model_call_traces: list[ModelCallTrace]
    agent_run_requests: list[AgentRunRequest]
    agent_run_results: list[AgentRunResult]
    agent_action_traces: list[AgentActionTrace]
    tool_call_traces: list[ToolCallTrace]
    context_bundle_traces: list[ContextBundleTrace]


@dataclass(frozen=True)
class _CandidateLink:
    url: str
    raw_anchor_text: str
    matched_identity_terms: tuple[str, ...]
    source_kind: str


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
class _RobotsCheck:
    policy_ref: Ref
    failure_type: ProductDiscoveryFailureType | None = None
    missing_field: str = ""
    diagnostics: tuple[str, ...] = ()


def run_product_discovery_benchmark(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    profile: str,
    store: ProductionPersistenceStore,
    discovery_adapter_factory: DiscoveryNetworkAdapterFactory,
    product_adapter_factory: ProductNetworkAdapterFactory,
    discovery_robots_fetcher: DiscoveryRobotsFetcher,
    product_robots_fetcher: ProductRobotsFetcher,
    model_binding: ProductAvailabilityModelBinding,
    agent_binding: ProductAvailabilityAgentBinding,
) -> ProductDiscoveryBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    candidates: list[ProductDiscoveryCandidate] = []
    blocked_source_refs: list[Ref] = []
    source_result_refs: list[Ref] = []
    diagnostics: list[str] = []
    model_requests: list[ModelRequest] = []
    model_responses: list[ModelResponse] = []
    model_call_traces: list[ModelCallTrace] = []
    agent_run_requests: list[AgentRunRequest] = []
    agent_run_results: list[AgentRunResult] = []
    agent_action_traces: list[AgentActionTrace] = []
    tool_call_traces: list[ToolCallTrace] = []
    context_bundle_traces: list[ContextBundleTrace] = []
    seen_urls: set[str] = set()

    if model_binding.port is None or agent_binding.port is None:
        report = _failure_report(
            manifest=manifest,
            failure=ProductDiscoveryFailureType.ADAPTER_UNAVAILABLE,
            missing_field="adapter_runtime_refs",
            diagnostics=["model provider or agent runtime adapter unavailable"],
            source_result_refs=[],
        )
        return ProductDiscoveryBenchmarkResult(
            report=report,
            candidates=[],
            derived_product_availability_manifest=None,
            product_availability_result=None,
            ranked_offers=[],
            model_requests=[],
            model_responses=[],
            model_call_traces=[],
            agent_run_requests=[],
            agent_run_results=[],
            agent_action_traces=[],
            tool_call_traces=[],
            context_bundle_traces=[],
        )

    for source in manifest.source_specs:
        source_run_ref = f"{manifest.id}:{source.id}:search"
        policy_failure = _source_policy_failure(manifest, source)
        if policy_failure is not None:
            failure, messages = policy_failure
            blocked_ref = f"blocked-source:{manifest.id}:{source.id}:{failure.value}"
            blocked_source_refs.append(blocked_ref)
            diagnostics.extend(messages)
            source_result_refs.append(blocked_ref)
            continue

        robots = _check_robots(source=source, robots_fetcher=discovery_robots_fetcher)
        if robots.failure_type is not None:
            blocked_ref = f"blocked-source:{manifest.id}:{source.id}:{robots.failure_type.value}"
            blocked_source_refs.append(blocked_ref)
            diagnostics.extend(robots.diagnostics)
            source_result_refs.append(blocked_ref)
            continue

        live_result = execute_live_http_acquisition(
            fixture_id=source_run_ref,
            scenario="success",
            target_url=source.search_url,
            store=store,
            adapter=discovery_adapter_factory(source_run_ref, source),
            profile=profile,
            egress_allowlist=[source.allowed_origin],
            allow_private_network=False,
            size_budget_bytes=source.size_budget_bytes,
            timeout_ms=source.timeout_ms,
        )
        live_report = live_result.report
        source_result_refs.append(live_report.id)
        network_result = (
            live_result.network_outcome.network_result
            if live_result.network_outcome is not None
            else None
        )
        if live_report.completion_result != CompletenessResult.PASS or network_result is None:
            blocked_ref = f"blocked-source:{manifest.id}:{source.id}:live-http"
            blocked_source_refs.append(blocked_ref)
            diagnostics.extend(live_report.diagnostics or [live_report.operator_status])
            continue

        decision = _build_decision_bundle(
            manifest=manifest,
            source=source,
            live_http_report=live_report,
            decision_type=ProductDiscoveryDecisionType.CANDIDATE_SELECTION,
            model_binding=model_binding,
            agent_binding=agent_binding,
            model_port=model_binding.port,
            agent_port=agent_binding.port,
        )
        model_requests.append(decision.model_request)
        model_responses.append(decision.model_response)
        model_call_traces.append(decision.model_call_trace)
        agent_run_requests.append(decision.agent_run_request)
        agent_run_results.append(decision.agent_run_result)
        agent_action_traces.append(decision.agent_action_trace)
        tool_call_traces.append(decision.tool_call_trace)
        context_bundle_traces.append(decision.context_bundle_trace)

        links = _discover_candidate_links(
            body=network_result.body_text,
            base_url=network_result.response.final_url,
            source=source,
            manifest=manifest,
        )
        if not links:
            blocked_ref = f"blocked-source:{manifest.id}:{source.id}:no-candidates"
            blocked_source_refs.append(blocked_ref)
            diagnostics.append(f"{source.site_name} search page produced no candidate URLs")
            continue

        for link in links[: source.max_candidates]:
            if len(candidates) >= manifest.max_total_candidates:
                break
            if link.url in seen_urls:
                continue
            seen_urls.add(link.url)
            rank = len(candidates) + 1
            candidates.append(
                _candidate_from_link(
                    manifest=manifest,
                    source=source,
                    link=link,
                    rank=rank,
                    live_report=live_report,
                    decision=decision,
                )
            )

    if not candidates:
        report = _failure_report(
            manifest=manifest,
            failure=ProductDiscoveryFailureType.NO_CANDIDATES,
            missing_field="discovered_candidate_refs",
            diagnostics=diagnostics or ["no source-backed product candidates were discovered"],
            source_result_refs=source_result_refs,
            blocked_source_refs=blocked_source_refs,
        )
        return ProductDiscoveryBenchmarkResult(
            report=report,
            candidates=[],
            derived_product_availability_manifest=None,
            product_availability_result=None,
            ranked_offers=[],
            model_requests=model_requests,
            model_responses=model_responses,
            model_call_traces=model_call_traces,
            agent_run_requests=agent_run_requests,
            agent_run_results=agent_run_results,
            agent_action_traces=agent_action_traces,
            tool_call_traces=tool_call_traces,
            context_bundle_traces=context_bundle_traces,
        )

    availability_manifest = _derived_product_availability_manifest(
        manifest=manifest,
        candidates=candidates,
    )
    product_result = run_product_availability_benchmark(
        manifest=availability_manifest,
        profile=profile,
        store=store,
        adapter_factory=product_adapter_factory,
        robots_fetcher=product_robots_fetcher,
        model_binding=model_binding,
        agent_binding=agent_binding,
        browser_adapter_factory=None,
        browser_source_required=False,
    )
    ranked_offers = _ranked_offers(product_result, limit=manifest.ranking_limit)
    report = _build_report(
        manifest=manifest,
        candidates=candidates,
        source_result_refs=source_result_refs,
        blocked_source_refs=blocked_source_refs,
        diagnostics=diagnostics,
        product_result=product_result,
        ranked_offers=ranked_offers,
        model_call_traces=model_call_traces + product_result.model_call_traces,
        agent_action_traces=agent_action_traces + product_result.agent_action_traces,
        tool_call_traces=tool_call_traces + product_result.tool_call_traces,
        context_bundle_traces=context_bundle_traces + product_result.context_bundle_traces,
    )
    return ProductDiscoveryBenchmarkResult(
        report=report,
        candidates=candidates,
        derived_product_availability_manifest=availability_manifest,
        product_availability_result=product_result,
        ranked_offers=ranked_offers,
        model_requests=model_requests + product_result.model_requests,
        model_responses=model_responses + product_result.model_responses,
        model_call_traces=model_call_traces + product_result.model_call_traces,
        agent_run_requests=agent_run_requests + product_result.agent_run_requests,
        agent_run_results=agent_run_results + product_result.agent_run_results,
        agent_action_traces=agent_action_traces + product_result.agent_action_traces,
        tool_call_traces=tool_call_traces + product_result.tool_call_traces,
        context_bundle_traces=context_bundle_traces + product_result.context_bundle_traces,
    )


def _source_policy_failure(
    manifest: ProductDiscoveryBenchmarkManifest,
    source: ProductDiscoverySourceSpec,
) -> tuple[ProductDiscoveryFailureType, list[str]] | None:
    allowed = {spec.allowed_origin for spec in manifest.source_specs}
    if source.allowed_origin not in allowed or url_origin(source.search_url) not in allowed:
        return (
            ProductDiscoveryFailureType.LIVE_HTTP_FAILED,
            [f"{source.search_url} is outside discovery allowlist"],
        )
    if is_private_network_url(source.search_url) or is_private_network_url(source.robots_url):
        return (
            ProductDiscoveryFailureType.LIVE_HTTP_FAILED,
            ["product discovery denied private-network search target"],
        )
    return None


def _check_robots(
    *,
    source: ProductDiscoverySourceSpec,
    robots_fetcher: DiscoveryRobotsFetcher,
) -> _RobotsCheck:
    policy_ref = f"policy:{source.id}:robots"
    try:
        robots = robots_fetcher(source)
    except OSError as exc:
        return _RobotsCheck(
            policy_ref=policy_ref,
            failure_type=ProductDiscoveryFailureType.NETWORK_UNAVAILABLE,
            missing_field="robots_url",
            diagnostics=(f"robots preflight failed: {exc}",),
        )
    if robots.status_code not in source.allowed_robots_status_codes:
        return _RobotsCheck(
            policy_ref=f"{policy_ref}:{robots.status_code}",
            failure_type=ProductDiscoveryFailureType.ROBOTS_DENIED,
            missing_field="robots_status_code",
            diagnostics=(f"robots status {robots.status_code} is not allowed",),
        )
    if robots.status_code == 200:
        parser = robotparser.RobotFileParser()
        parser.set_url(source.robots_url)
        parser.parse(robots.body_text.splitlines())
        if not parser.can_fetch("VeraCrawl-real-benchmark/1", source.search_url):
            return _RobotsCheck(
                policy_ref=f"{policy_ref}:deny",
                failure_type=ProductDiscoveryFailureType.ROBOTS_DENIED,
                missing_field="robots_policy",
                diagnostics=(f"robots policy disallows {source.search_url}",),
            )
    return _RobotsCheck(policy_ref=f"{policy_ref}:allow:{robots.status_code}")


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._href = html.unescape(href)
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = " ".join(" ".join(self._parts).split())
            self.links.append((self._href, text))
            self._href = None
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)


def _discover_candidate_links(
    *,
    body: str,
    base_url: str,
    source: ProductDiscoverySourceSpec,
    manifest: ProductDiscoveryBenchmarkManifest,
) -> list[_CandidateLink]:
    parser = _AnchorParser()
    parser.feed(body)
    raw_links = [(href, text, "anchor") for href, text in parser.links]
    for pattern in source.candidate_url_patterns:
        for match in re.finditer(pattern, body, flags=re.IGNORECASE):
            raw = match.group(1) if match.groups() else match.group(0)
            raw_links.append((html.unescape(raw), "", "pattern"))

    candidates: list[_CandidateLink] = []
    seen: set[str] = set()
    for raw_url, raw_text, source_kind in raw_links:
        candidate_url = _normalize_candidate_url(raw_url, base_url)
        if candidate_url is None or candidate_url in seen:
            continue
        if not candidate_url.startswith(source.allowed_origin):
            continue
        if candidate_url == source.search_url:
            continue
        if _excluded(candidate_url, raw_text, source):
            continue
        if not _matches_candidate_pattern(candidate_url, source):
            continue
        if _has_rejected_identity(
            f"{raw_text} {candidate_url.replace('-', ' ').replace('/', ' ')}",
            manifest.rejected_identity_terms,
        ):
            continue
        matched = tuple(
            _matched_terms(
                f"{raw_text} {candidate_url}",
                manifest.required_identity_terms,
            )
        )
        seen.add(candidate_url)
        candidates.append(
            _CandidateLink(
                url=candidate_url,
                raw_anchor_text=raw_text,
                matched_identity_terms=matched,
                source_kind=source_kind,
            )
        )
    return sorted(
        candidates,
        key=lambda item: (
            -len(item.matched_identity_terms),
            0 if item.source_kind == "anchor" else 1,
            item.url,
        ),
    )


def _normalize_candidate_url(raw_url: str, base_url: str) -> str | None:
    stripped = html.unescape(raw_url).strip().strip("\"'")
    if not stripped or stripped.startswith(("javascript:", "mailto:", "tel:", "#")):
        return None
    absolute = urljoin(base_url, stripped)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    without_fragment = parsed._replace(fragment="").geturl()
    if is_private_network_url(without_fragment):
        return None
    return without_fragment


def _excluded(candidate_url: str, raw_text: str, source: ProductDiscoverySourceSpec) -> bool:
    haystack = f"{candidate_url} {raw_text}"
    built_in = (
        r"/cart\b",
        r"/login\b",
        r"/signin\b",
        r"/account\b",
        r"/compare\b",
        r"/coupon\b",
        r"/activity\b",
        r"/campaign\b",
        r"javascript:",
    )
    for pattern in (*built_in, *source.exclude_url_patterns):
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            return True
    return False


def _matches_candidate_pattern(candidate_url: str, source: ProductDiscoverySourceSpec) -> bool:
    return any(
        re.search(pattern, candidate_url, flags=re.IGNORECASE)
        for pattern in source.candidate_url_patterns
    )


def _has_rejected_identity(raw_text: str, rejected_terms: list[str]) -> bool:
    if not raw_text:
        return False
    normalized = re.sub(r"[^0-9A-Za-z]+", " ", raw_text).casefold()
    for term in rejected_terms:
        folded_term = term.casefold()
        if " " in folded_term:
            if folded_term in normalized:
                return True
            continue
        if re.search(
            rf"(?<![0-9a-z]){re.escape(folded_term)}(?![0-9a-z])",
            normalized,
        ):
            return True
    return False


def _matched_terms(haystack: str, terms: list[str]) -> list[str]:
    folded = haystack.casefold()
    return [term for term in terms if term.casefold() in folded]


def _candidate_from_link(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    source: ProductDiscoverySourceSpec,
    link: _CandidateLink,
    rank: int,
    live_report: LiveHttpAcquisitionReport,
    decision: _DecisionBundle,
) -> ProductDiscoveryCandidate:
    source_anchor_ref = (
        f"source-anchor:{manifest.id}:{source.id}:candidate:"
        f"{rank}:{stable_hash(link.url)[:12]}"
    )
    artifact_ref = live_report.artifact_refs[0]
    content_hash_ref = live_report.content_hash_refs[0]
    canonical_url_ref = live_report.canonical_url_refs[0]
    return ProductDiscoveryCandidate(
        id=f"product-discovery-candidate:{manifest.id}:{source.id}:{rank}",
        fixture_id=manifest.id,
        source_spec_ref=f"product-discovery-source:{manifest.id}:{source.id}",
        site_name=source.site_name,
        query=manifest.query,
        search_url=source.search_url,
        candidate_url=link.url,
        candidate_rank=rank,
        raw_anchor_text=link.raw_anchor_text,
        matched_identity_terms=list(link.matched_identity_terms),
        source_anchor_ref=source_anchor_ref,
        artifact_ref=artifact_ref,
        content_hash_ref=content_hash_ref,
        canonical_url_ref=canonical_url_ref,
        model_call_trace_ref=decision.model_call_trace.id,
        agent_action_trace_ref=decision.agent_action_trace.id,
        tool_call_trace_refs=[decision.tool_call_trace.id],
        context_bundle_trace_ref=decision.context_bundle_trace.id,
        policy_decision_refs=sorted(
            set(live_report.policy_decision_refs + decision.agent_action_trace.policy_decision_refs)
        ),
        command_record_refs=sorted(
            set(
                live_report.command_record_refs
                + [f"command:{manifest.id}:{source.id}:candidate:{rank}"]
            )
        ),
        event_cursor_refs=sorted(
            set(
                live_report.event_cursor_refs
                + [f"event-cursor:{manifest.id}:{source.id}:candidate:{rank}"]
            )
        ),
        outbox_refs=sorted(
            set(live_report.outbox_refs + [f"outbox:{manifest.id}:{source.id}:candidate:{rank}"])
        ),
        replay_bundle_ref=f"replay-bundle:{manifest.id}:{source.id}:candidate:{rank}",
        completion_result=CompletenessResult.PASS,
    )


def _derived_product_availability_manifest(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    candidates: list[ProductDiscoveryCandidate],
) -> ProductAvailabilityBenchmarkManifest:
    source_by_ref = {
        f"product-discovery-source:{manifest.id}:{source.id}": source
        for source in manifest.source_specs
    }
    target_specs = []
    for candidate in candidates:
        source = source_by_ref[candidate.source_spec_ref]
        target_specs.append(
            ProductAvailabilityTargetSpec(
                id=_target_id(candidate),
                site_name=candidate.site_name,
                target_url=candidate.candidate_url,
                robots_url=source.robots_url,
                allowed_origin=source.allowed_origin,
                required_identity_terms=manifest.required_identity_terms,
                rejected_identity_terms=manifest.rejected_identity_terms,
                allowed_robots_status_codes=source.allowed_robots_status_codes,
                timeout_ms=source.timeout_ms,
                size_budget_bytes=source.size_budget_bytes,
                expected_site_result=CompletenessResult.PASS,
            )
        )
    return ProductAvailabilityBenchmarkManifest(
        id=f"{manifest.id}:derived-product-availability",
        scenario=manifest.scenario,
        profile_refs=manifest.profile_refs,
        product_name=manifest.product_name,
        brand=manifest.brand,
        required_identity_terms=manifest.required_identity_terms,
        rejected_identity_terms=manifest.rejected_identity_terms,
        target_specs=target_specs,
        provider_names=manifest.provider_names,
        framework_names=manifest.framework_names,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="product_availability_benchmark_completed",
        negative_case=False,
        required_ref_types=[
            "live_http",
            "model_call_trace",
            "agent_action_trace",
            "tool_call_trace",
            "context_bundle_trace",
            "source_anchor",
            "field_evidence",
            "offer_projection",
            "command_event_outbox",
            "replay",
        ],
    )


def _target_id(candidate: ProductDiscoveryCandidate) -> str:
    parsed = urlparse(candidate.candidate_url)
    path_slug = re.sub(r"[^a-zA-Z0-9]+", "-", parsed.path.strip("/")).strip("-").lower()
    if not path_slug:
        path_slug = stable_hash(candidate.candidate_url)[:12]
    digest = stable_hash(candidate.candidate_url)[:8]
    return f"{_slug(candidate.site_name)}-{path_slug[:48]}-{digest}"


def _ranked_offers(
    product_result: ProductAvailabilityBenchmarkResult,
    *,
    limit: int,
) -> list[SortableProductOfferRecord]:
    offers_by_id = {offer.id: offer for offer in product_result.offer_records}
    ranked_refs = product_result.offer_projection_report.sorted_by_price_refs
    ranked = [offers_by_id[ref] for ref in ranked_refs if ref in offers_by_id]
    return sorted(
        ranked,
        key=lambda offer: (
            offer.price_sort_amount is None,
            offer.price_sort_amount or 0.0,
            offer.delivery_sort_rank,
            offer.delivery_eta_max_days or 999_999,
            offer.site_name,
            offer.offer_url,
        ),
    )[:limit]


def _build_report(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    candidates: list[ProductDiscoveryCandidate],
    source_result_refs: list[Ref],
    blocked_source_refs: list[Ref],
    diagnostics: list[str],
    product_result: ProductAvailabilityBenchmarkResult,
    ranked_offers: list[SortableProductOfferRecord],
    model_call_traces: list[ModelCallTrace],
    agent_action_traces: list[AgentActionTrace],
    tool_call_traces: list[ToolCallTrace],
    context_bundle_traces: list[ContextBundleTrace],
) -> ProductDiscoveryRunReport:
    availability_report = product_result.report
    offer_projection = product_result.offer_projection_report
    policy_refs = sorted(
        set(
            _collect("policy_decision_refs", candidates)
            + availability_report.policy_decision_refs
            + offer_projection.policy_decision_refs
        )
    )
    command_refs = sorted(
        set(
            _collect("command_record_refs", candidates)
            + availability_report.command_record_refs
            + offer_projection.command_record_refs
            + [f"command:{manifest.id}:product-discovery-report"]
        )
    )
    event_refs = sorted(
        set(
            _collect("event_cursor_refs", candidates)
            + availability_report.event_cursor_refs
            + offer_projection.event_cursor_refs
            + [f"event-cursor:{manifest.id}:product-discovery-report"]
        )
    )
    outbox_refs = sorted(
        set(
            _collect("outbox_refs", candidates)
            + availability_report.outbox_refs
            + offer_projection.outbox_refs
            + [f"outbox:{manifest.id}:product-discovery-report"]
        )
    )
    replay_refs = sorted(
        set(
            [candidate.replay_bundle_ref for candidate in candidates]
            + availability_report.replay_bundle_refs
            + offer_projection.replay_bundle_refs
            + [f"replay-bundle:{manifest.id}:product-discovery-report"]
        )
    )
    report_diagnostics = list(diagnostics)
    if offer_projection.diagnostics:
        report_diagnostics.extend(offer_projection.diagnostics)
    if ranked_offers and not (
        blocked_source_refs
        or availability_report.blocked_site_result_refs
        or offer_projection.blocked_offer_refs
    ):
        completion = CompletenessResult.PASS
        operator_status = "product_discovery_ranked_offers_completed"
        failure = None
    elif ranked_offers:
        completion = CompletenessResult.NEEDS_REVIEW
        operator_status = "product_discovery_partial_sources_blocked"
        failure = None
        if not report_diagnostics:
            report_diagnostics.append("some discovery or product sources were blocked")
    else:
        completion = CompletenessResult.FAIL
        operator_status = "product_discovery_no_sortable_offers"
        failure = ProductDiscoveryFailureType.NO_SORTABLE_OFFERS
        if not report_diagnostics:
            report_diagnostics.append("no discovered candidates produced sortable offers")
    return ProductDiscoveryRunReport(
        id=f"product-discovery-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}:product-discovery",
        query=manifest.query,
        product_name=manifest.product_name,
        source_count=len(manifest.source_specs),
        source_result_refs=source_result_refs,
        discovered_candidate_refs=[candidate.id for candidate in candidates],
        accepted_candidate_refs=[candidate.id for candidate in candidates],
        blocked_source_refs=sorted(
            set(
                blocked_source_refs
                + availability_report.blocked_source_refs
                + offer_projection.blocked_source_refs
            )
        ),
        derived_product_availability_manifest_ref=(
            f"product-availability-manifest:{manifest.id}:derived"
        ),
        product_availability_report_ref=availability_report.id,
        offer_projection_report_ref=offer_projection.id,
        ranked_offer_refs=[offer.id for offer in ranked_offers],
        model_call_trace_refs=[trace.id for trace in model_call_traces],
        agent_action_trace_refs=[trace.id for trace in agent_action_traces],
        tool_call_trace_refs=[trace.id for trace in tool_call_traces],
        context_bundle_trace_refs=[trace.id for trace in context_bundle_traces],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        replay_bundle_refs=replay_refs,
        failure_report_refs=(
            [f"failure:{manifest.id}:{failure.value}"] if failure is not None else []
        ),
        missing_ref_fields=(
            ["ranked_offer_refs"]
            if failure == ProductDiscoveryFailureType.NO_SORTABLE_OFFERS
            else []
        ),
        failure_type=failure,
        operator_status=operator_status,
        completion_result=completion,
        diagnostics=report_diagnostics,
    )


def _failure_report(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    failure: ProductDiscoveryFailureType,
    missing_field: str,
    diagnostics: list[str],
    source_result_refs: list[Ref],
    blocked_source_refs: list[Ref] | None = None,
) -> ProductDiscoveryRunReport:
    return ProductDiscoveryRunReport(
        id=f"product-discovery-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}:product-discovery",
        query=manifest.query,
        product_name=manifest.product_name,
        source_count=len(manifest.source_specs),
        source_result_refs=source_result_refs,
        blocked_source_refs=blocked_source_refs
        or [f"blocked-source:{manifest.id}:{failure.value}"],
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=diagnostics,
    )


def _build_decision_bundle(
    *,
    manifest: ProductDiscoveryBenchmarkManifest,
    source: ProductDiscoverySourceSpec,
    live_http_report: LiveHttpAcquisitionReport,
    decision_type: ProductDiscoveryDecisionType,
    model_binding: ProductAvailabilityModelBinding,
    agent_binding: ProductAvailabilityAgentBinding,
    model_port: ModelProviderPort,
    agent_port: AgentRuntimePort,
) -> _DecisionBundle:
    decision_slug = decision_type.value
    role = (
        AgentRole.PLANNER
        if decision_type == ProductDiscoveryDecisionType.QUERY_PLANNING
        else AgentRole.FRONTIER
    )
    run_id = f"run:{manifest.id}:{source.id}:{decision_slug}"
    policy_refs = [
        f"policy:{manifest.id}:{source.id}:source-scope",
        f"policy:{manifest.id}:{source.id}:prompt-context",
        f"policy:{manifest.id}:{source.id}:candidate-selection",
    ]
    context_trace = ContextBundleTrace(
        id=f"context-bundle-trace:{manifest.id}:{source.id}:{decision_slug}",
        run_id=run_id,
        agent_id=f"agent:{manifest.id}:{source.id}:{role.value}",
        context_ref_schema=f"schema:{manifest.id}:product-discovery-context",
        included_context_refs=sorted(
            set(
                [
                    live_http_report.id,
                    *live_http_report.source_observation_refs,
                    *live_http_report.artifact_refs,
                    *live_http_report.content_hash_refs,
                ]
            )
        ),
        sanitized_context_ref=f"sanitized-context:{manifest.id}:{source.id}:{decision_slug}",
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
        credential_exposure_check_ref=f"credential-exposure-check:{manifest.id}:{source.id}:none",
        evidence_refs=live_http_report.artifact_refs,
    )
    agent_request = AgentRunRequest(
        id=f"agent-run-request:{manifest.id}:{source.id}:{decision_slug}",
        run_id=run_id,
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        objective_ref=f"objective:{manifest.id}:query-product-discovery",
        context_bundle_id=context_trace.id,
        allowed_tool_spec_refs=[f"tool-spec:{manifest.id}:{decision_slug}:source-read"],
        required_output_schema_ref=f"schema:{manifest.id}:{decision_slug}:output",
        loop_budget_ref=f"loop-budget:{manifest.id}:{source.id}:{decision_slug}",
        policy_decision_refs=policy_refs,
    )
    model_request = ModelRequest(
        id=f"model-request:{manifest.id}:{source.id}:{decision_slug}:{_slug(model_binding.provider_name)}",
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
        f"fixture={manifest.id}; query={manifest.query}; product={manifest.product_name}; "
        f"site={source.site_name}; search_url={source.search_url}; "
        f"decision={decision_type.value}; source_refs={context_trace.included_context_refs}. "
        "Recommend candidate discovery strategy only. Candidate URLs must be read "
        "from source artifacts and model output cannot be source evidence."
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
        id=f"model-call-trace:{manifest.id}:{source.id}:{decision_slug}:{_slug(model_binding.provider_name)}",
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
        id=f"tool-call-trace:{manifest.id}:{source.id}:{decision_slug}:source-read",
        run_id=run_id,
        agent_action_trace_id=agent_result.agent_action_trace_id,
        tool_spec_id=agent_request.allowed_tool_spec_refs[0],
        tool_name=f"{decision_slug}_source_read",
        tool_version="1",
        input_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-input",
        output_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-output",
        input_ref=context_trace.sanitized_context_ref,
        output_ref=f"tool-output:{manifest.id}:{source.id}:{decision_slug}",
        command_envelope_id=f"command-envelope:{manifest.id}:{source.id}:{decision_slug}",
        command_result_id=f"command-result:{manifest.id}:{source.id}:{decision_slug}",
        policy_decision_refs=policy_refs,
        status=ToolCallStatus.EXECUTED,
    )
    agent_action_trace = AgentActionTrace(
        id=agent_result.agent_action_trace_id,
        run_id=run_id,
        objective_id=f"objective:{manifest.id}:query-product-discovery",
        agent_id=f"agent:{manifest.id}:{source.id}:{role.value}",
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        model_call_trace_refs=[model_call_trace.id],
        context_bundle_trace_id=context_trace.id,
        tool_call_trace_refs=[tool_trace.id],
        command_result_refs=[tool_trace.command_result_id],
        policy_decision_refs=policy_refs,
        input_refs=context_trace.included_context_refs,
        output_refs=[agent_result.output_ref],
        reasoning_summary_ref=f"reasoning-summary:{manifest.id}:{source.id}:{decision_slug}",
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


def _collect(field: str, items: Sequence[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        value = getattr(item, field)
        if isinstance(value, list):
            refs.extend(value)
        elif isinstance(value, str):
            refs.append(value)
    return sorted(set(refs))


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
