"""Multi-page deep crawl frontier benchmark runtime."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.deep_crawl import (
    DeepCrawlPageObservation,
    DeepCrawlPageSpec,
    DeepCrawlQualityManifest,
    DeepCrawlQualityReport,
    DeepCrawlSiteSpec,
    DeepCrawlStopReasonRecord,
    FrontierDecisionTrace,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    DeepCrawlFailureType,
    DeepCrawlFrontierAction,
    DeepCrawlPageType,
    DeepCrawlStopReason,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class DeepCrawlCorpusResult:
    report: DeepCrawlQualityReport
    frontier_decisions: list[FrontierDecisionTrace]
    page_observations: list[DeepCrawlPageObservation]
    stop_reasons: list[DeepCrawlStopReasonRecord]


_DIRECT_FAILURES: dict[str, tuple[DeepCrawlFailureType, str]] = {
    "deep-crawl-duplicate-loop": (
        DeepCrawlFailureType.DUPLICATE_NOT_SUPPRESSED,
        "duplicate_suppression_refs",
    ),
    "deep-crawl-off-origin-pollution": (
        DeepCrawlFailureType.FRONTIER_POLLUTION,
        "skipped_link_refs",
    ),
    "deep-crawl-robots-denied": (
        DeepCrawlFailureType.ROBOTS_DENIAL_BYPASSED,
        "policy_decision_refs",
    ),
    "deep-crawl-budget-exhausted": (
        DeepCrawlFailureType.BUDGET_EXHAUSTED,
        "rate_budget_ref",
    ),
    "deep-crawl-infinite-pagination": (
        DeepCrawlFailureType.INFINITE_PAGINATION,
        "stop_reason_refs",
    ),
    "deep-crawl-replay-mismatch": (
        DeepCrawlFailureType.REPLAY_MISMATCH,
        "replay_bundle_refs",
    ),
}


def run_deep_crawl_quality_corpus(
    *,
    manifest: DeepCrawlQualityManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> DeepCrawlCorpusResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"deep crawl corpus {manifest.id} does not support {profile}")

    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        report = _direct_failure_report(manifest, failure, missing)
        store.save_canonical_model("deep_crawl_reports", report.id, report)
        return DeepCrawlCorpusResult(
            report=report,
            frontier_decisions=[],
            page_observations=[],
            stop_reasons=[],
        )

    expanded_sites = [_expand_site_spec(site) for site in manifest.site_specs]
    decisions: list[FrontierDecisionTrace] = []
    observations: list[DeepCrawlPageObservation] = []
    stop_reasons: list[DeepCrawlStopReasonRecord] = []
    for site in expanded_sites:
        site_decisions, site_observations, site_stop = _run_site(
            manifest_id=manifest.id,
            site=site,
            store=store,
            decision_offset=len(decisions),
        )
        decisions.extend(site_decisions)
        observations.extend(site_observations)
        stop_reasons.append(site_stop)

    report = _build_report(
        manifest=manifest,
        sites=expanded_sites,
        decisions=decisions,
        observations=observations,
        stop_reasons=stop_reasons,
    )
    store.save_canonical_model("deep_crawl_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("deep_crawl_reports", report.id, report)
    return DeepCrawlCorpusResult(
        report=report,
        frontier_decisions=decisions,
        page_observations=observations,
        stop_reasons=stop_reasons,
    )


def _run_site(
    *,
    manifest_id: str,
    site: DeepCrawlSiteSpec,
    store: ProductionPersistenceStore,
    decision_offset: int,
) -> tuple[list[FrontierDecisionTrace], list[DeepCrawlPageObservation], DeepCrawlStopReasonRecord]:
    pages_by_url = {page.url: page for page in site.page_specs}
    decisions: list[FrontierDecisionTrace] = []
    observations: list[DeepCrawlPageObservation] = []
    frontier: list[tuple[str, int, Ref | None, list[Ref]]] = [
        (url, 0, None, [f"source-anchor:{site.id}:seed:{index}"])
        for index, url in enumerate(site.seed_urls, start=1)
    ]
    seen_canonical_urls: set[str] = set()
    stop_reason = DeepCrawlStopReason.FRONTIER_EXHAUSTED

    while frontier:
        target_url, depth, source_page_ref, source_anchor_refs = frontier.pop(0)
        if len(observations) >= site.max_pages:
            frontier.insert(0, (target_url, depth, source_page_ref, source_anchor_refs))
            stop_reason = DeepCrawlStopReason.MAX_PAGES_REACHED
            break

        page = pages_by_url.get(target_url)
        skip_reason = _skip_reason(site, page, target_url, depth)
        if skip_reason is not None:
            decision = _record_frontier_decision(
                manifest_id=manifest_id,
                site=site,
                index=decision_offset + len(decisions) + 1,
                target_url=target_url,
                canonical_url=page.canonical_url if page else None,
                source_page_ref=source_page_ref,
                depth=depth,
                action=DeepCrawlFrontierAction.SKIP,
                reason=skip_reason,
                source_anchor_refs=source_anchor_refs,
                duplicate_ref=None,
                page=page,
                store=store,
            )
            decisions.append(decision)
            continue

        assert page is not None
        if page.canonical_url in seen_canonical_urls:
            decision = _record_frontier_decision(
                manifest_id=manifest_id,
                site=site,
                index=decision_offset + len(decisions) + 1,
                target_url=target_url,
                canonical_url=page.canonical_url,
                source_page_ref=source_page_ref,
                depth=depth,
                action=DeepCrawlFrontierAction.SKIP,
                reason="duplicate_canonical_suppressed",
                source_anchor_refs=source_anchor_refs,
                duplicate_ref=f"duplicate-suppression:{site.id}:{stable_hash(page.url)[:12]}",
                page=page,
                store=store,
            )
            decisions.append(decision)
            continue

        seen_canonical_urls.add(page.canonical_url)
        action = (
            DeepCrawlFrontierAction.PRIORITIZE
            if page.ai_prioritized
            else DeepCrawlFrontierAction.KEEP
        )
        decision = _record_frontier_decision(
            manifest_id=manifest_id,
            site=site,
            index=decision_offset + len(decisions) + 1,
            target_url=target_url,
            canonical_url=page.canonical_url,
            source_page_ref=source_page_ref,
            depth=depth,
            action=action,
            reason="frontier_policy_allowed",
            source_anchor_refs=source_anchor_refs or page.source_anchor_refs,
            duplicate_ref=None,
            page=page,
            store=store,
        )
        decisions.append(decision)
        observation = _record_page_observation(
            manifest_id=manifest_id,
            site=site,
            page=page,
            decision=decision,
            store=store,
        )
        observations.append(observation)
        for link_url in page.link_urls:
            frontier.append((link_url, depth + 1, page.id, page.source_anchor_refs))

    stop = _record_stop_reason(
        manifest_id=manifest_id,
        site=site,
        reason=stop_reason,
        frontier_remaining_count=len(frontier),
        page_count=len(observations),
        store=store,
    )
    return decisions, observations, stop


def _skip_reason(
    site: DeepCrawlSiteSpec,
    page: DeepCrawlPageSpec | None,
    target_url: str,
    depth: int,
) -> str | None:
    if _is_private_network_url(target_url) or (page is not None and page.private_network):
        return "private_network_skipped"
    if _origin(target_url) != site.allowed_origin:
        return "off_origin_skipped"
    if depth > site.max_depth:
        return "max_depth_skipped"
    if page is None:
        return "unknown_page_skipped"
    if not page.robots_allowed:
        return "robots_denied_skipped"
    return None


def _record_frontier_decision(
    *,
    manifest_id: str,
    site: DeepCrawlSiteSpec,
    index: int,
    target_url: str,
    canonical_url: str | None,
    source_page_ref: Ref | None,
    depth: int,
    action: DeepCrawlFrontierAction,
    reason: str,
    source_anchor_refs: list[Ref],
    duplicate_ref: Ref | None,
    page: DeepCrawlPageSpec | None,
    store: ProductionPersistenceStore,
) -> FrontierDecisionTrace:
    decision_id = f"frontier-decision:{manifest_id}:{site.id}:{index:04d}"
    policy_refs = _policy_refs(site, reason, target_url)
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{decision_id}",
        command_type="record_deep_crawl_frontier_decision",
        target_aggregate_type="FrontierDecisionTrace",
        target_aggregate_id=decision_id,
        event_type="deep_crawl_frontier_decision_recorded",
        output_refs=[decision_id],
        policy_decision_refs=policy_refs,
        store=store,
    )
    ai_prioritized = bool(
        page and page.ai_prioritized and action == DeepCrawlFrontierAction.PRIORITIZE
    )
    graph_refs = (
        list(page.graph_frontier_refs)
        if page and page.graph_frontier_refs
        else [f"graph-frontier:{site.id}:{stable_hash(target_url)[:12]}"]
    )
    link_provenance_refs = [f"link-provenance:{site.id}:{stable_hash(target_url)[:12]}"]
    duplicate_refs = [duplicate_ref] if duplicate_ref else []
    skipped_refs = (
        [f"skipped-link:{site.id}:{stable_hash(target_url + reason)[:12]}"]
        if action == DeepCrawlFrontierAction.SKIP
        else []
    )
    decision = FrontierDecisionTrace(
        id=decision_id,
        site_ref=site.id,
        target_url=target_url,
        canonical_url=canonical_url,
        source_page_ref=source_page_ref,
        depth=depth,
        action=action,
        reason=reason,
        ai_prioritized=ai_prioritized,
        source_anchor_refs=source_anchor_refs
        or (page.source_anchor_refs if page is not None else []),
        link_provenance_refs=link_provenance_refs,
        canonical_url_refs=[f"canonical-url:{stable_hash(canonical_url)[:12]}"]
        if canonical_url
        else [],
        duplicate_suppression_refs=duplicate_refs,
        skipped_link_refs=skipped_refs,
        graph_frontier_refs=graph_refs,
        memory_refs=list(page.memory_refs) if page else [],
        model_call_refs=list(page.model_call_refs) if ai_prioritized and page else [],
        agent_action_refs=list(page.agent_action_refs) if ai_prioritized and page else [],
        tool_call_refs=list(page.tool_call_refs) if ai_prioritized and page else [],
        context_bundle_refs=list(page.context_bundle_refs) if ai_prioritized and page else [],
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        replay_bundle_ref=f"replay-bundle:{decision_id}",
        completion_result=CompletenessResult.PASS,
    )
    store.save_canonical_model("deep_crawl_frontier_decisions", decision.id, decision)
    return decision


def _record_page_observation(
    *,
    manifest_id: str,
    site: DeepCrawlSiteSpec,
    page: DeepCrawlPageSpec,
    decision: FrontierDecisionTrace,
    store: ProductionPersistenceStore,
) -> DeepCrawlPageObservation:
    observation_id = f"deep-crawl-observation:{manifest_id}:{page.id}"
    policy_refs = _policy_refs(site, "page_observed", page.url)
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{observation_id}",
        command_type="record_deep_crawl_page_observation",
        target_aggregate_type="DeepCrawlPageObservation",
        target_aggregate_id=observation_id,
        event_type="deep_crawl_page_observed",
        output_refs=[observation_id],
        policy_decision_refs=policy_refs,
        store=store,
    )
    observation = DeepCrawlPageObservation(
        id=observation_id,
        site_ref=site.id,
        page_spec_ref=page.id,
        url=page.url,
        canonical_url=page.canonical_url,
        page_type=page.page_type,
        depth=page.depth,
        artifact_refs=[page.artifact_ref or f"artifact:{page.id}:html"],
        content_hash_refs=[page.content_hash_ref or stable_hash(page.url)],
        source_anchor_refs=page.source_anchor_refs,
        link_provenance_refs=decision.link_provenance_refs,
        canonical_url_refs=decision.canonical_url_refs,
        duplicate_suppression_refs=decision.duplicate_suppression_refs,
        graph_page_refs=[f"graph-page:{page.id}"],
        graph_frontier_refs=decision.graph_frontier_refs,
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        replay_bundle_ref=f"replay-bundle:{observation_id}",
        completion_result=CompletenessResult.PASS,
    )
    store.save_canonical_model("deep_crawl_page_observations", observation.id, observation)
    return observation


def _record_stop_reason(
    *,
    manifest_id: str,
    site: DeepCrawlSiteSpec,
    reason: DeepCrawlStopReason,
    frontier_remaining_count: int,
    page_count: int,
    store: ProductionPersistenceStore,
) -> DeepCrawlStopReasonRecord:
    stop_id = f"deep-crawl-stop:{manifest_id}:{site.id}"
    policy_refs = [site.rate_budget_ref, site.robots_policy_ref, site.private_network_policy_ref]
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{stop_id}",
        command_type="record_deep_crawl_stop_reason",
        target_aggregate_type="DeepCrawlStopReasonRecord",
        target_aggregate_id=stop_id,
        event_type="deep_crawl_stop_reason_recorded",
        output_refs=[stop_id],
        policy_decision_refs=policy_refs,
        store=store,
    )
    stop = DeepCrawlStopReasonRecord(
        id=stop_id,
        site_ref=site.id,
        reason=reason,
        frontier_remaining_count=frontier_remaining_count,
        page_count=page_count,
        max_depth=site.max_depth,
        max_pages=site.max_pages,
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        replay_bundle_ref=f"replay-bundle:{stop_id}",
        completion_result=CompletenessResult.PASS,
    )
    store.save_canonical_model("deep_crawl_stop_reasons", stop.id, stop)
    return stop


def _build_report(
    *,
    manifest: DeepCrawlQualityManifest,
    sites: list[DeepCrawlSiteSpec],
    decisions: list[FrontierDecisionTrace],
    observations: list[DeepCrawlPageObservation],
    stop_reasons: list[DeepCrawlStopReasonRecord],
) -> DeepCrawlQualityReport:
    required_pages = {
        page.id
        for site in sites
        for page in site.page_specs
        if page.required_for_coverage and page.robots_allowed and not page.private_network
    }
    covered_pages = {
        observation.page_spec_ref
        for observation in observations
        if observation.page_spec_ref in required_pages
    }
    failure_type, diagnostics, missing = _report_failure(
        manifest=manifest,
        required_pages=required_pages,
        covered_pages=covered_pages,
        decisions=decisions,
        stop_reasons=stop_reasons,
    )
    passing = failure_type is None
    return DeepCrawlQualityReport(
        id=f"deep-crawl-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        site_count=len(sites),
        required_page_count=len(required_pages),
        covered_page_count=len(covered_pages),
        observed_page_count=len(observations),
        frontier_decision_count=len(decisions),
        skipped_link_count=sum(
            1 for decision in decisions if decision.action == DeepCrawlFrontierAction.SKIP
        ),
        duplicate_suppressed_count=sum(
            1 for decision in decisions if decision.duplicate_suppression_refs
        ),
        off_origin_skip_count=sum(
            1 for decision in decisions if decision.reason == "off_origin_skipped"
        ),
        robots_denied_skip_count=sum(
            1 for decision in decisions if decision.reason == "robots_denied_skipped"
        ),
        private_network_skip_count=sum(
            1 for decision in decisions if decision.reason == "private_network_skipped"
        ),
        stop_reason_count=len(stop_reasons),
        minimum_site_count=manifest.minimum_site_count,
        minimum_required_page_count=manifest.minimum_required_page_count,
        observation_refs=[item.id for item in observations],
        frontier_decision_refs=[item.id for item in decisions],
        stop_reason_refs=[item.id for item in stop_reasons],
        artifact_refs=_collect("artifact_refs", observations),
        content_hash_refs=_collect("content_hash_refs", observations),
        source_anchor_refs=sorted(
            set(
                _collect("source_anchor_refs", observations)
                + _collect("source_anchor_refs", decisions)
            )
        ),
        link_provenance_refs=sorted(
            set(
                _collect("link_provenance_refs", observations)
                + _collect("link_provenance_refs", decisions)
            )
        ),
        canonical_url_refs=sorted(
            set(
                _collect("canonical_url_refs", observations)
                + _collect("canonical_url_refs", decisions)
            )
        ),
        duplicate_suppression_refs=_collect("duplicate_suppression_refs", decisions),
        graph_refs=sorted(
            set(
                _collect("graph_page_refs", observations)
                + _collect("graph_frontier_refs", decisions)
            )
        ),
        ai_decision_refs=sorted(
            set(
                _collect("model_call_refs", decisions)
                + _collect("agent_action_refs", decisions)
                + _collect("tool_call_refs", decisions)
                + _collect("context_bundle_refs", decisions)
            )
        ),
        policy_decision_refs=sorted(
            set(
                _collect("policy_decision_refs", decisions)
                + _collect("policy_decision_refs", observations)
                + _collect("policy_decision_refs", stop_reasons)
            )
        ),
        command_record_refs=sorted(
            set(
                _collect("command_record_refs", decisions)
                + _collect("command_record_refs", observations)
                + _collect("command_record_refs", stop_reasons)
            )
        ),
        event_cursor_refs=sorted(
            set(
                _collect("event_cursor_refs", decisions)
                + _collect("event_cursor_refs", observations)
                + _collect("event_cursor_refs", stop_reasons)
            )
        ),
        outbox_refs=sorted(
            set(
                _collect("outbox_refs", decisions)
                + _collect("outbox_refs", observations)
                + _collect("outbox_refs", stop_reasons)
            )
        ),
        replay_bundle_refs=sorted(
            set(
                _collect_one("replay_bundle_ref", decisions)
                + _collect_one("replay_bundle_ref", observations)
                + _collect_one("replay_bundle_ref", stop_reasons)
            )
        ),
        failure_report_refs=[f"failure:{manifest.id}:{failure_type.value}"]
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "deep_crawl_completed",
        completion_result=CompletenessResult.PASS if passing else CompletenessResult.FAIL,
    )


def _report_failure(
    *,
    manifest: DeepCrawlQualityManifest,
    required_pages: set[str],
    covered_pages: set[str],
    decisions: list[FrontierDecisionTrace],
    stop_reasons: list[DeepCrawlStopReasonRecord],
) -> tuple[DeepCrawlFailureType | None, list[str], list[str]]:
    if len(manifest.site_specs) < manifest.minimum_site_count:
        return (
            DeepCrawlFailureType.INSUFFICIENT_PAGE_COVERAGE,
            ["site coverage below manifest minimum"],
            ["site_count"],
        )
    if len(covered_pages) < manifest.minimum_required_page_count or covered_pages != required_pages:
        return (
            DeepCrawlFailureType.INSUFFICIENT_PAGE_COVERAGE,
            [
                f"covered required pages {len(covered_pages)} did not match required "
                f"{len(required_pages)}"
            ],
            ["covered_page_count"],
        )
    if not decisions:
        return (
            DeepCrawlFailureType.MISSING_FRONTIER_DECISION,
            ["deep crawl recorded no frontier decisions"],
            ["frontier_decision_refs"],
        )
    if len(stop_reasons) < len(manifest.site_specs):
        return (
            DeepCrawlFailureType.STOP_REASON_MISSING,
            ["deep crawl missing stop reasons"],
            ["stop_reason_refs"],
        )
    if any(not decision.replay_bundle_ref for decision in decisions):
        return (
            DeepCrawlFailureType.MISSING_REPLAY_REFS,
            ["frontier decision missing replay refs"],
            ["replay_bundle_refs"],
        )
    return None, [], []


def _direct_failure_report(
    manifest: DeepCrawlQualityManifest,
    failure: DeepCrawlFailureType,
    missing: str,
) -> DeepCrawlQualityReport:
    return DeepCrawlQualityReport(
        id=f"deep-crawl-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        site_count=len(manifest.site_specs),
        minimum_site_count=manifest.minimum_site_count,
        minimum_required_page_count=manifest.minimum_required_page_count,
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"deep crawl blocked by scenario: {failure.value}"],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _expand_site_spec(site: DeepCrawlSiteSpec) -> DeepCrawlSiteSpec:
    if site.page_specs:
        return site
    origin = site.allowed_origin.rstrip("/")
    page_count = site.generated_page_count
    detail_count = max(5, page_count - 5)
    detail_urls = [f"{origin}/{site.id}/detail-{index}" for index in range(1, detail_count + 1)]
    sitemap_url = f"{origin}/{site.id}/sitemap.xml"
    feed_url = f"{origin}/{site.id}/feed.xml"
    listing_1_url = f"{origin}/{site.id}/listing-1"
    listing_2_url = f"{origin}/{site.id}/listing-2"
    listing_3_url = f"{origin}/{site.id}/listing-3"
    duplicate_url = f"{origin}/{site.id}/detail-1?ref=duplicate"
    robots_denied_url = f"{origin}/{site.id}/blocked"
    off_origin_url = f"https://offsite.invalid/{site.id}/outside"
    private_url = "http://127.0.0.1/admin"

    pages: list[DeepCrawlPageSpec] = [
        _generated_page(
            site,
            "sitemap",
            sitemap_url,
            DeepCrawlPageType.SITEMAP,
            0,
            [feed_url, listing_1_url],
        ),
        _generated_page(
            site,
            "feed",
            feed_url,
            DeepCrawlPageType.FEED,
            1,
            [detail_urls[-1]],
        ),
        _generated_page(
            site,
            "listing-1",
            listing_1_url,
            DeepCrawlPageType.LISTING,
            1,
            [listing_2_url, detail_urls[0], detail_urls[1]],
        ),
        _generated_page(
            site,
            "listing-2",
            listing_2_url,
            DeepCrawlPageType.PAGINATION,
            2,
            [listing_3_url, detail_urls[2], detail_urls[3]],
            ai_prioritized=True,
        ),
        _generated_page(
            site,
            "listing-3",
            listing_3_url,
            DeepCrawlPageType.PAGINATION,
            3,
            detail_urls[4:-1] + [duplicate_url, robots_denied_url, off_origin_url, private_url],
        ),
    ]
    for index, detail_url in enumerate(detail_urls, start=1):
        depth = 2 if index <= 2 or index == detail_count else 4
        pages.append(
            _generated_page(
                site,
                f"detail-{index}",
                detail_url,
                DeepCrawlPageType.DETAIL,
                depth,
                [],
            )
        )
    pages.append(
        _generated_page(
            site,
            "detail-1-duplicate",
            duplicate_url,
            DeepCrawlPageType.CANONICAL,
            4,
            [],
            canonical_url=detail_urls[0],
            required=False,
        )
    )
    pages.append(
        _generated_page(
            site,
            "blocked",
            robots_denied_url,
            DeepCrawlPageType.OTHER,
            4,
            [],
            required=False,
            robots_allowed=False,
        )
    )
    return site.model_copy(
        update={
            "seed_urls": [sitemap_url],
            "page_specs": pages,
            "expected_required_page_count": page_count,
            "expected_page_type_refs": [
                DeepCrawlPageType.SITEMAP,
                DeepCrawlPageType.FEED,
                DeepCrawlPageType.LISTING,
                DeepCrawlPageType.PAGINATION,
                DeepCrawlPageType.DETAIL,
                DeepCrawlPageType.CANONICAL,
            ],
            "max_pages": max(site.max_pages, page_count + 2),
        }
    )


def _generated_page(
    site: DeepCrawlSiteSpec,
    slug: str,
    url: str,
    page_type: DeepCrawlPageType,
    depth: int,
    link_urls: list[str],
    *,
    canonical_url: str | None = None,
    required: bool = True,
    robots_allowed: bool = True,
    ai_prioritized: bool = False,
) -> DeepCrawlPageSpec:
    page_id = f"{site.id}:{slug}"
    trace_prefix = f"{site.id}:{slug}"
    return DeepCrawlPageSpec(
        id=page_id,
        url=url,
        allowed_origin=site.allowed_origin,
        canonical_url=canonical_url or url,
        page_type=page_type,
        depth=depth,
        link_urls=link_urls,
        required_for_coverage=required,
        robots_allowed=robots_allowed,
        ai_prioritized=ai_prioritized,
        artifact_ref=f"artifact:{page_id}:html",
        content_hash_ref=f"content-hash:{stable_hash({'site': site.id, 'slug': slug})[:16]}",
        source_anchor_refs=[f"source-anchor:{page_id}:body"],
        model_call_refs=[f"model-call:{trace_prefix}:frontier"] if ai_prioritized else [],
        agent_action_refs=[f"agent-action:{trace_prefix}:prioritize"] if ai_prioritized else [],
        tool_call_refs=[f"tool-call:{trace_prefix}:score-links"] if ai_prioritized else [],
        context_bundle_refs=[f"context-bundle:{trace_prefix}:site"] if ai_prioritized else [],
        graph_frontier_refs=[f"graph-frontier:{trace_prefix}"],
        memory_refs=[f"memory:{trace_prefix}:prior-crawl"] if ai_prioritized else [],
    )


def _policy_refs(site: DeepCrawlSiteSpec, reason: str, target_url: str) -> list[Ref]:
    return sorted(
        {
            site.rate_budget_ref,
            site.robots_policy_ref,
            site.private_network_policy_ref,
            f"policy:deep-crawl:{site.id}:{reason}:{stable_hash(target_url)[:12]}",
        }
    )


def _record_report_event(
    manifest_id: str,
    report: DeepCrawlQualityReport,
    store: ProductionPersistenceStore,
) -> DeepCrawlQualityReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:deep-crawl-report",
        command_type="record_deep_crawl_report",
        target_aggregate_type="DeepCrawlQualityReport",
        target_aggregate_id=report.id,
        event_type="deep_crawl_reported",
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
        actor_ref="actor:deep-crawl-benchmark",
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


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_private_network_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return (
        host == "localhost"
        or host.startswith("127.")
        or host.startswith("10.")
        or host.startswith("192.168.")
        or host.startswith("169.254.")
        or any(host.startswith(f"172.{index}.") for index in range(16, 32))
    )


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
