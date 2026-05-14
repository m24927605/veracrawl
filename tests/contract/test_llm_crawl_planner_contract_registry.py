"""Contract registry tests for s2 ``LlmCrawlPlanner`` contracts (tests 12 + 13)."""

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
    for name in _S2_CONTRACT_NAMES:
        assert name in FOUNDATION_CONTRACTS, f"missing entry for {name}"
        reg = FOUNDATION_CONTRACTS[name]
        assert reg.replay_required is True, f"{name} requires replay_required=True"
        assert reg.owner_service is OwnerService.AGENTS, f"{name} requires AGENTS"
        assert reg.python_model == f"veracrawl.contracts.llm_crawl_planner.{name}"


def test_registry_validate_returns_ok() -> None:
    report = validate_registry()
    assert report.ok, f"registry validation failed: {report.errors}"
