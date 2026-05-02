from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports
from veracrawl.ports.durable import (
    DurableCommandHandlerPort,
    DurableEventStorePort,
    OutboxRepositoryPort,
    UnitOfWorkPort,
)
from veracrawl.ports.scheduler import SchedulerStatePort


def test_durable_ports_are_protocols() -> None:
    for port in [
        UnitOfWorkPort,
        DurableEventStorePort,
        OutboxRepositoryPort,
        DurableCommandHandlerPort,
        SchedulerStatePort,
    ]:
        assert getattr(port, "_is_protocol", False) is True


def test_durable_core_has_no_concrete_infrastructure_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_durable_modules_are_not_site_specific() -> None:
    root = Path(__file__).parents[2] / "src" / "veracrawl"
    durable_files = [
        path
        for path in root.rglob("*.py")
        if any(part in {"scheduler", "runtime_support", "runtime_events"} for part in path.parts)
    ]
    forbidden = {"amazon", "shopify", "linkedin", "single_site", "scraper"}
    assert not {
        path for path in durable_files if any(token in path.name.lower() for token in forbidden)
    }
