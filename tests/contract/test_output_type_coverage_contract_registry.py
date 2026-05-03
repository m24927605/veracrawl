from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_output_type_coverage_contracts_are_registered() -> None:
    for name in [
        "OutputTypeCoverageRecord",
        "OutputTypePublicationGateReport",
        "OutputTypeCoverageFixtureManifest",
        "EvidencePacket",
        "EvidenceCoverageResult",
        "VerificationDecision",
        "PublishedOutput",
        "OutputManifest",
        "CommandResult",
        "EventCursorRecord",
        "OutboxRecord",
        "ReplayBundleManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_output_type_coverage_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_output_type_coverage": "output_type_coverage_recorded",
        "record_output_type_coverage_report": "output_type_coverage_reported",
        "record_output_type_coverage_fixture_manifest": (
            "output_type_coverage_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "output-type-coverage-success",
        "output-type-coverage-runtime-unavailable",
        "output-type-coverage-missing-output-type",
        "output-type-coverage-unsupported-output-type",
        "output-type-coverage-derived-context-as-evidence",
        "output-type-coverage-candidate-as-evidence",
        "output-type-coverage-graph-as-evidence",
        "output-type-coverage-memory-as-evidence",
        "output-type-coverage-agent-reasoning-as-evidence",
        "output-type-coverage-temporal-kg-as-evidence",
        "output-type-coverage-missing-table-cell-evidence",
        "output-type-coverage-missing-file-lifecycle",
        "output-type-coverage-missing-dataset-item-evidence",
        "output-type-coverage-missing-fact-verification",
        "output-type-coverage-missing-replay",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_evidence_ref


def test_output_type_coverage_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["output_type_coverage_gate"]
    assert area.coverage_status == "materialized"
    assert "OutputTypeCoverageRecord" in area.materialized_contract_refs
    assert "OutputTypePublicationGateReport" in area.materialized_contract_refs
    assert "OutputTypeCoverageFixtureManifest" in area.materialized_contract_refs
