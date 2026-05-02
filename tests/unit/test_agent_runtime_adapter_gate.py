from __future__ import annotations

from veracrawl.adapters.agent_frameworks.contract import build_contract_execution_records
from veracrawl.agents.adapter_gate import run_agent_runtime_adapter_gate
from veracrawl.contracts.agent_adapter import REQUIRED_AGENT_FRAMEWORKS
from veracrawl.contracts.enums import AgentAdapterFailureType, CompletenessResult


def test_agent_runtime_adapter_gate_success_requires_all_frameworks() -> None:
    fixture_id = "unit"
    result = run_agent_runtime_adapter_gate(
        fixture_id=fixture_id,
        scenario="agent-runtime-adapter-success",
        execution_records=build_contract_execution_records(fixture_id),
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.verified_framework_names) == set(REQUIRED_AGENT_FRAMEWORKS)
    assert report.framework_execution_refs
    assert report.model_provider_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.replay_bundle_ref
    assert result.execution_records


def test_agent_runtime_adapter_runtime_unavailable_needs_review() -> None:
    result = run_agent_runtime_adapter_gate(
        fixture_id="unit-no-runtime",
        scenario="agent-runtime-adapter-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_agent_runtime_adapter_negative_scenarios_fail() -> None:
    expectations = {
        "agent-runtime-adapter-raw-prompt-leak": AgentAdapterFailureType.RAW_PROMPT_LEAK,
        "agent-runtime-adapter-framework-state-canonical": (
            AgentAdapterFailureType.FRAMEWORK_STATE_CANONICAL
        ),
        "agent-runtime-adapter-missing-model-trace": (
            AgentAdapterFailureType.MISSING_MODEL_TRACE
        ),
        "agent-runtime-adapter-missing-tool-trace": AgentAdapterFailureType.MISSING_TOOL_TRACE,
        "agent-runtime-adapter-missing-replay": AgentAdapterFailureType.MISSING_REPLAY_REFS,
        "agent-runtime-adapter-missing-security-privacy": (
            AgentAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS
        ),
        "agent-runtime-adapter-unsupported-framework": (
            AgentAdapterFailureType.UNSUPPORTED_FRAMEWORK
        ),
    }
    for scenario, failure in expectations.items():
        result = run_agent_runtime_adapter_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
