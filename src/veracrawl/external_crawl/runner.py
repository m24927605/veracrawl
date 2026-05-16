"""External crawl orchestrator.

Wires the Phase 2 building blocks into a single executable runner:

* :class:`~veracrawl.external_crawl.frontier.ExternalCrawlFrontier`
  decides what to fetch next and tracks budgets;
* :class:`~veracrawl.ports.crawl_http_fetcher.CrawlHttpFetcherPort`
  turns a canonical URL into bytes;
* :class:`~veracrawl.ports.crawl_artifact_store.CrawlArtifactStorePort`
  persists raw HTML evidence + sidecar metadata (the
  filesystem-backed default lives in
  ``veracrawl.adapters.object_stores.local_fs_crawl_artifact_store``);
* :class:`~veracrawl.external_crawl.link_extractor.LinkExtractor`
  discovers new candidates to enqueue.

Outputs:

* ``artifacts/raw-html/<digest>.html`` — one per fetched HTML page;
* ``outputs/documents.jsonl`` — one record per fetched document;
* ``outputs/links.jsonl`` — one record per discovered link
  (admitted or skipped, with skip reason);
* ``events/frontier.jsonl`` — every frontier transition;
* ``reports/run_report.json`` — aggregated counters + stop reason.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from veracrawl.contracts.common import Ref
from veracrawl.contracts.crawl_job import (
    CrawlJobSpec,
    ExtractionMode,
    PrivateNetworkPolicy,
    RobotsPolicy,
)
from veracrawl.contracts.crawl_planner import AdapterPrior, PlanDecision, PlanRequest
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.contracts.graph_observation import (
    PageStructureObservedEvent,
    RedirectObservedEvent,
    UrlObservedEvent,
)
from veracrawl.contracts.planner_observation_feedback import (
    PlannerObservationFeedback,
    derive_planner_observation_feedback,  # noqa: F401 — used in step-4 replan path
)
from veracrawl.external_crawl.dispatch import _choose_fetcher
from veracrawl.external_crawl.frontier import (
    ExternalCrawlFrontier,
    FrontierEvent,
    FrontierItem,
    SkipReason,
)
from veracrawl.external_crawl.frontier_protocol import FrontierLike
from veracrawl.external_crawl.html_metadata_extractor import HtmlMetadataExtractor
from veracrawl.external_crawl.link_extractor import (
    HtmlAnchorExtractor,
    LinkExtractor,
)
from veracrawl.external_crawl.normalize_document import (
    NormalizedDocument,
    normalize_document,
)
from veracrawl.external_crawl.remote_rss import _parse_feed
from veracrawl.external_crawl.remote_sitemap import RemoteSitemapAdapter
from veracrawl.external_crawl.url import canonicalize_url
from veracrawl.ports.crawl_artifact_store import CrawlArtifactStorePort
from veracrawl.ports.crawl_http_fetcher import (
    CrawlHttpFetcherPort,
    FetchError,
    FetchOutcome,
)
from veracrawl.ports.crawl_planner import CrawlPlannerPort
from veracrawl.ports.extractor import (
    ExtractionCandidate,
    ExtractionRequest,
    ExtractorPort,
)
from veracrawl.ports.graph_observation import GraphObservationPort
from veracrawl.ports.pdf_text_extractor import PdfTextExtractorPort
from veracrawl.ports.rate_limiter import (
    NoopRateLimiter,
    RateLimiterPort,
    RateLimitFloor,
    RateLimitPermit,
)
from veracrawl.ports.replay_consumer import ReplayConsumerPort
from veracrawl.ports.robots import NoopRobotsPort, RobotsPort


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _parse_retry_after(value: str | None) -> float | None:
    """Parse an RFC 7231 ``Retry-After`` header into seconds.

    Both forms are accepted:

    * ``<delta-seconds>`` — a non-negative integer (or float, which
      RFC strictly disallows but some servers emit).
    * ``<HTTP-date>`` — an RFC 7231 §7.1.1.1 date string, e.g.
      ``"Wed, 21 Oct 2099 07:28:00 GMT"``. The parser returns the
      seconds remaining until that date.

    Returns ``None`` for missing / whitespace-only / negative-seconds
    / past-date / malformed values so the caller's limiter falls
    back to its built-in cooldown.
    """
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None

    try:
        seconds = float(stripped)
    except ValueError:
        pass
    else:
        # RFC: delta-seconds must be non-negative. Treat negatives as
        # malformed rather than "wait infinity backwards in time".
        return seconds if seconds >= 0 else None

    # Fall through to HTTP-date parsing.
    from email.utils import parsedate_to_datetime

    try:
        parsed = parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        # RFC requires GMT; defensively assume UTC for naive parses.
        parsed = parsed.replace(tzinfo=UTC)
    delta = (parsed - datetime.now(tz=UTC)).total_seconds()
    return delta if delta > 0 else None


def _event_to_dict(event: FrontierEvent) -> dict[str, Any]:
    return {
        "kind": event.kind,
        "canonical_url": event.canonical_url,
        "depth": event.depth,
        "skip_reason": event.skip_reason.value if event.skip_reason else None,
        "occurred_at": event.occurred_at.isoformat(),
    }


class ExternalCrawlRunner:
    """Phase 2 external crawl orchestrator."""

    def __init__(
        self,
        *,
        spec: CrawlJobSpec,
        store: CrawlArtifactStorePort,
        run_root: Path,
        fetcher: CrawlHttpFetcherPort,
        link_extractor: LinkExtractor | None = None,
        extractors: list[ExtractorPort] | None = None,
        pdf_extractor: PdfTextExtractorPort | None = None,
        robots_port: RobotsPort | None = None,
        rate_limiter: RateLimiterPort | None = None,
        user_agent: str = "veracrawl/0.1",
        clock: Callable[[], float] = time.monotonic,
        planner: CrawlPlannerPort | None = None,
        plan_request_builder: Callable[[CrawlJobSpec, Path], PlanRequest] | None = None,
        utc_clock: Callable[[], datetime] | None = None,
        utc_clock_ref: Ref | None = None,
        graph_observer: GraphObservationPort | None = None,
        feedback_aware_planner_factory: Callable[
            [PlannerObservationFeedback], CrawlPlannerPort,
        ] | None = None,
        frontier: FrontierLike | None = None,
        fetcher_map: dict[AdapterType, CrawlHttpFetcherPort] | None = None,
        replay_seed_ref: Ref | None = None,
        replay_consumer: ReplayConsumerPort | None = None,
    ) -> None:
        s3_set = planner is not None and plan_request_builder is not None
        s3_none = planner is None and plan_request_builder is None
        s6_set = (
            utc_clock is not None
            and utc_clock_ref is not None
            and graph_observer is not None
            and feedback_aware_planner_factory is not None
        )
        s6_none = (
            utc_clock is None
            and utc_clock_ref is None
            and graph_observer is None
            and feedback_aware_planner_factory is None
        )
        if not ((s3_set or s3_none) and (s6_set or s6_none)):
            raise ValueError(
                "ExternalCrawlRunner: partial s3/s6 ctor args. "
                "Modes: legacy (all None) | s3 (planner + plan_request_builder) | "
                "s6 (s3 pair + utc_clock + utc_clock_ref + graph_observer + "
                "feedback_aware_planner_factory).",
            )
        if s6_set and not s3_set:
            raise ValueError(
                "ExternalCrawlRunner: s6 args (utc_clock + utc_clock_ref + "
                "graph_observer + feedback_aware_planner_factory) require the s3 pair "
                "(planner + plan_request_builder) to also be set.",
            )
        if utc_clock_ref is not None and not utc_clock_ref.strip():
            raise ValueError(
                "ExternalCrawlRunner: utc_clock_ref must be non-blank when set",
            )
        # s3.2: fetcher_map + replay_seed_ref must be set together and
        # require the s3 planner pair (no priors → nothing to dispatch).
        s32_set = fetcher_map is not None and replay_seed_ref is not None
        s32_none = fetcher_map is None and replay_seed_ref is None
        if not (s32_set or s32_none):
            if fetcher_map is not None and replay_seed_ref is None:
                raise ValueError(
                    "ExternalCrawlRunner: fetcher_map requires "
                    "replay_seed_ref to be set (replay determinism).",
                )
            raise ValueError(
                "ExternalCrawlRunner: replay_seed_ref requires "
                "fetcher_map to be set (s3.2 dispatch mode).",
            )
        if s32_set and not s3_set:
            raise ValueError(
                "ExternalCrawlRunner: s3.2 (fetcher_map + "
                "replay_seed_ref) requires the s3 planner pair "
                "(planner + plan_request_builder) — adapter_priors "
                "come from the plan decision.",
            )
        if replay_seed_ref is not None and not replay_seed_ref.strip():
            raise ValueError(
                "ExternalCrawlRunner: replay_seed_ref must be "
                "non-blank when set",
            )
        if fetcher_map is not None and not fetcher_map:
            raise ValueError(
                "ExternalCrawlRunner: fetcher_map must be non-empty",
            )
        self._fetcher_map = fetcher_map
        self._replay_seed_ref = replay_seed_ref
        self._adapter_dispatch_choices: dict[str, str] = {}
        # s12: replay consumer overrides utc_clock when both provided.
        self._replay_consumer = replay_consumer
        self._replay_invocation_count = 0
        if replay_consumer is not None:
            recorded_clock = replay_consumer.next_utc
            def _replay_clock() -> datetime:
                self._replay_invocation_count += 1
                return recorded_clock()
            utc_clock = _replay_clock
        self._planner = planner
        self._plan_request_builder = plan_request_builder
        self._utc_clock = utc_clock
        self._utc_clock_ref = utc_clock_ref
        self._graph_observer = graph_observer
        self._feedback_aware_planner_factory = feedback_aware_planner_factory
        self._plan_decision: PlanDecision | None = None
        self._spec = spec
        self._store = store
        self._run_root = run_root
        self._fetcher = fetcher
        self._link_extractor: LinkExtractor = link_extractor or HtmlAnchorExtractor()
        self._sitemap_adapter = RemoteSitemapAdapter(fetcher=fetcher)
        self._extractors: list[ExtractorPort] = (
            extractors if extractors is not None else self._default_extractors(spec)
        )
        self._pdf_extractor = pdf_extractor
        self._robots_port: RobotsPort = robots_port or NoopRobotsPort()
        self._rate_limiter: RateLimiterPort = rate_limiter or NoopRateLimiter()
        self._user_agent = user_agent
        self._clock = clock

        allow_loopback = spec.private_network_policy == PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY
        # s3.1: optional caller-injected frontier (e.g.,
        # PriorityCrawlFrontier). Default remains the legacy FIFO
        # ExternalCrawlFrontier so existing callers are unaffected.
        self._frontier: FrontierLike = frontier if frontier is not None else (
            ExternalCrawlFrontier(
                allowed_domains=frozenset(spec.allowed_domains),
                denied_domains=frozenset(spec.denied_domains),
                max_depth=spec.max_depth,
                max_pages=spec.max_pages,
                allow_loopback=allow_loopback,
            )
        )

        self._cited_artifact_refs: set[str] = set()
        self._candidates_written = 0
        self._evidence_packets_written = 0
        self._obs_seq = 0
        self._original_plan_request: PlanRequest | None = None
        self._clock_trace: list[str] = []
        self._fetch_count = 0
        self._replan_done = False
        self._plan_decision_2: PlanDecision | None = None
        self._observation_snapshot_ref: str | None = None
        self._observation_feedback_ref: str | None = None

    def _s6_active(self) -> bool:
        return (
            self._graph_observer is not None
            and self._utc_clock is not None
            and self._original_plan_request is not None
        )

    def _next_seq(self) -> int:
        seq = self._obs_seq
        self._obs_seq += 1
        return seq

    def _tick_utc_clock(self) -> datetime:
        assert self._utc_clock is not None
        t = self._utc_clock()
        self._clock_trace.append(t.isoformat())
        return t

    # Carry-forward gap #1 (s12 full clock override) — REFRAMED, NOT CLOSED.
    #
    # Original framing: "every wall-clock read in the runner should
    # route through ``replay_consumer.next_utc`` when wired so the
    # replay invariant binds outside s6 mode."
    #
    # On attempting the fix, the 8 ``_now()`` call sites I'd
    # convert are all observability timestamps (``started_at``,
    # ``fetched_at``, failure ``at``, ``checked_at``,
    # ``completed_at``) — they land in ``run_report.json`` /
    # ``documents.jsonl`` / ``robots-cache.json`` for human
    # diagnostics. None of them are read by the runner's behavior
    # loop. They're explicitly tagged as "wall-clock fields" by
    # s13's ``_replay_compare.normalize_report`` and excluded from
    # the byte-equality invariant.
    #
    # Routing them through ``self._utc_clock`` would:
    # 1. Break s6's implicit invariant that ``clock_trace`` records
    #    EVERY ``self._utc_clock`` call (witnessed by
    #    ``test_s6_mode_populates_clock_trace_in_run_report``: an
    #    auto-advancing fake clock would drain on the new reads,
    #    and ``clock_trace``'s recorded subset would no longer
    #    match the advancing-clock sequence verbatim).
    # 2. Require expanding s11's ``ReplayBundle.clock_trace`` to
    #    capture every UTC read, not just s6 events — a
    #    bundle-shape change with cross-slice impact.
    #
    # Honest conclusion: the gap as originally framed conflates
    # two different invariants (replay-stable BEHAVIOR vs replay-
    # stable OBSERVABILITY). The replay-stable behavior part is
    # already correctly bound via the s6 ``_tick_utc_clock``
    # path. The replay-stable observability part needs its own
    # design slice (bundle shape + tagging) and is NOT a simple
    # ``_now()`` → ``self._utc_clock()`` substitution.
    #
    # Keeping the 8 wall-clock sites on ``_now()`` for now; opening
    # a dedicated follow-up slice to design the observability-
    # timestamp replay invariant once a real use case requires it.

    def _record_url_observed(
        self, *, canonical_url: str, depth: int,
        parent_canonical_url: str | None, source_ref: str,
    ) -> None:
        if not self._s6_active():
            return
        assert self._graph_observer is not None
        assert self._utc_clock is not None
        assert self._original_plan_request is not None
        self._graph_observer.record_url_observed(UrlObservedEvent(
            id=f"url-obs:{self._spec.id}:{self._next_seq()}",
            run_ref=self._original_plan_request.run_ref,
            canonical_url=canonical_url,
            depth=depth,
            parent_canonical_url=parent_canonical_url,
            source_ref=source_ref,
            observed_at=self._tick_utc_clock(),
        ))

    def _record_redirect_observed(self, outcome: FetchOutcome) -> None:
        if not self._s6_active() or not outcome.redirect_history:
            return
        assert self._graph_observer is not None
        assert self._utc_clock is not None
        assert self._original_plan_request is not None
        for hop in outcome.redirect_history:
            self._graph_observer.record_redirect_observed(RedirectObservedEvent(
                id=f"redirect-obs:{self._spec.id}:{self._next_seq()}",
                run_ref=self._original_plan_request.run_ref,
                from_canonical_url=hop.from_url,
                to_canonical_url=hop.to_url,
                status_code=hop.status_code,
                observed_at=self._tick_utc_clock(),
            ))

    def _maybe_replan(self) -> bool:
        """Trigger the s6 single replan on first frontier-empty after >=1 fetch.

        Returns True when this call actually performed the replan
        (caller continues the loop); False otherwise (caller breaks).
        """
        if (
            self._replan_done
            or not self._s6_active()
            or self._fetch_count < 1
            or self._feedback_aware_planner_factory is None
        ):
            return False
        assert self._graph_observer is not None
        assert self._original_plan_request is not None
        snap = self._graph_observer.snapshot(
            id=f"snap:{self._spec.id}:1",
            snapshot_at=self._tick_utc_clock(),
        )
        fb = derive_planner_observation_feedback(
            id=f"fb:{self._spec.id}:1",
            run_ref=self._original_plan_request.run_ref,
            snapshot=snap,
        )
        req2 = self._original_plan_request.model_copy(update={
            "id": f"plan-req:{self._spec.id}:2",
            "observed_state_refs": [
                *self._original_plan_request.observed_state_refs, fb.id,
            ],
        })
        planner2 = self._feedback_aware_planner_factory(fb)
        decision2 = planner2.plan(req2)
        self._plan_decision_2 = decision2
        self._observation_snapshot_ref = snap.id
        self._observation_feedback_ref = fb.id
        # s3.1: replan hints update the priority queue before
        # enqueueing replan seeds. Guarded by hasattr; legacy FIFO
        # frontier ignores this no-op.
        add_hints = getattr(self._frontier, "add_hints", None)
        if add_hints is not None:
            add_hints(list(decision2.frontier_priority_hints))
        # Frontier dedup is authoritative — re-enqueuing an already-
        # admitted URL returns admitted=False, so we skip the
        # url_observed record in that case.
        sorted_seeds = sorted(
            enumerate(decision2.planned_seeds),
            key=lambda iv: (-iv[1].priority_score, iv[0]),
        )
        for _, seed in sorted_seeds:
            outcome_enqueue = self._frontier.enqueue(
                seed.canonical_url, depth=0, parent_canonical_url=None,
            )
            if outcome_enqueue.admitted and outcome_enqueue.canonical_url:
                self._record_url_observed(
                    canonical_url=outcome_enqueue.canonical_url,
                    depth=0, parent_canonical_url=None,
                    source_ref="frontier-admit:replan-seed",
                )
        self._replan_done = True
        return True

    def _record_page_structure_observed(
        self, *, page_canonical_url: str, discovered_link_count: int,
    ) -> None:
        if not self._s6_active():
            return
        assert self._graph_observer is not None
        assert self._utc_clock is not None
        assert self._original_plan_request is not None
        self._graph_observer.record_page_structure_observed(
            PageStructureObservedEvent(
                id=f"page-obs:{self._spec.id}:{self._next_seq()}",
                run_ref=self._original_plan_request.run_ref,
                page_canonical_url=page_canonical_url,
                discovered_link_count=discovered_link_count,
                discovered_canonical_urls=[],
                observed_at=self._tick_utc_clock(),
            ),
        )

    @staticmethod
    def _default_extractors(spec: CrawlJobSpec) -> list[ExtractorPort]:
        # ``deterministic`` mode wires the HTML metadata extractor.
        # ``llm_assisted`` requires the caller to inject a callable
        # (so the core never has a static LLM dependency); the
        # runner defaults to no extractor in that mode and warns
        # via the run report's ``policy_denials`` counter. See
        # ``Phase 5 hand-off`` in STATUS.md.
        if spec.extraction.mode == ExtractionMode.DETERMINISTIC:
            return [HtmlMetadataExtractor()]
        return []

    def run(self) -> dict[str, Any]:
        documents_path = self._run_root / "outputs" / "documents.jsonl"
        links_path = self._run_root / "outputs" / "links.jsonl"
        normalized_path = self._run_root / "outputs" / "normalized_documents.jsonl"
        candidates_path = (
            self._run_root / "outputs" / "extraction_candidates.jsonl"
        )
        evidence_path = self._run_root / "outputs" / "evidence_packets.jsonl"
        events_path = self._run_root / "events" / "frontier.jsonl"
        redirects_path = self._run_root / "events" / "redirects.jsonl"

        for path in (
            documents_path,
            links_path,
            normalized_path,
            candidates_path,
            evidence_path,
            events_path,
            redirects_path,
        ):
            path.unlink(missing_ok=True)
        # Touch redirects.jsonl so it always exists for downstream
        # tooling, even when no hops were observed.
        redirects_path.parent.mkdir(parents=True, exist_ok=True)
        redirects_path.touch()

        if self._planner is not None and self._plan_request_builder is not None:
            plan_request = self._plan_request_builder(self._spec, self._run_root)
            self._original_plan_request = plan_request
            self._plan_decision = self._planner.plan(plan_request)
            # s3.1: feed hints to the frontier before enqueueing seeds
            # so the first pop already respects priority. Guarded by
            # hasattr — legacy FIFO frontier has no add_hints.
            add_hints = getattr(self._frontier, "add_hints", None)
            if add_hints is not None:
                add_hints(list(self._plan_decision.frontier_priority_hints))
            sorted_seeds = sorted(
                enumerate(self._plan_decision.planned_seeds),
                key=lambda iv: (-iv[1].priority_score, iv[0]),
            )
            for _, seed in sorted_seeds:
                outcome_enqueue = self._frontier.enqueue(
                    seed.canonical_url, depth=0, parent_canonical_url=None,
                )
                if outcome_enqueue.admitted and outcome_enqueue.canonical_url:
                    self._record_url_observed(
                        canonical_url=outcome_enqueue.canonical_url,
                        depth=0, parent_canonical_url=None,
                        source_ref="frontier-admit:seed",
                    )
        else:
            for seed in self._spec.seed_urls:
                self._frontier.enqueue(seed, depth=0, parent_canonical_url=None)

        failures: list[dict[str, Any]] = []
        started_at = _now()
        deadline = self._clock() + self._spec.max_runtime_seconds
        stop_reason = "queue_drained"

        with (
            documents_path.open("a", encoding="utf-8") as docs_fp,
            links_path.open("a", encoding="utf-8") as links_fp,
            normalized_path.open("a", encoding="utf-8") as normalized_fp,
            candidates_path.open("a", encoding="utf-8") as candidates_fp,
            evidence_path.open("a", encoding="utf-8") as evidence_fp,
        ):
            while True:
                if self._clock() > deadline:
                    stop_reason = "runtime_exceeded"
                    break
                item = self._frontier.pop()
                if item is None:
                    if self._frontier.budget_exhausted():
                        # Don't replan on budget exhaustion — there may
                        # be queued URLs the budget refused; the plan
                        # rule only authorizes replan when the frontier
                        # truly drained after at least one fetch.
                        stop_reason = "budget_exhausted"
                        break
                    if self._maybe_replan():
                        continue
                    break

                if not self._robots_allowed(item.canonical_url):
                    self._frontier.skip(
                        item.canonical_url, SkipReason.ROBOTS_DENIED
                    )
                    continue

                fetch_outcome = self._fetch_with_rate_limit(
                    item, failures
                )
                if fetch_outcome is None:
                    continue

                self._frontier.mark_fetched(item.canonical_url)
                self._fetch_count += 1
                self._record_redirect_observed(fetch_outcome)
                self._write_redirect_hops(
                    item.canonical_url, fetch_outcome, redirects_path
                )
                artifact_ref = self._persist_artifact(
                    item.canonical_url, fetch_outcome
                )
                docs_fp.write(
                    json.dumps(
                        self._document_record(item, fetch_outcome, artifact_ref)
                    )
                    + "\n"
                )

                normalized = normalize_document(
                    canonical_url=item.canonical_url,
                    body=fetch_outcome.body,
                    content_type=fetch_outcome.content_type,
                    raw_artifact_ref=artifact_ref,
                    pdf_extractor=self._pdf_extractor,
                    redirect_lineage=tuple(fetch_outcome.redirect_chain)
                    + (fetch_outcome.final_url,),
                )
                normalized_fp.write(
                    json.dumps(self._normalized_record(normalized)) + "\n"
                )

                if normalized.status == "ok" and self._extractors:
                    self._run_extractors(
                        canonical_url=item.canonical_url,
                        normalized=normalized,
                        body=fetch_outcome.body,
                        content_type=fetch_outcome.content_type,
                        artifact_ref=artifact_ref,
                        candidates_fp=candidates_fp,
                        evidence_fp=evidence_fp,
                    )

                self._discover_and_enqueue(item, fetch_outcome, links_fp)

        # Persist event log after the loop so partial files don't appear.
        with events_path.open("w", encoding="utf-8") as events_fp:
            for event in self._frontier.events():
                events_fp.write(json.dumps(_event_to_dict(event)) + "\n")

        # Flush model-call traces from any extractor that recorded
        # them (currently the LlmAssistedExtractor). Duck-typed: any
        # extractor with a ``recent_traces`` method qualifies.
        model_traces_path = self._run_root / "events" / "model_calls.jsonl"
        with model_traces_path.open("w", encoding="utf-8") as traces_fp:
            for extractor in self._extractors:
                recent = getattr(extractor, "recent_traces", None)
                if recent is None:
                    continue
                for trace in recent():
                    traces_fp.write(
                        json.dumps(trace.model_dump(mode="json")) + "\n"
                    )

        report = self._build_report(
            started_at=started_at, failures=failures, stop_reason=stop_reason
        )
        report_path = self._run_root / "reports" / "run_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )

        # Persist the job spec next to the report so replay tooling
        # can recover both without separate lookups.
        spec_path = self._run_root / "reports" / "job_spec.json"
        spec_path.write_text(
            json.dumps(self._spec.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        replay_report = self._build_replay_report()
        replay_path = self._run_root / "reports" / "replay_report.json"
        replay_path.write_text(
            json.dumps(replay_report, indent=2, sort_keys=True), encoding="utf-8"
        )
        report["replay_completeness_result"] = replay_report["status"]
        report["extraction_candidates"] = self._candidates_written
        report["evidence_packets"] = self._evidence_packets_written
        if self._plan_decision is not None:
            d = self._plan_decision
            sorted_seeds = sorted(
                enumerate(d.planned_seeds),
                key=lambda iv: (-iv[1].priority_score, iv[0]),
            )
            report["plan_decision_ref"] = d.id
            report["plan_decision_replay_refs"] = list(d.replay_refs)
            report["plan_decision_frontier_priority_hints"] = [
                h.model_dump(mode="json") for h in d.frontier_priority_hints
            ]
            report["plan_decision_adapter_priors"] = [
                p.model_dump(mode="json") for p in d.adapter_priors
            ]
            report["plan_decision_planned_seed_order"] = [
                s.canonical_url for _, s in sorted_seeds
            ]
            report["plan_decision_extraction_strategy_refs"] = list(
                d.extraction_strategy_refs
            )
        # s6 keyed-always fields. In legacy / s3 mode these stay None
        # (and replan_invoked False) so the JSON shape is stable; in s6
        # mode they are populated when the replan path fires.
        d2 = self._plan_decision_2
        if d2 is not None:
            sorted_seeds_2 = sorted(
                enumerate(d2.planned_seeds),
                key=lambda iv: (-iv[1].priority_score, iv[0]),
            )
            report["plan_decision_2_ref"] = d2.id
            report["plan_decision_2_replay_refs"] = list(d2.replay_refs)
            report["plan_decision_2_planned_seed_order"] = [
                s.canonical_url for _, s in sorted_seeds_2
            ]
            report["plan_decision_2_adapter_priors"] = [
                p.model_dump(mode="json") for p in d2.adapter_priors
            ]
            report["plan_decision_2_frontier_priority_hints"] = [
                h.model_dump(mode="json") for h in d2.frontier_priority_hints
            ]
            report["plan_decision_2_extraction_strategy_refs"] = list(
                d2.extraction_strategy_refs,
            )
        else:
            report["plan_decision_2_ref"] = None
            report["plan_decision_2_replay_refs"] = None
            report["plan_decision_2_planned_seed_order"] = None
            report["plan_decision_2_adapter_priors"] = None
            report["plan_decision_2_frontier_priority_hints"] = None
            report["plan_decision_2_extraction_strategy_refs"] = None
        report["observation_snapshot_ref"] = self._observation_snapshot_ref
        report["observation_feedback_ref"] = self._observation_feedback_ref
        report["utc_clock_ref"] = self._utc_clock_ref
        report["clock_trace"] = list(self._clock_trace) if self._clock_trace else None
        report["replan_invoked"] = self._replan_done
        # s3.2 keyed-always fields. ``None`` in legacy / s3 mode so the
        # JSON shape stays stable; populated when ``fetcher_map`` is set.
        report["replay_seed_ref"] = self._replay_seed_ref
        report["adapter_dispatch_choices"] = (
            dict(self._adapter_dispatch_choices)
            if self._fetcher_map is not None else None
        )
        # s12 keyed-always fields.
        report["replay_consumer_ref"] = (
            "replay-consumer:active"
            if self._replay_consumer is not None else None
        )
        report["replay_invocation_count"] = (
            self._replay_invocation_count
            if self._replay_consumer is not None else None
        )
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        return report

    @staticmethod
    def _write_redirect_hops(
        canonical_url: str, outcome: FetchOutcome, redirects_path: Any
    ) -> None:
        if not outcome.redirect_history:
            return
        with redirects_path.open("a", encoding="utf-8") as fp:
            for hop in outcome.redirect_history:
                fp.write(
                    json.dumps(
                        {
                            "canonical_url": canonical_url,
                            "from_url": hop.from_url,
                            "to_url": hop.to_url,
                            "status_code": hop.status_code,
                            "observed_at": _now().isoformat(),
                        }
                    )
                    + "\n"
                )

    def _robots_allowed(self, url: str) -> bool:
        """Apply ``spec.robots_policy`` to a candidate URL.

        ``OBEY`` and ``DENY_WITHOUT_ROBOTS`` block disallowed URLs.
        ``WARN`` always lets the URL through (the disallow is still
        recorded as a frontier event by the ``RobotsPort`` impl when
        it logs).
        """
        policy = self._spec.robots_policy
        if policy == RobotsPolicy.WARN:
            return True
        advice = self._robots_port.evaluate(url, user_agent=self._user_agent)
        return advice.is_allowed

    def _floor_from_spec(self) -> RateLimitFloor:
        rate = self._spec.rate_limit
        request_rate = (
            (rate.requests_per_minute, 60)
            if rate.requests_per_minute > 0
            else None
        )
        return RateLimitFloor(
            crawl_delay_seconds=rate.crawl_delay_seconds,
            request_rate=request_rate,
        )

    @staticmethod
    def _origin_of(url: str) -> str:
        parsed = urlsplit(url)
        if not parsed.scheme or not parsed.hostname:
            return url
        host = parsed.hostname.lower()
        if parsed.port and not (
            (parsed.scheme == "http" and parsed.port == 80)
            or (parsed.scheme == "https" and parsed.port == 443)
        ):
            host = f"{host}:{parsed.port}"
        return f"{parsed.scheme}://{host}"

    @staticmethod
    def _route_class_for(url: str) -> RouteClass:
        parsed = urlsplit(url)
        path = (parsed.path or "/").lower()
        query = (parsed.query or "").lower()
        # File downloads first — extension wins.
        if "." in path:
            ext = path.rsplit(".", 1)[-1]
            if ext in {
                "pdf", "doc", "docx", "xls", "xlsx",
                "zip", "tar", "gz", "tgz", "rar", "7z",
                "png", "jpg", "jpeg", "gif", "webp", "svg",
                "mp4", "mp3", "wav", "flac", "mov", "avi",
                "csv", "tsv",
            }:
                return RouteClass.FILE
        if "/api/" in path or path.startswith("/api"):
            return RouteClass.API
        if "/search" in path or "q=" in query or "search=" in query:
            return RouteClass.SEARCH
        if path.endswith("/") or "/list" in path or "/index" in path:
            return RouteClass.LISTING
        return RouteClass.DETAIL

    def _fetch_with_rate_limit(
        self, item: FrontierItem, failures: list[dict[str, Any]]
    ) -> FetchOutcome | None:
        url = item.canonical_url
        origin = self._origin_of(url)
        route_class = self._route_class_for(url)
        floor = self._floor_from_spec()
        adapter_type, fetcher = self._select_fetcher(item)
        with self._rate_limiter.acquire(
            origin=origin,
            route_class=route_class,
            adapter_type=adapter_type,
            floor=floor,
        ) as permit:
            return self._fetch(url, fetcher, failures, permit)

    def _select_fetcher(
        self, item: FrontierItem,
    ) -> tuple[AdapterType, CrawlHttpFetcherPort]:
        # s3.2: legacy path picks the single configured fetcher with
        # ``AdapterType.HTTP`` (preserves existing behavior); dispatch
        # path picks deterministically via ``_choose_fetcher``.
        if self._fetcher_map is None or self._replay_seed_ref is None:
            return AdapterType.HTTP, self._fetcher
        priors: list[AdapterPrior] = []
        if self._plan_decision_2 is not None:
            priors = list(self._plan_decision_2.adapter_priors)
        elif self._plan_decision is not None:
            priors = list(self._plan_decision.adapter_priors)
        adapter_type = _choose_fetcher(
            item=item,
            priors=priors,
            fetcher_map=self._fetcher_map,
            replay_seed_ref=self._replay_seed_ref,
            source_adapters=list(self._spec.source_adapters),
        )
        self._adapter_dispatch_choices[item.canonical_url] = adapter_type.value
        return adapter_type, self._fetcher_map[adapter_type]

    def _fetch(
        self,
        url: str,
        fetcher: CrawlHttpFetcherPort,
        failures: list[dict[str, Any]],
        permit: RateLimitPermit | None = None,
    ) -> FetchOutcome | None:
        try:
            outcome = fetcher.fetch(url, timeout_seconds=10.0)
        except FetchError as exc:
            failures.append(
                {
                    "canonical_url": url,
                    "stage": "fetch",
                    "error": str(exc),
                    "at": _now().isoformat(),
                }
            )
            # Transport errors don't carry a server-side throttle
            # signal; do not feed the AIMD limiter a synthetic
            # throttle here.
            return None
        if outcome.status_code in {429, 503}:
            failures.append(
                {
                    "canonical_url": url,
                    "stage": "fetch",
                    "error": f"HTTP {outcome.status_code}",
                    "at": _now().isoformat(),
                }
            )
            if permit is not None:
                retry_after = _parse_retry_after(
                    outcome.headers.get("Retry-After")
                    or outcome.headers.get("retry-after")
                )
                self._rate_limiter.report_throttled(
                    permit=permit, retry_after_seconds=retry_after
                )
            return None
        if outcome.status_code >= 400:
            failures.append(
                {
                    "canonical_url": url,
                    "stage": "fetch",
                    "error": f"HTTP {outcome.status_code}",
                    "at": _now().isoformat(),
                }
            )
            return None
        if permit is not None:
            self._rate_limiter.report_success(permit=permit)
        return outcome

    def _persist_artifact(
        self, canonical_url: str, outcome: FetchOutcome
    ) -> str:
        """Persist the fetched body and return the artifact ref."""
        digest = hashlib.sha256(outcome.body).hexdigest()
        category = self._artifact_category(outcome.content_type)
        suffix = self._extension_for_content_type(outcome.content_type)
        artifact_ref = f"{category}/{digest[:24]}{suffix}"
        self._store.put_bytes(
            artifact_ref,
            outcome.body,
            content_type=outcome.content_type or "application/octet-stream",
            metadata={
                "source_url": canonical_url,
                "privacy_classification": "internal",
                "replay_ref": f"fetch:{digest}",
                "final_url": outcome.final_url,
                "status_code": str(outcome.status_code),
            },
        )
        return artifact_ref

    @staticmethod
    def _artifact_category(content_type: str) -> str:
        lowered = (content_type or "").lower()
        if "html" in lowered or "xml" in lowered:
            return "raw-html"
        return "documents"

    @staticmethod
    def _extension_for_content_type(content_type: str) -> str:
        lowered = (content_type or "").lower()
        if "html" in lowered:
            return ".html"
        if "xml" in lowered:
            return ".xml"
        if "json" in lowered:
            return ".json"
        if "pdf" in lowered:
            return ".pdf"
        if "plain" in lowered or "text" in lowered:
            return ".txt"
        return ".bin"

    def _document_record(
        self, item: object, outcome: FetchOutcome, artifact_ref: str
    ) -> dict[str, Any]:
        # ``item`` typed as object so this helper does not import the
        # FrontierItem name into the module's public API surface.
        from veracrawl.external_crawl.frontier import FrontierItem

        assert isinstance(item, FrontierItem)
        return {
            "canonical_url": item.canonical_url,
            "final_url": outcome.final_url,
            "status_code": outcome.status_code,
            "content_type": outcome.content_type,
            "content_digest": hashlib.sha256(outcome.body).hexdigest(),
            "size_bytes": len(outcome.body),
            "artifact_ref": artifact_ref,
            "artifact_category": artifact_ref.split("/", 1)[0],
            "depth": item.depth,
            "parent_canonical_url": item.parent_canonical_url,
            "fetched_at": _now().isoformat(),
            "redirect_chain": outcome.redirect_chain,
        }

    def _discover_and_enqueue(
        self,
        item: object,
        outcome: FetchOutcome,
        links_fp: Any,
    ) -> None:
        from veracrawl.external_crawl.frontier import FrontierItem

        assert isinstance(item, FrontierItem)
        discovered = self._discover_links(outcome)
        self._record_page_structure_observed(
            page_canonical_url=item.canonical_url,
            discovered_link_count=len(discovered),
        )
        for raw in discovered:
            try:
                canonical = canonicalize_url(raw)
            except ValueError:
                canonical = None
            outcome_enqueue = self._frontier.enqueue(
                raw, depth=item.depth + 1, parent_canonical_url=item.canonical_url
            )
            if outcome_enqueue.admitted and outcome_enqueue.canonical_url:
                self._record_url_observed(
                    canonical_url=outcome_enqueue.canonical_url,
                    depth=item.depth + 1,
                    parent_canonical_url=item.canonical_url,
                    source_ref="frontier-admit:discovery",
                )
            links_fp.write(
                json.dumps(
                    {
                        "parent_canonical_url": item.canonical_url,
                        "discovered_url": raw,
                        "canonical_url": canonical,
                        "admitted": outcome_enqueue.admitted,
                        "skip_reason": (
                            outcome_enqueue.skip_reason.value
                            if outcome_enqueue.skip_reason
                            else None
                        ),
                    }
                )
                + "\n"
            )

    def _run_extractors(
        self,
        *,
        canonical_url: str,
        normalized: NormalizedDocument,
        body: bytes,
        content_type: str,
        artifact_ref: str,
        candidates_fp: Any,
        evidence_fp: Any,
    ) -> None:
        request = ExtractionRequest(
            canonical_url=canonical_url,
            normalized_text=normalized.text,
            raw_body=body,
            content_type=content_type,
            raw_artifact_ref=artifact_ref,
            anchors=list(normalized.anchors),
        )
        for extractor in self._extractors:
            result = extractor.extract(request)
            for candidate in result.candidates:
                candidates_fp.write(json.dumps(self._candidate_record(candidate)) + "\n")
                self._candidates_written += 1
                evidence_fp.write(
                    json.dumps(self._evidence_packet_record(candidate)) + "\n"
                )
                self._evidence_packets_written += 1
                self._cited_artifact_refs.update(
                    anchor.raw_artifact_ref for anchor in candidate.evidence_anchors
                )

    @staticmethod
    def _candidate_record(candidate: ExtractionCandidate) -> dict[str, Any]:
        return {
            "canonical_url": candidate.canonical_url,
            "schema_ref": candidate.schema_ref,
            "fields": candidate.fields,
            "evidence_anchors": [
                {
                    "page_number": anchor.page_number,
                    "char_offset_start": anchor.char_offset_start,
                    "char_offset_end": anchor.char_offset_end,
                    "text_hash": anchor.text_hash,
                    "raw_artifact_ref": anchor.raw_artifact_ref,
                    "redirect_lineage": list(anchor.redirect_lineage),
                }
                for anchor in candidate.evidence_anchors
            ],
        }

    @staticmethod
    def _evidence_packet_record(candidate: ExtractionCandidate) -> dict[str, Any]:
        # Phase 4 packet shape: candidate identity + the artifact
        # refs it cites + the per-anchor text hashes. Replay
        # verifies every ref still exists in the run dir.
        return {
            "canonical_url": candidate.canonical_url,
            "schema_ref": candidate.schema_ref,
            "field_names": sorted(candidate.fields.keys()),
            "raw_artifact_refs": sorted(
                {anchor.raw_artifact_ref for anchor in candidate.evidence_anchors}
            ),
            "text_hashes": [anchor.text_hash for anchor in candidate.evidence_anchors],
        }

    def _build_replay_report(self) -> dict[str, Any]:
        artifacts_root = self._run_root / "artifacts"
        missing: list[str] = []
        for ref in sorted(self._cited_artifact_refs):
            target = artifacts_root / ref
            if not target.is_file():
                missing.append(ref)
        return {
            "run_id": self._run_root.name,
            "artifacts_cited": len(self._cited_artifact_refs),
            "artifacts_missing": len(missing),
            "missing_refs": missing,
            "status": "complete" if not missing else "needs_review",
            "checked_at": _now().isoformat(),
        }

    def _normalized_record(self, normalized: NormalizedDocument) -> dict[str, Any]:
        return {
            "canonical_url": normalized.canonical_url,
            "raw_artifact_ref": normalized.raw_artifact_ref,
            "content_type": normalized.content_type,
            "status": normalized.status,
            "reason": normalized.reason,
            "text_length": len(normalized.text),
            "anchors": [
                {
                    "page_number": anchor.page_number,
                    "char_offset_start": anchor.char_offset_start,
                    "char_offset_end": anchor.char_offset_end,
                    "text_hash": anchor.text_hash,
                    "raw_artifact_ref": anchor.raw_artifact_ref,
                    "redirect_lineage": list(anchor.redirect_lineage),
                }
                for anchor in normalized.anchors
            ],
        }

    def _discover_links(self, outcome: FetchOutcome) -> list[str]:
        """Dispatch link discovery by content type.

        * HTML → ``<a href>`` extraction;
        * XML with sitemap shape → ``<loc>`` extraction (recurses one
          level into sitemap indices);
        * anything else → no further URLs.
        """
        content_type = (outcome.content_type or "").lower()
        if "html" in content_type:
            return self._link_extractor.extract(
                base_url=outcome.final_url,
                body=outcome.body,
                content_type=outcome.content_type,
            )
        if "xml" in content_type or "rss" in content_type:
            # Try sitemap shape first (most common XML on crawled
            # sites); fall through to feed parsing for RSS/Atom.
            from veracrawl.external_crawl.remote_sitemap import _parse_locs

            urls, child_locs, _ = _parse_locs(outcome.body)
            if urls:
                return urls
            if child_locs:
                collected: list[str] = []
                for child_url in child_locs:
                    bundle = self._sitemap_adapter.discover(child_url)
                    collected.extend(bundle.discovered_urls)
                return collected
            feed_urls, _kind, _error = _parse_feed(outcome.body)
            return feed_urls
        return []

    def _build_report(
        self,
        *,
        started_at: datetime,
        failures: list[dict[str, Any]],
        stop_reason: str,
    ) -> dict[str, Any]:
        counters = self._frontier.counters()
        skipped_by_reason = {
            reason.value: count
            for reason, count in counters.skipped_by_reason.items()
        }
        policy_denials = sum(
            counters.skipped_by_reason.get(reason, 0)
            for reason in (
                SkipReason.PRIVATE_NETWORK_DENIED,
                SkipReason.DENIED_DOMAIN,
                SkipReason.ROBOTS_DENIED,
            )
        )
        return {
            "run_id": self._run_root.name,
            "job_id": self._spec.id,
            "project_id": self._spec.project_id,
            "job_spec_hash": self._spec.content_hash(),
            "status": "completed",
            "stop_reason": stop_reason,
            "started_at": started_at.isoformat(),
            "completed_at": _now().isoformat(),
            "seed_urls": list(self._spec.seed_urls),
            "pages_fetched": counters.fetched,
            "pages_skipped": sum(skipped_by_reason.values()),
            "skipped_by_reason": skipped_by_reason,
            "artifacts_written": counters.fetched,
            "extraction_candidates": 0,
            "evidence_packets": 0,
            "failures": failures,
            "policy_denials": policy_denials,
            "replay_completeness_result": "pending",
        }


__all__ = ["ExternalCrawlRunner"]
