"""Registry tests for s7 contracts (tests 10-11)."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry


def test_registry_contains_schema_proposal() -> None:
    entry = FOUNDATION_CONTRACTS["SchemaProposal"]
    assert entry.owner_service is OwnerService.AGENTS
    assert entry.replay_required is True


def test_registry_contains_proposed_field_and_read_model() -> None:
    proposed = FOUNDATION_CONTRACTS["ProposedField"]
    read_model = FOUNDATION_CONTRACTS["NormalizedDocumentReadModel"]
    assert proposed.owner_service is OwnerService.AGENTS
    assert read_model.owner_service is OwnerService.AGENTS


def test_registry_validate_returns_ok() -> None:
    report = validate_registry()
    assert report.ok, report.errors
