"""``CrawlPlannerPort`` — s1 of general-purpose-crawler-agentification.

See ``docs/plans/general-purpose-crawler-agentification/
s1-crawl-planner-port-contract.md``. The port is the hexagonal
boundary between callers that hold a ``PlanRequest`` and adapters
that produce a ``PlanDecision``. s1 ships one fixture adapter
(``adapters/planning/deterministic_crawl_planner.py``) implementing
this protocol; future slices add LLM-backed and graph-aware adapters
without changing this surface.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.crawl_planner import PlanDecision, PlanRequest


@runtime_checkable
class CrawlPlannerPort(Protocol):
    """Plan a crawl given an objective and caller-supplied seed URLs."""

    def plan(self, request: PlanRequest) -> PlanDecision:
        """Triage ``request.seed_urls`` into a typed ``PlanDecision``.

        Implementations MUST:

        * preserve the ``request.id`` provenance — the returned
          ``PlanDecision.request_ref`` equals ``request.id`` and the
          same id appears in ``replay_refs``;
        * write their own adapter identifier into
          ``PlanDecision.planner_adapter_ref`` and into
          ``replay_refs`` so a replay verifier can re-instantiate
          the adapter version that produced the decision;
        * forward (not synthesize) ``request.policy_decision_refs``
          into ``PlanDecision.policy_decision_refs``;
        * record any non-determinism (model output, RNG seed, clock)
          via additional entries appended to ``replay_refs``.

        Implementations MUST NOT branch on the contents or
        cardinality of ``request.observed_state_refs`` in s1 — that
        slot belongs to a later slice's typed observed-state
        contract.
        """

        ...


__all__ = ["CrawlPlannerPort"]
