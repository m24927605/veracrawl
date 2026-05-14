"""Contract tests for ``veracrawl.contracts.llm_crawl_planner`` (s2 step 1).

Implements the s2 plan's red list, section ``tests/contract/
test_llm_crawl_planner_contracts.py``. Tests 1-11 cover the four
LLM-output pydantic models (``LlmProposedSeed``,
``LlmProposedAdapterPrior``, ``LlmProposedFrontierPriorityHint``,
``LlmPlanProposal``); test 11a covers the typed-error inheritance
for ``ProviderTraceMissingError`` (iter-4 finding 4).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import AdapterType, FrontierMatchKind
from veracrawl.contracts.errors import (
    FatalError,
    ProviderTraceMissingError,
    ReplayLookupMissError,
    VeraCrawlError,
)
from veracrawl.contracts.llm_crawl_planner import (
    LlmPlanProposal,
    LlmProposedAdapterPrior,
    LlmProposedFrontierPriorityHint,
    LlmProposedSeed,
)


def _valid_proposed_seed() -> dict[str, object]:
    return {
        "canonical_url": "https://example.com/seed",
        "priority_score": 0.7,
        "adapter_hint": AdapterType.HTTP,
    }


def _valid_proposed_adapter_prior() -> dict[str, object]:
    return {"adapter_type": AdapterType.HTTP, "weight": 0.6}


def _valid_proposed_frontier_priority_hint() -> dict[str, object]:
    return {
        "match_kind": FrontierMatchKind.URL_PREFIX,
        "match_value": "https://example.com/",
        "priority_delta": 0.2,
    }


def _valid_plan_proposal() -> dict[str, object]:
    return {
        "planned_seeds": [LlmProposedSeed(**_valid_proposed_seed())],
        "adapter_priors": [LlmProposedAdapterPrior(**_valid_proposed_adapter_prior())],
        "frontier_priority_hints": [],
        "extraction_strategy_refs": [],
        "rationale_summary": "llm rationale",
    }


# Test 1
def test_llm_proposed_seed_rejects_non_http_url() -> None:
    payload = _valid_proposed_seed() | {"canonical_url": "file:///tmp"}
    with pytest.raises(ValidationError, match="canonical_url"):
        LlmProposedSeed(**payload)


# Test 2
def test_llm_proposed_seed_rejects_priority_out_of_range() -> None:
    payload = _valid_proposed_seed() | {"priority_score": 1.5}
    with pytest.raises(ValidationError, match="priority_score"):
        LlmProposedSeed(**payload)


# Test 3
def test_llm_proposed_adapter_prior_rejects_weight_out_of_range() -> None:
    payload = _valid_proposed_adapter_prior() | {"weight": -0.1}
    with pytest.raises(ValidationError, match="weight"):
        LlmProposedAdapterPrior(**payload)


# Test 4
def test_llm_proposed_frontier_priority_hint_rejects_delta_out_of_range() -> None:
    payload = _valid_proposed_frontier_priority_hint() | {"priority_delta": 2.0}
    with pytest.raises(ValidationError, match="priority_delta"):
        LlmProposedFrontierPriorityHint(**payload)


# Test 5
def test_llm_proposed_frontier_priority_hint_rejects_blank_match_value() -> None:
    payload = _valid_proposed_frontier_priority_hint() | {"match_value": ""}
    with pytest.raises(ValidationError, match="match_value"):
        LlmProposedFrontierPriorityHint(**payload)


# Test 6
def test_llm_proposed_frontier_priority_hint_rejects_match_value_inconsistent_with_kind() -> None:
    payload = _valid_proposed_frontier_priority_hint() | {
        "match_kind": FrontierMatchKind.URL_PREFIX,
        "match_value": "not-a-url",
    }
    with pytest.raises(ValidationError, match="match_value"):
        LlmProposedFrontierPriorityHint(**payload)


# Test 7
def test_llm_plan_proposal_rejects_empty_planned_seeds() -> None:
    payload = _valid_plan_proposal() | {"planned_seeds": []}
    with pytest.raises(ValidationError, match="planned_seeds"):
        LlmPlanProposal(**payload)


# Test 8
def test_llm_plan_proposal_rejects_empty_adapter_priors() -> None:
    payload = _valid_plan_proposal() | {"adapter_priors": []}
    with pytest.raises(ValidationError, match="adapter_priors"):
        LlmPlanProposal(**payload)


# Test 9
def test_llm_plan_proposal_rejects_duplicate_adapter_types() -> None:
    duplicate = [
        LlmProposedAdapterPrior(adapter_type=AdapterType.HTTP, weight=0.4),
        LlmProposedAdapterPrior(adapter_type=AdapterType.HTTP, weight=0.3),
    ]
    payload = _valid_plan_proposal() | {"adapter_priors": duplicate}
    with pytest.raises(ValidationError, match="adapter_priors"):
        LlmPlanProposal(**payload)


# Test 10
def test_llm_plan_proposal_rejects_adapter_priors_sum_above_one() -> None:
    over_one = [
        LlmProposedAdapterPrior(adapter_type=AdapterType.HTTP, weight=0.5),
        LlmProposedAdapterPrior(adapter_type=AdapterType.SITEMAP, weight=0.5),
        LlmProposedAdapterPrior(adapter_type=AdapterType.RSS, weight=0.5),
    ]
    payload = _valid_plan_proposal() | {"adapter_priors": over_one}
    with pytest.raises(ValidationError, match="sum"):
        LlmPlanProposal(**payload)


# Test 11
def test_llm_plan_proposal_rejects_blank_rationale_summary() -> None:
    payload = _valid_plan_proposal() | {"rationale_summary": ""}
    with pytest.raises(ValidationError, match="rationale_summary"):
        LlmPlanProposal(**payload)


# Test 11a — iter-4 finding 4: typed-error inheritance pinned.
def test_provider_trace_missing_error_is_fatal_error_subclass() -> None:
    assert issubclass(ProviderTraceMissingError, FatalError)
    assert issubclass(ProviderTraceMissingError, VeraCrawlError)


# Test 11a-ctor — s2 step-1 task-review iter 1: domain-specific
# constructor + message. The error mirrors ``PromptTemplateNotFoundError``
# (single kwarg, no ``ModelProviderError`` plumbing).
def test_provider_trace_missing_error_constructs_with_domain_kwarg() -> None:
    err = ProviderTraceMissingError(provider_request_id="provider-request:test:1")
    assert err.provider_request_id == "provider-request:test:1"
    assert "provider-request:test:1" in str(err)
    assert "raw_response_ref" in str(err)


# Test 11b — s2 step-1 task-review iter 1: ReplayLookupMissError typing
# + constructor.
def test_replay_lookup_miss_error_is_fatal_error_subclass_and_constructs() -> None:
    assert issubclass(ReplayLookupMissError, FatalError)
    assert issubclass(ReplayLookupMissError, VeraCrawlError)
    err = ReplayLookupMissError(provider_request_id="provider-request:test:2")
    assert err.provider_request_id == "provider-request:test:2"
    assert "provider-request:test:2" in str(err)
