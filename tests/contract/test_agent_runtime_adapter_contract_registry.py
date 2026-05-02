from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_agent_runtime_adapter_contracts_are_registered() -> None:
    for name in [
        "AgentAdapterExecutionRecord",
        "AgentRuntimeAdapterReport",
        "AgentRuntimeAdapterFixtureManifest",
        "AgentRunRequest",
        "AgentRunResult",
        "AgentActionTrace",
        "ModelCallTrace",
        "ToolCallTrace",
        "ContextBundleTrace",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_agent_runtime_adapter_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_agent_adapter_execution": "agent_adapter_execution_recorded",
        "record_agent_runtime_adapter_report": "agent_runtime_adapter_reported",
        "record_agent_runtime_adapter_fixture_manifest": (
            "agent_runtime_adapter_fixture_manifest_recorded"
        ),
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "agent-runtime-adapter-success",
        "agent-runtime-adapter-runtime-unavailable",
        "agent-runtime-adapter-raw-prompt-leak",
        "agent-runtime-adapter-framework-state-canonical",
        "agent-runtime-adapter-missing-model-trace",
        "agent-runtime-adapter-missing-tool-trace",
        "agent-runtime-adapter-missing-replay",
        "agent-runtime-adapter-missing-security-privacy",
        "agent-runtime-adapter-unsupported-framework",
    ]:
        assert fixture_id in FIXTURE_ORACLES
        assert FIXTURE_ORACLES[fixture_id].expected_agent_adapter_ref


def test_agent_runtime_adapter_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["agent_runtime_adapter_operational_gate"]
    assert area.coverage_status == "materialized"
    assert "AgentRuntimeAdapterReport" in area.materialized_contract_refs
    assert "SecurityPrivacyReport" in area.materialized_contract_refs
