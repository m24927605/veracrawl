"""Registry tests for s8.a contracts."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry


def test_registry_contains_drift_report() -> None:
    entry = FOUNDATION_CONTRACTS["DriftReport"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_contains_repair_proposal() -> None:
    entry = FOUNDATION_CONTRACTS["RepairProposal"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_contains_extraction_outcome() -> None:
    entry = FOUNDATION_CONTRACTS["ExtractionOutcome"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_validate_ok() -> None:
    report = validate_registry()
    assert report.ok, report.errors
