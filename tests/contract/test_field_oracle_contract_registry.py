from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
)


def test_field_oracle_contracts_are_registered() -> None:
    for name in [
        "FieldOracleFieldSpec",
        "FieldOracleSchema",
        "ExpectedFieldValue",
        "FieldEvaluationRecord",
        "FieldOracleBenchmarkReport",
        "FieldOracleBenchmarkManifest",
    ]:
        assert name in FOUNDATION_CONTRACTS
        assert FOUNDATION_CONTRACTS[name].owner_service.value in {"extract", "tests"}


def test_field_oracle_commands_and_events_are_registered() -> None:
    for command in [
        "record_field_oracle_evaluation",
        "record_field_oracle_report",
        "record_field_oracle_manifest",
    ]:
        assert command in COMMAND_TYPES
        for event in COMMAND_TYPES[command].emitted_event_types:
            assert event in EVENT_TYPES


def test_field_oracle_fixtures_are_registered() -> None:
    assert FIXTURE_ORACLES["field-oracle-quality-corpus"].negative_case is False
    for fixture_id in [
        "field-oracle-wrong-value",
        "field-oracle-missing-anchor",
        "field-oracle-schema-violation",
        "field-oracle-stale-evidence",
        "field-oracle-publication-bypass",
        "field-oracle-llm-as-evidence",
    ]:
        assert FIXTURE_ORACLES[fixture_id].negative_case is True
        assert FIXTURE_ORACLES[fixture_id].expected_field_oracle_ref


def test_field_oracle_target_area_is_registered() -> None:
    area = TARGET_CONTRACT_AREAS["field_oracle_extraction_benchmark"]
    assert "FieldOracleBenchmarkReport" in area.materialized_contract_refs
    assert "EvidencePacket" in area.materialized_contract_refs
    assert "VerificationDecision" in area.materialized_contract_refs
