"""``DeterministicCrawlPlannerV2`` — s5 feedback-aware fixture adapter.

See ``docs/plans/general-purpose-crawler-agentification/
s5-planner-observation-feedback.md``. Pure deterministic function
of ``(request, feedback)``. When ``feedback`` is set, the adapter
emits typed ``frontier_priority_hints`` for redirect neighbours,
canonical targets, and structural hub pages. When ``feedback`` is
``None``, behavior matches s1's ``DeterministicCrawlPlanner``.
"""

from __future__ import annotations

from urllib.parse import urlparse

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    FrontierPriorityHint,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType, FrontierMatchKind
from veracrawl.contracts.planner_observation_feedback import PlannerObservationFeedback
from veracrawl.ports.crawl_planner import CrawlPlannerPort

ADAPTER_REF: Ref = "adapter:deterministic-crawl-planner-v2:v1"
_HTTP_PRIOR_RATIONALE: Ref = "rationale:deterministic-crawl-planner-v2:http-only"
_REDIRECT_DELTA = 0.6
_CANONICAL_DELTA = 0.4
_HUB_DELTA = 0.2
_HUB_THRESHOLD = 5


def _seed_priority(index: int) -> float:
    return 1.0 / (1 + index)


def _host(url: str) -> str:
    return urlparse(url).hostname or ""


def _short_hash(url: str) -> str:
    return stable_hash(url)[:8]


class DeterministicCrawlPlannerV2(CrawlPlannerPort):
    """Feedback-aware deterministic planner adapter."""

    def __init__(self, *, feedback: PlannerObservationFeedback | None = None) -> None:
        self._feedback = feedback

    def plan(self, request: PlanRequest) -> PlanDecision:
        fb = self._feedback
        if fb is not None:
            if fb.run_ref != request.run_ref:
                raise ValueError(
                    "DeterministicCrawlPlannerV2: feedback.run_ref must match request.run_ref",
                )
            if fb.id not in request.observed_state_refs:
                raise ValueError(
                    "DeterministicCrawlPlannerV2: feedback.id must be threaded "
                    "through request.observed_state_refs",
                )

        planned_seeds = [
            PlannedSeed(
                canonical_url=url,
                priority_score=_seed_priority(i),
                adapter_hint=AdapterType.HTTP,
                rationale_ref=f"rationale:{ADAPTER_REF}:seed-{i}",
            )
            for i, url in enumerate(request.seed_urls)
        ]

        adapter_priors = [
            AdapterPrior(
                adapter_type=AdapterType.HTTP,
                weight=1.0,
                rationale_ref=_HTTP_PRIOR_RATIONALE,
            ),
        ]

        frontier_priority_hints: list[FrontierPriorityHint] = []
        if fb is not None:
            for url in fb.redirect_neighbours:
                host = _host(url)
                frontier_priority_hints.append(
                    FrontierPriorityHint(
                        match_kind=FrontierMatchKind.HOST_GLOB,
                        match_value=host,
                        priority_delta=_REDIRECT_DELTA,
                        rationale_ref=f"rationale:{ADAPTER_REF}:redirect-{host}",
                    ),
                )
            for url in fb.canonical_targets:
                frontier_priority_hints.append(
                    FrontierPriorityHint(
                        match_kind=FrontierMatchKind.URL_PREFIX,
                        match_value=url,
                        priority_delta=_CANONICAL_DELTA,
                        rationale_ref=f"rationale:{ADAPTER_REF}:canonical-{_short_hash(url)}",
                    ),
                )
            for url in sorted(fb.page_neighbour_count_by_url):
                count = fb.page_neighbour_count_by_url[url]
                if count < _HUB_THRESHOLD:
                    continue
                frontier_priority_hints.append(
                    FrontierPriorityHint(
                        match_kind=FrontierMatchKind.URL_PREFIX,
                        match_value=url,
                        priority_delta=_HUB_DELTA,
                        rationale_ref=f"rationale:{ADAPTER_REF}:hub-{_short_hash(url)}",
                    ),
                )

        replay_refs: list[Ref] = [
            request.id,
            ADAPTER_REF,
            request.replay_config_ref,
            request.objective_ref,
        ]
        if fb is not None:
            replay_refs.append(fb.id)

        return PlanDecision(
            id=f"plan-decision:{request.id}",
            request_ref=request.id,
            planner_adapter_ref=ADAPTER_REF,
            planned_seeds=planned_seeds,
            adapter_priors=adapter_priors,
            frontier_priority_hints=frontier_priority_hints,
            replay_refs=replay_refs,
            policy_decision_refs=list(request.policy_decision_refs),
        )
