from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_temporal_kg_contracts_are_registered() -> None:
    for name in [
        "TemporalKGEntityIdentity",
        "TemporalKGProjectionRecord",
        "TemporalKGIdentityAdjudicationRecord",
        "TemporalKGRuntimeReport",
        "TemporalKGFixtureManifest",
        "CommandResult",
        "EventCursorRecord",
        "OutboxRecord",
        "ReplayBundleManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_temporal_kg_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "project_temporal_kg_identity": "temporal_kg_identity_projected",
        "project_temporal_kg_record": "temporal_kg_record_projected",
        "adjudicate_temporal_kg_identity": "temporal_kg_identity_adjudicated",
        "record_temporal_kg_report": "temporal_kg_reported",
        "record_temporal_kg_fixture_manifest": "temporal_kg_fixture_manifest_recorded",
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "temporal-kg-projection-success",
        "temporal-kg-false-merge-adjudicated",
        "temporal-kg-false-split-superseded",
        "temporal-kg-runtime-unavailable",
        "temporal-kg-provisional-identity",
        "temporal-kg-projection-as-evidence",
        "temporal-kg-missing-canonical-source",
        "temporal-kg-missing-bitemporal-refs",
        "temporal-kg-false-merge-without-adjudication",
        "temporal-kg-false-split-without-supersession",
        "temporal-kg-missing-replay",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_graph_ref


def test_temporal_kg_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["temporal_kg_identity_projection_gate"]
    assert area.coverage_status == "materialized"
    assert "TemporalKGEntityIdentity" in area.materialized_contract_refs
    assert "TemporalKGProjectionRecord" in area.materialized_contract_refs
    assert "TemporalKGIdentityAdjudicationRecord" in area.materialized_contract_refs
    assert "TemporalKGRuntimeReport" in area.materialized_contract_refs
