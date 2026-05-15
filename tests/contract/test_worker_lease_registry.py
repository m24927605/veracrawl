"""Registry tests for s16."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry


def test_registry_contains_worker_lease() -> None:
    entry = FOUNDATION_CONTRACTS["WorkerLease"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_contains_work_outcome() -> None:
    entry = FOUNDATION_CONTRACTS["WorkOutcome"]
    assert entry.owner_service is OwnerService.AGENTS


def test_registry_validate_ok() -> None:
    report = validate_registry()
    assert report.ok, report.errors
