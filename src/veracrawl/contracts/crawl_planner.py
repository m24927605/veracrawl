"""Crawl-planner port contracts (s1 of general-purpose-crawler-agentification).

See ``docs/plans/general-purpose-crawler-agentification/
s1-crawl-planner-port-contract.md`` for the typed surface of one
``CrawlPlannerPort.plan(request)`` call.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, VeraModel
from veracrawl.contracts.enums import AdapterType, FrontierMatchKind

_SUM_TOL = 1.0 + 1e-9
_HOST_GLOB = re.compile(r"^[a-zA-Z0-9._*-]+$")
_MIME_PREFIX = re.compile(r"^[a-zA-Z0-9!#$&^_.+-]+/[a-zA-Z0-9!#$&^_.+*-]*$")


def _is_http_url(value: str) -> bool:
    p = urlparse(value)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class PlannedSeed(VeraModel):
    canonical_url: str
    priority_score: float
    adapter_hint: AdapterType
    rationale_ref: Ref
    @model_validator(mode="after")
    def _validate(self) -> PlannedSeed:
        _require(_is_http_url(self.canonical_url), "canonical_url must be absolute http(s)")
        _require(0.0 <= self.priority_score <= 1.0, "priority_score must be in [0.0, 1.0]")
        _require(bool(self.rationale_ref.strip()), "rationale_ref must be non-blank")
        return self


class AdapterPrior(VeraModel):
    adapter_type: AdapterType
    weight: float
    rationale_ref: Ref
    @model_validator(mode="after")
    def _validate(self) -> AdapterPrior:
        _require(0.0 <= self.weight <= 1.0, "weight must be in [0.0, 1.0]")
        _require(bool(self.rationale_ref.strip()), "rationale_ref must be non-blank")
        return self


class FrontierPriorityHint(VeraModel):
    match_kind: FrontierMatchKind
    match_value: str
    priority_delta: float
    rationale_ref: Ref
    @model_validator(mode="after")
    def _validate(self) -> FrontierPriorityHint:
        _require(-1.0 <= self.priority_delta <= 1.0, "priority_delta must be in [-1.0, 1.0]")
        _require(bool(self.match_value.strip()), "match_value must be non-blank")
        if self.match_kind is FrontierMatchKind.URL_PREFIX:
            _require(_is_http_url(self.match_value), "match_value must be http(s) URL")
        elif self.match_kind is FrontierMatchKind.HOST_GLOB:
            _require(bool(_HOST_GLOB.match(self.match_value)), "match_value must be host glob")
        else:
            _require(bool(_MIME_PREFIX.match(self.match_value)), "match_value must be type/subtype")
        _require(bool(self.rationale_ref.strip()), "rationale_ref must be non-blank")
        return self


class PlanRequest(VeraModel):
    id: str
    run_ref: Ref
    objective_ref: Ref
    seed_urls: list[str]
    budget_ref: Ref
    policy_snapshot_ref: Ref
    policy_decision_refs: list[Ref]
    replay_config_ref: Ref
    observed_state_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate(self) -> PlanRequest:
        for name in ("id", "run_ref", "objective_ref", "budget_ref",
                     "policy_snapshot_ref", "replay_config_ref"):
            _require(bool(getattr(self, name).strip()), f"{name} must be non-blank")
        _require(bool(self.seed_urls), "seed_urls must be non-empty")
        for i, url in enumerate(self.seed_urls):
            _require(_is_http_url(url), f"seed_urls[{i}] must be absolute http(s) URL")
        _require(len(set(self.seed_urls)) == len(self.seed_urls),
                 "seed_urls must not contain duplicate URLs")
        _require(bool(self.policy_decision_refs), "policy_decision_refs must be non-empty")
        return self


class PlanDecision(VeraModel):
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
    def _validate(self) -> PlanDecision:
        _require(bool(self.request_ref.strip()), "request_ref must be non-blank")
        _require(bool(self.planner_adapter_ref.strip()), "planner_adapter_ref must be non-blank")
        _require(bool(self.planned_seeds), "planned_seeds must be non-empty")
        _require(bool(self.adapter_priors), "adapter_priors must be non-empty")
        seen: set[AdapterType] = set()
        for p in self.adapter_priors:
            _require(p.adapter_type not in seen,
                     f"adapter_priors duplicate adapter_type: {p.adapter_type.value}")
            seen.add(p.adapter_type)
        total = sum(p.weight for p in self.adapter_priors)
        _require(total <= _SUM_TOL, f"adapter_priors weight sum must be ≤ 1.0 (got {total})")
        _require(self.request_ref in self.replay_refs,
                 "replay_refs must contain request_ref")
        _require(self.planner_adapter_ref in self.replay_refs,
                 "replay_refs must contain planner_adapter_ref")
        _require(bool(self.policy_decision_refs), "policy_decision_refs must be non-empty")
        return self
