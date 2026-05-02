from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_memory_contracts_registered() -> None:
    for contract in [
        "MemoryEvent",
        "MemoryRetrievalTrace",
        "CrossScopeMemoryTunnel",
        "OperationalTemporalMemoryRecord",
        "MemoryKernelReport",
        "MemoryFixtureManifest",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_memory_commands_events_fixtures_registered() -> None:
    assert {"write_memory_event", "retrieve_memory", "record_memory_kernel_report"}.issubset(
        COMMAND_TYPES
    )
    assert {"memory_written", "memory_retrieved", "memory_kernel_reported"}.issubset(
        EVENT_TYPES
    )
    assert TARGET_CONTRACT_AREAS["memory"].coverage_status == "materialized"
    assert {
        "memory-write-retrieve-success",
        "memory-invalidation-exclusion",
        "cross-scope-sanitized-memory",
        "poisoned-memory-blocked",
        "unauthorized-cross-scope-memory",
        "memory-as-evidence",
    }.issubset(FIXTURE_ORACLES)


def test_memory_registry_validation_passes() -> None:
    assert validate_registry().ok
