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
        "output_type_coverage_gate",
        "website_pattern_coverage_gate",
        "product_acceptance_gate",
        "evidence_publication",
        "projection",
        "graph",
        "memory",
        "export",
        "ops",
        "artifact_lifecycle",
        "operational_object_store_adapter",
        "durable_persistence",
        "production_persistence_queue_runtime",
        "concrete_persistence_adapters",
        "operational_postgres_persistence_adapter",
        "operational_queue_broker_adapter",
        "operational_runtime_infrastructure_gate",
        "operational_disaster_recovery_gate",
        "operational_observability_gate",
        "security_privacy_lifecycle_gate",
        "agent_runtime_adapter_operational_gate",
        "model_provider_adapter_operational_gate",
        "source_coverage_adapter_operational_gate",
        "dynamic_source_adapter_runtime_foundation",
        "graph_frontier_review_runtime_gate",
        "temporal_kg_identity_projection_gate",
        "scheduler",
        "source_acquisition",
        "network_browser_acquisition",
        "normalize_extract",
        "scale_reliability",
    }
    assert set(TARGET_CONTRACT_AREAS) == expected
    for area, registration in TARGET_CONTRACT_AREAS.items():
        assert registration.contract_area == area
        assert registration.required_test_refs
        if registration.coverage_status != "materialized":
            assert registration.followup_spec_gate


def test_materialized_target_areas_have_closed_readiness_impact() -> None:
    unresolved_terms = ("before target-complete", "must define", "placeholder")
    for area, registration in TARGET_CONTRACT_AREAS.items():
        if registration.coverage_status != "materialized":
            assert registration.followup_spec_gate
            continue
        assert registration.materialized_contract_refs, area
        assert not registration.placeholder_contract_refs, area
        assert registration.followup_spec_gate is None, area
        impact_text = (
            f"{registration.replay_impact} {registration.privacy_lifecycle_impact}"
        ).lower()
        for term in unresolved_terms:
            assert term not in impact_text, (area, term, impact_text)
        assert "materialized" in impact_text


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
