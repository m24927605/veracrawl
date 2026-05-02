from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_model_provider_adapter_contracts_are_registered() -> None:
    for name in [
        "ModelProviderAdapterExecutionRecord",
        "ModelProviderAdapterReport",
        "ModelProviderAdapterFixtureManifest",
        "ModelRequest",
        "ModelResponse",
        "ModelCallTrace",
        "ContextBundleTrace",
        "AgentRunRequest",
        "AgentRunResult",
        "AgentActionTrace",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_model_provider_adapter_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_model_provider_adapter_execution": (
            "model_provider_adapter_execution_recorded"
        ),
        "record_model_provider_adapter_report": "model_provider_adapter_reported",
        "record_model_provider_adapter_fixture_manifest": (
            "model_provider_adapter_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "model-provider-adapter-success",
        "model-provider-adapter-runtime-unavailable",
        "model-provider-adapter-raw-prompt-leak",
        "model-provider-adapter-raw-response-leak",
        "model-provider-adapter-provider-state-canonical",
        "model-provider-adapter-missing-context-trace",
        "model-provider-adapter-missing-replay",
        "model-provider-adapter-missing-security-privacy",
        "model-provider-adapter-unsafe-tool-suggestion",
        "model-provider-adapter-unsupported-provider",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_model_provider_ref


def test_model_provider_adapter_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["model_provider_adapter_operational_gate"]
    assert area.coverage_status == "materialized"
    assert "ModelProviderAdapterReport" in area.materialized_contract_refs
    assert "SecurityPrivacyReport" in area.materialized_contract_refs
