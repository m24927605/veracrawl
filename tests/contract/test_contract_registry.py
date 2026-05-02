from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    registry_json,
    validate_registry,
)


def test_registry_is_complete_and_valid() -> None:
    report = validate_registry()
    assert report.ok, report.errors
    assert "CommandEnvelope" in FOUNDATION_CONTRACTS
    assert "TargetContractAreaCoverage" in FOUNDATION_CONTRACTS
    assert registry_json().startswith("{")


def test_target_contract_area_coverage_is_explicit() -> None:
    expected = {
        "source_adapters",
        "commands",
        "events",
        "replay",
        "agent_runtime",
        "fixture_oracles",
        "evidence",
        "verification",
        "publication",
        "projection",
        "graph",
        "memory",
        "export",
        "ops",
        "artifact_lifecycle",
        "durable_persistence",
        "scheduler",
        "source_acquisition",
        "network_browser_acquisition",
        "normalize_extract",
    }
    assert set(TARGET_CONTRACT_AREAS) == expected
    for area, registration in TARGET_CONTRACT_AREAS.items():
        assert registration.contract_area == area
        assert registration.required_test_refs
        if registration.coverage_status != "materialized":
            assert registration.followup_spec_gate


def test_command_and_event_schema_refs_resolve() -> None:
    schema_refs = set(FOUNDATION_CONTRACTS)
    for command in COMMAND_TYPES.values():
        assert command.payload_schema_ref in schema_refs
        for event_type in command.emitted_event_types:
            assert event_type in EVENT_TYPES
    for event_type in EVENT_TYPES.values():
        assert event_type.payload_schema_ref in schema_refs
        assert event_type.replay_critical_refs


def test_cross_owner_mutation_is_represented_by_command_registry() -> None:
    for command in COMMAND_TYPES.values():
        assert command.owner_service
        assert command.target_aggregate_type
        assert "owning service" not in command.owner_service.value
