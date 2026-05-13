"""Crawl-planner port contracts (s1 of the general-purpose-crawler-agentification topic).

Implements the contract surface declared in
``docs/plans/general-purpose-crawler-agentification/
s1-crawl-planner-port-contract.md``. The five models below are the
typed result of one call to ``CrawlPlannerPort.plan(request)``:
given a ``PlanRequest`` (caller-supplied ``seed_urls`` + budget /
policy / replay refs), the planner returns a ``PlanDecision``
carrying ``PlannedSeed`` triage, ``AdapterPrior`` weights, and
``FrontierPriorityHint`` patterns.

This module is intentionally framework-neutral: it depends only on
``veracrawl.contracts.common`` (the ``VeraModel`` /
``TimestampedModel`` strict-config base) and
``veracrawl.contracts.enums`` (``AdapterType``, ``FrontierMatchKind``).
No model SDK, no browser, no storage, no agent framework imports.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AdapterType, FrontierMatchKind

_ADAPTER_PRIOR_SUM_TOLERANCE = 1.0 + 1e-9
_HOST_GLOB_RE = re.compile(r"^[a-zA-Z0-9._*-]+$")
_MIME_PREFIX_RE = re.compile(r"^[a-zA-Z0-9!#$&^_.+-]+/[a-zA-Z0-9!#$&^_.+*-]*$")


def _is_http_url(value: str) -> bool:
    """Match ``contracts.agent._is_http_url`` semantics without crossing the boundary.

    The s1 plan's open question 1 explicitly preserves duplication
    over cross-module reach into an underscore-prefixed symbol. The
    check is intentionally identical: ``http`` or ``https`` scheme
    plus a non-empty network location.
    """

    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


# ---------------------------------------------------------------------------
# PlannedSeed
# ---------------------------------------------------------------------------


class PlannedSeed(TimestampedModel):
    """One canonical URL the planner decided to admit to the frontier."""

    canonical_url: str
    priority_score: float
    adapter_hint: AdapterType
    rationale_ref: Ref

    @model_validator(mode="after")
    def validate_planned_seed(self) -> PlannedSeed:
        if not _is_http_url(self.canonical_url):
            raise ValueError(
                "planned seed canonical_url must be an absolute http(s) URL"
            )
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("planned seed priority_score must be in [0.0, 1.0]")
        if not self.rationale_ref.strip():
            raise ValueError("planned seed rationale_ref must be non-blank")
        return self


# ---------------------------------------------------------------------------
# AdapterPrior
# ---------------------------------------------------------------------------


class AdapterPrior(TimestampedModel):
    """Relative weight the planner assigns to one source adapter."""

    adapter_type: AdapterType
    weight: float
    rationale_ref: Ref

    @model_validator(mode="after")
    def validate_adapter_prior(self) -> AdapterPrior:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("adapter prior weight must be in [0.0, 1.0]")
        if not self.rationale_ref.strip():
            raise ValueError("adapter prior rationale_ref must be non-blank")
        return self


# ---------------------------------------------------------------------------
# FrontierPriorityHint
# ---------------------------------------------------------------------------


class FrontierPriorityHint(TimestampedModel):
    """A pattern-based priority delta the planner suggests to the frontier."""

    match_kind: FrontierMatchKind
    match_value: str
    priority_delta: float
    rationale_ref: Ref

    @model_validator(mode="after")
    def validate_frontier_priority_hint(self) -> FrontierPriorityHint:
        if not -1.0 <= self.priority_delta <= 1.0:
            raise ValueError(
                "frontier priority hint priority_delta must be in [-1.0, 1.0]"
            )
        if not self.match_value.strip():
            raise ValueError("frontier priority hint match_value must be non-blank")
        if self.match_kind is FrontierMatchKind.URL_PREFIX:
            if not _is_http_url(self.match_value):
                raise ValueError(
                    "frontier priority hint match_value must be an absolute "
                    "http(s) URL prefix when match_kind is url_prefix"
                )
        elif self.match_kind is FrontierMatchKind.HOST_GLOB:
            if not _HOST_GLOB_RE.match(self.match_value):
                raise ValueError(
                    "frontier priority hint match_value must be a host glob "
                    "([a-zA-Z0-9._*-]+) when match_kind is host_glob"
                )
        else:  # CONTENT_TYPE_PREFIX
            if not _MIME_PREFIX_RE.match(self.match_value):
                raise ValueError(
                    "frontier priority hint match_value must be a type/subtype "
                    "prefix when match_kind is content_type_prefix"
                )
        if not self.rationale_ref.strip():
            raise ValueError(
                "frontier priority hint rationale_ref must be non-blank"
            )
        return self


# ---------------------------------------------------------------------------
# PlanRequest
# ---------------------------------------------------------------------------


class PlanRequest(TimestampedModel):
    """Input to ``CrawlPlannerPort.plan``.

    The caller supplies the candidate ``seed_urls`` plus the lineage
    refs the planner needs to record provenance. The objective body
    is referenced (``objective_ref``) but **not** required to be
    resolved by the planner in s1 — that's a later slice's port.
    """

    id: str
    run_ref: Ref
    objective_ref: Ref
    seed_urls: list[str]
    budget_ref: Ref
    policy_snapshot_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_config_ref: Ref
    observed_state_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plan_request(self) -> PlanRequest:
        scalars: dict[str, str] = {
            "id": self.id,
            "run_ref": self.run_ref,
            "objective_ref": self.objective_ref,
            "budget_ref": self.budget_ref,
            "policy_snapshot_ref": self.policy_snapshot_ref,
            "replay_config_ref": self.replay_config_ref,
        }
        for name, value in scalars.items():
            if not value.strip():
                raise ValueError(f"plan request {name} must be non-blank")
        if not self.seed_urls:
            raise ValueError("plan request seed_urls must be non-empty")
        for index, url in enumerate(self.seed_urls):
            if not _is_http_url(url):
                raise ValueError(
                    f"plan request seed_urls[{index}] must be an absolute "
                    "http(s) URL"
                )
        if len(set(self.seed_urls)) != len(self.seed_urls):
            raise ValueError("plan request seed_urls must not contain duplicate URLs")
        if not self.policy_decision_refs:
            raise ValueError("plan request policy_decision_refs must be non-empty")
        return self


# ---------------------------------------------------------------------------
# PlanDecision
# ---------------------------------------------------------------------------


class PlanDecision(TimestampedModel):
    """Output of ``CrawlPlannerPort.plan``.

    Carries the planner's triage of the caller's seed URLs plus
    adapter-prior weights, frontier hints, and the replay /
    policy-decision provenance refs.
    """

    id: str
    request_ref: Ref
    planner_adapter_ref: Ref
    planned_seeds: list[PlannedSeed]
    adapter_priors: list[AdapterPrior]
    frontier_priority_hints: list[FrontierPriorityHint] = Field(default_factory=list)
    extraction_strategy_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref]
    policy_decision_refs: list[Ref]

    @model_validator(mode="after")
    def validate_plan_decision(self) -> PlanDecision:
        if not self.request_ref.strip():
            raise ValueError("plan decision request_ref must be non-blank")
        if not self.planner_adapter_ref.strip():
            raise ValueError("plan decision planner_adapter_ref must be non-blank")
        if not self.planned_seeds:
            raise ValueError("plan decision planned_seeds must be non-empty")
        if not self.adapter_priors:
            raise ValueError("plan decision adapter_priors must be non-empty")
        seen: set[AdapterType] = set()
        for prior in self.adapter_priors:
            if prior.adapter_type in seen:
                raise ValueError(
                    "plan decision adapter_priors must have unique adapter_type "
                    f"values (duplicate: {prior.adapter_type.value})"
                )
            seen.add(prior.adapter_type)
        weight_sum = sum(prior.weight for prior in self.adapter_priors)
        if weight_sum > _ADAPTER_PRIOR_SUM_TOLERANCE:
            raise ValueError(
                "plan decision adapter_priors weight sum must be ≤ 1.0 + 1e-9 "
                f"(got {weight_sum})"
            )
        if self.request_ref not in self.replay_refs:
            raise ValueError(
                "plan decision replay_refs must contain request_ref for replay "
                "lineage"
            )
        if self.planner_adapter_ref not in self.replay_refs:
            raise ValueError(
                "plan decision replay_refs must contain planner_adapter_ref for "
                "replay lineage"
            )
        if not self.policy_decision_refs:
            raise ValueError("plan decision policy_decision_refs must be non-empty")
        return self
