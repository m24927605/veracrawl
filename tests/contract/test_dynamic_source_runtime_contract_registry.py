from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_dynamic_source_runtime_contracts_are_registered() -> None:
    for name in [
        "DynamicSourceRuntimeAdapterRecord",
        "DynamicSourceRuntimeReport",
        "DynamicSourceRuntimeFixtureManifest",
        "SourceAdapterResult",
        "FetchAttempt",
        "PageSnapshot",
        "BrowserInteractionStep",
        "CredentialUseAudit",
        "DocumentArtifact",
        "CommandResult",
        "EventCursorRecord",
        "OutboxRecord",
        "ObservabilityReport",
        "SecurityPrivacyReport",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_dynamic_source_runtime_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_dynamic_source_runtime_adapter": "dynamic_source_runtime_adapter_recorded",
        "record_dynamic_source_runtime_report": "dynamic_source_runtime_reported",
        "record_dynamic_source_runtime_fixture_manifest": (
            "dynamic_source_runtime_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "dynamic-source-runtime-success",
        "dynamic-source-runtime-runtime-unavailable",
        "dynamic-source-runtime-raw-secret-leak",
        "dynamic-source-runtime-adapter-state-canonical",
        "dynamic-source-runtime-missing-credential-audit",
        "dynamic-source-runtime-missing-document-artifact",
        "dynamic-source-runtime-missing-api-payload",
        "dynamic-source-runtime-missing-replay",
        "dynamic-source-runtime-unsafe-browser-side-effect",
        "dynamic-source-runtime-unsupported-adapter",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_dynamic_source_runtime_ref


def test_dynamic_source_runtime_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["dynamic_source_adapter_runtime_foundation"]
    assert area.coverage_status == "materialized"
    assert "DynamicSourceRuntimeAdapterRecord" in area.materialized_contract_refs
    assert "DynamicSourceRuntimeReport" in area.materialized_contract_refs
    assert "DynamicSourceRuntimeFixtureManifest" in area.materialized_contract_refs
    assert "SecurityPrivacyReport" in area.materialized_contract_refs
