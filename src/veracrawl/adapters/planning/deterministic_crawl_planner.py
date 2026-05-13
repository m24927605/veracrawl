"""``DeterministicCrawlPlanner`` — s1 fixture adapter for ``CrawlPlannerPort``.

See ``docs/plans/general-purpose-crawler-agentification/
s1-crawl-planner-port-contract.md``. Pure deterministic function of
the ``PlanRequest`` payload — no clock, no RNG, no model output.
The s5 graph-feedback slice will replace this with a graph-aware
adapter; the LLM adapter lands in s2.
"""

from __future__ import annotations

from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.ports.crawl_planner import CrawlPlannerPort


class DeterministicCrawlPlanner(CrawlPlannerPort):
    """Triage every ``request.seed_urls`` entry into a ``PlannedSeed``."""

    ADAPTER_REF = "adapter:deterministic-crawl-planner:v1"
    HTTP_PRIOR_RATIONALE_REF = "rationale:deterministic-crawl-planner:http-only"

    @staticmethod
    def SEED_PRIORITY_DECAY(index: int) -> float:  # noqa: N802 — documented constant-style name
        """``1 / (1 + index)`` — first seed 1.0, second 0.5, third 1/3, etc."""

        return 1.0 / (1 + index)

    def plan(self, request: PlanRequest) -> PlanDecision:
        planned_seeds = [
            PlannedSeed(
                canonical_url=url,
                priority_score=self.SEED_PRIORITY_DECAY(i),
                adapter_hint=AdapterType.HTTP,
                rationale_ref=f"rationale:{self.ADAPTER_REF}:seed-{i}",
            )
            for i, url in enumerate(request.seed_urls)
        ]
        adapter_priors = [
            AdapterPrior(
                adapter_type=AdapterType.HTTP,
                weight=1.0,
                rationale_ref=self.HTTP_PRIOR_RATIONALE_REF,
            ),
        ]
        return PlanDecision(
            id=f"plan-decision:{request.id}",
            request_ref=request.id,
            planner_adapter_ref=self.ADAPTER_REF,
            planned_seeds=planned_seeds,
            adapter_priors=adapter_priors,
            replay_refs=[
                request.id,
                self.ADAPTER_REF,
                request.replay_config_ref,
                request.objective_ref,
            ],
            policy_decision_refs=list(request.policy_decision_refs),
        )
