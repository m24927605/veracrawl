"""Contract registry tests for s1 ``CrawlPlanner`` contracts.

Implements the s1 plan's red list, section ``tests/contract/
test_crawl_planner_contract_registry.py`` (tests 18 + 19).
Confirms the five s1 contracts are registered in
``FOUNDATION_CONTRACTS`` with ``replay_required=True`` and
``owner_service=OwnerService.AGENTS``, and that
``validate_registry()`` still returns ``ok``.
"""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry

_S1_CONTRACT_NAMES = (
    "PlanRequest",
    "PlannedSeed",
    "AdapterPrior",
    "FrontierPriorityHint",
    "PlanDecision",
)


def test_registry_contains_all_five_planner_contracts() -> None:
    """Test 18 — registry registers all five s1 contracts correctly."""

    for name in _S1_CONTRACT_NAMES:
        assert name in FOUNDATION_CONTRACTS, f"missing registry entry for {name}"
        registration = FOUNDATION_CONTRACTS[name]
        assert registration.replay_required is True, (
            f"{name} must register with replay_required=True"
        )
        assert registration.owner_service is OwnerService.AGENTS, (
            f"{name} must register with owner_service=AGENTS"
        )
        assert registration.python_model == f"veracrawl.contracts.crawl_planner.{name}", (
            f"{name} python_model must point at veracrawl.contracts.crawl_planner"
        )


def test_registry_validate_returns_ok() -> None:
    """Test 19 — global registry validation still passes."""

    report = validate_registry()
    assert report.ok, f"registry validation failed: {report.errors}"
