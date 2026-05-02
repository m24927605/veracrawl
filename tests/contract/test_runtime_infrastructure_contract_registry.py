from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_runtime_infrastructure_contracts_are_registered() -> None:
    for name in [
        "RuntimeInfrastructureSpec",
        "RuntimeInfrastructureReport",
        "RuntimeInfrastructureFixtureManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS


def test_runtime_infrastructure_commands_events_and_fixtures_are_registered() -> None:
    assert "record_runtime_infrastructure_spec" in COMMAND_TYPES
    assert "record_runtime_infrastructure_report" in COMMAND_TYPES
    assert "runtime_infrastructure_spec_recorded" in EVENT_TYPES
    assert "runtime_infrastructure_reported" in EVENT_TYPES
    for fixture_id in [
        "operational-infrastructure-success",
        "operational-infrastructure-idempotency-success",
        "operational-infrastructure-runtime-unavailable",
        "infrastructure-missing-persistence-refs",
        "infrastructure-missing-queue-refs",
        "infrastructure-missing-object-refs",
        "infrastructure-missing-replay-refs",
    ]:
        assert fixture_id in FIXTURE_ORACLES
    assert "operational_runtime_infrastructure_gate" in TARGET_CONTRACT_AREAS
