"""Registry tests for ``PlannerObservationFeedback`` (s5 tests 18-19)."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry


# Test 18
def test_registry_contains_planner_observation_feedback() -> None:
    r = FOUNDATION_CONTRACTS["PlannerObservationFeedback"]
    assert r.owner_service is OwnerService.AGENTS
    assert r.replay_required is True


# Test 19
def test_registry_validate_returns_ok() -> None:
    assert validate_registry().ok
