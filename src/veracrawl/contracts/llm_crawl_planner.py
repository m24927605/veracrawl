"""LLM-output contracts for s2's ``LlmCrawlPlanner`` adapter.

See ``docs/plans/general-purpose-crawler-agentification/
s2-llm-crawl-planner-adapter.md``. The four pydantic models below
are what the LLM is required to emit (validated via JSON-object
response format) before the adapter projects the output into the
s1 ``PlanDecision`` shape.
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


class LlmProposedSeed(VeraModel):
    canonical_url: str
    priority_score: float
    adapter_hint: AdapterType
    @model_validator(mode="after")
    def _validate(self) -> LlmProposedSeed:
        _require(_is_http_url(self.canonical_url), "canonical_url must be absolute http(s)")
        _require(0.0 <= self.priority_score <= 1.0, "priority_score must be in [0.0, 1.0]")
        return self


class LlmProposedAdapterPrior(VeraModel):
    adapter_type: AdapterType
    weight: float
    @model_validator(mode="after")
    def _validate(self) -> LlmProposedAdapterPrior:
        _require(0.0 <= self.weight <= 1.0, "weight must be in [0.0, 1.0]")
        return self


class LlmProposedFrontierPriorityHint(VeraModel):
    match_kind: FrontierMatchKind
    match_value: str
    priority_delta: float
    @model_validator(mode="after")
    def _validate(self) -> LlmProposedFrontierPriorityHint:
        _require(-1.0 <= self.priority_delta <= 1.0, "priority_delta must be in [-1.0, 1.0]")
        _require(bool(self.match_value.strip()), "match_value must be non-blank")
        if self.match_kind is FrontierMatchKind.URL_PREFIX:
            _require(_is_http_url(self.match_value), "match_value must be http(s) URL")
        elif self.match_kind is FrontierMatchKind.HOST_GLOB:
            _require(bool(_HOST_GLOB.match(self.match_value)), "match_value must be host glob")
        else:
            _require(bool(_MIME_PREFIX.match(self.match_value)), "match_value must be type/subtype")
        return self


class LlmPlanProposal(VeraModel):
    planned_seeds: list[LlmProposedSeed]
    adapter_priors: list[LlmProposedAdapterPrior]
    frontier_priority_hints: list[LlmProposedFrontierPriorityHint] = Field(default_factory=list)
    extraction_strategy_refs: list[Ref] = Field(default_factory=list)
    rationale_summary: str
    @model_validator(mode="after")
    def _validate(self) -> LlmPlanProposal:
        _require(bool(self.planned_seeds), "planned_seeds must be non-empty")
        _require(bool(self.adapter_priors), "adapter_priors must be non-empty")
        seen: set[AdapterType] = set()
        for p in self.adapter_priors:
            _require(p.adapter_type not in seen,
                     f"adapter_priors duplicate adapter_type: {p.adapter_type.value}")
            seen.add(p.adapter_type)
        total = sum(p.weight for p in self.adapter_priors)
        _require(total <= _SUM_TOL, f"adapter_priors weight sum must be ≤ 1.0 (got {total})")
        _require(bool(self.rationale_summary.strip()), "rationale_summary must be non-blank")
        return self
