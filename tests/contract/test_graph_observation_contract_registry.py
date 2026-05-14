"""Registry tests for s4 graph-observation contracts (tests 16 + 17)."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry

_S4_NAMES = (
    "UrlObservedEvent", "RedirectObservedEvent", "CanonicalObservedEvent",
    "PageStructureObservedEvent", "GraphObservationSnapshot",
)


def test_registry_contains_all_five_graph_observation_contracts() -> None:
    for name in _S4_NAMES:
        assert name in FOUNDATION_CONTRACTS, f"missing entry for {name}"
        reg = FOUNDATION_CONTRACTS[name]
        assert reg.replay_required is True
        assert reg.owner_service is OwnerService.GRAPH
        assert reg.python_model == f"veracrawl.contracts.graph_observation.{name}"


def test_registry_validate_returns_ok() -> None:
    report = validate_registry()
    assert report.ok, f"registry validation failed: {report.errors}"
