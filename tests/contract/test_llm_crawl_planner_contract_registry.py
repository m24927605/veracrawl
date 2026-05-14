"""Contract registry tests for s2 ``LlmCrawlPlanner`` contracts.

Implements the s2 plan's red list section ``tests/contract/
test_llm_crawl_planner_contract_registry.py`` (tests 12 + 13).
Asserts the four LLM-output contracts are registered in
``FOUNDATION_CONTRACTS`` with ``replay_required=True`` and
``owner_service=OwnerService.AGENTS`` (mirroring s1's pattern).
"""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry

_S2_CONTRACT_NAMES = (
    "LlmPlanProposal",
    "LlmProposedSeed",
    "LlmProposedAdapterPrior",
    "LlmProposedFrontierPriorityHint",
)


def test_registry_contains_all_four_llm_planner_contracts() -> None:
    """Test 12 — registry registers all four s2 contracts correctly."""

    for name in _S2_CONTRACT_NAMES:
        assert name in FOUNDATION_CONTRACTS, f"missing registry entry for {name}"
        registration = FOUNDATION_CONTRACTS[name]
        assert registration.replay_required is True, (
            f"{name} must register with replay_required=True"
        )
        assert registration.owner_service is OwnerService.AGENTS, (
            f"{name} must register with owner_service=AGENTS"
        )
        assert (
            registration.python_model
            == f"veracrawl.contracts.llm_crawl_planner.{name}"
        ), f"{name} python_model must point at veracrawl.contracts.llm_crawl_planner"


def test_registry_validate_returns_ok() -> None:
    """Test 13 — global registry validation still passes."""

    report = validate_registry()
    assert report.ok, f"registry validation failed: {report.errors}"
