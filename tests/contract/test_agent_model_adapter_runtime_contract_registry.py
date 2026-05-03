from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_agent_model_adapter_runtime_contracts_are_registered() -> None:
    for name in [
        "AgentModelAdapterRuntimeReport",
        "AgentModelAdapterFixtureManifest",
        "ModelProviderAdapterExecutionRecord",
        "AgentAdapterExecutionRecord",
        "AgentRunRequest",
        "AgentRunResult",
        "ModelRequest",
        "ModelResponse",
        "ModelCallTrace",
        "ToolCallTrace",
        "ContextBundleTrace",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_agent_model_adapter_runtime_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_agent_model_adapter_runtime_report": (
            "agent_model_adapter_runtime_reported"
        ),
        "record_agent_model_adapter_fixture_manifest": (
            "agent_model_adapter_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "agent-model-adapter-local-runtime-success",
        "agent-model-adapter-runtime-unavailable",
        "agent-model-adapter-missing-run-control",
        "agent-model-adapter-missing-live-normalization",
        "agent-model-adapter-missing-schema-extraction",
        "agent-model-adapter-unsupported-provider",
        "agent-model-adapter-unsupported-framework",
        "agent-model-adapter-raw-prompt-leak",
        "agent-model-adapter-raw-response-leak",
        "agent-model-adapter-raw-credential-leak",
        "agent-model-adapter-framework-state-canonical",
        "agent-model-adapter-provider-transcript-canonical",
        "agent-model-adapter-missing-model-trace",
        "agent-model-adapter-missing-tool-trace",
        "agent-model-adapter-missing-replay",
        "agent-model-adapter-core-import-boundary",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_agent_model_adapter_ref


def test_agent_model_adapter_runtime_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["real_agent_model_adapter_runtime"]
    assert area.coverage_status == "materialized"
    assert "AgentModelAdapterRuntimeReport" in area.materialized_contract_refs
    assert "AgentAdapterExecutionRecord" in area.materialized_contract_refs
