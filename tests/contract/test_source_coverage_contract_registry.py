from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_source_coverage_contracts_are_registered() -> None:
    for name in [
        "SourceCoverageAdapterExecutionRecord",
        "SourceCoverageAdapterReport",
        "SourceCoverageAdapterFixtureManifest",
        "SourceAdapterSpec",
        "SourceAdapterResult",
        "FetchAttempt",
        "PageSnapshot",
        "BrowserInteractionStep",
        "CredentialUseAudit",
        "DocumentArtifact",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_source_coverage_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_source_coverage_adapter_execution": (
            "source_coverage_adapter_execution_recorded"
        ),
        "record_source_coverage_adapter_report": "source_coverage_adapter_reported",
        "record_source_coverage_adapter_fixture_manifest": (
            "source_coverage_adapter_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "source-coverage-adapter-success",
        "source-coverage-adapter-runtime-unavailable",
        "source-coverage-adapter-native-state-canonical",
        "source-coverage-adapter-raw-secret-leak",
        "source-coverage-adapter-missing-browser-refs",
        "source-coverage-adapter-missing-credential-audit",
        "source-coverage-adapter-missing-document-artifact",
        "source-coverage-adapter-missing-api-payload",
        "source-coverage-adapter-missing-replay",
        "source-coverage-adapter-unsafe-browser-side-effect",
        "source-coverage-adapter-unsupported-adapter",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_source_coverage_ref


def test_source_coverage_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["source_coverage_adapter_operational_gate"]
    assert area.coverage_status == "materialized"
    assert "SourceCoverageAdapterExecutionRecord" in area.materialized_contract_refs
    assert "SourceCoverageAdapterReport" in area.materialized_contract_refs
    assert "SecurityPrivacyReport" in area.materialized_contract_refs
