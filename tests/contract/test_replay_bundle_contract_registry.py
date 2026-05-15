"""Registry tests for s11 ``ReplayBundle``."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry


def test_registry_contains_replay_bundle() -> None:
    entry = FOUNDATION_CONTRACTS["ReplayBundle"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_validate_ok() -> None:
    report = validate_registry()
    assert report.ok, report.errors
