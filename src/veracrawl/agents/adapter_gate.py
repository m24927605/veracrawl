"""Core agent runtime adapter operational gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.agent_adapter import (
    REQUIRED_AGENT_FRAMEWORKS,
    AgentAdapterExecutionRecord,
    AgentRuntimeAdapterReport,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AgentAdapterFailureType, CompletenessResult


@dataclass(frozen=True)
class AgentRuntimeAdapterGateResult:
    execution_records: list[AgentAdapterExecutionRecord]
    report: AgentRuntimeAdapterReport


_FAILURES: dict[str, tuple[AgentAdapterFailureType, str]] = {
    "agent-runtime-adapter-raw-prompt-leak": (
        AgentAdapterFailureType.RAW_PROMPT_LEAK,
        "raw_prompt_leak_refs",
    ),
    "agent-runtime-adapter-framework-state-canonical": (
        AgentAdapterFailureType.FRAMEWORK_STATE_CANONICAL,
        "framework_state_canonical_refs",
    ),
    "agent-runtime-adapter-missing-model-trace": (
        AgentAdapterFailureType.MISSING_MODEL_TRACE,
        "model_call_trace_refs",
    ),
    "agent-runtime-adapter-missing-tool-trace": (
        AgentAdapterFailureType.MISSING_TOOL_TRACE,
        "tool_call_trace_refs",
    ),
    "agent-runtime-adapter-missing-replay": (
        AgentAdapterFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "agent-runtime-adapter-missing-security-privacy": (
        AgentAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS,
        "security_privacy_report_refs",
    ),
    "agent-runtime-adapter-unsupported-framework": (
        AgentAdapterFailureType.UNSUPPORTED_FRAMEWORK,
        "unsupported_framework_refs",
    ),
}


def run_agent_runtime_adapter_gate(
    *,
    fixture_id: str,
    scenario: str,
    execution_records: list[AgentAdapterExecutionRecord] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> AgentRuntimeAdapterGateResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:agent-adapter"]
    if scenario == "agent-runtime-adapter-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if not execution_records:
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    return _success_result(
        fixture_id=fixture_id,
        execution_records=execution_records,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    execution_records: list[AgentAdapterExecutionRecord],
    policy_refs: list[Ref],
) -> AgentRuntimeAdapterGateResult:
    verified = [record.framework_name for record in execution_records]
    report = AgentRuntimeAdapterReport(
        id=f"agent-runtime-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        framework_execution_refs=[record.id for record in execution_records],
        required_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
        verified_framework_names=verified,
        model_provider_refs=[f"model-provider-adapter:{fixture_id}:contract"],
        policy_decision_refs=policy_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:agent-adapter"],
        security_privacy_report_refs=[f"security-privacy-report:{fixture_id}:agent-adapter"],
        command_record_refs=[f"command:{fixture_id}:agent-adapter"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:agent-adapter"],
        outbox_refs=[f"outbox:{fixture_id}:agent-adapter"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:agent-adapter",
        operator_status="agent_runtime_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    return AgentRuntimeAdapterGateResult(execution_records=execution_records, report=report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> AgentRuntimeAdapterGateResult:
    report = AgentRuntimeAdapterReport(
        id=f"agent-runtime-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:agent-adapter"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:{framework.lower().replace(' ', '-')}"
            for framework in REQUIRED_AGENT_FRAMEWORKS
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="agent_runtime_adapter_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return AgentRuntimeAdapterGateResult(execution_records=[], report=report)


def _failure_result(
    *,
    fixture_id: str,
    failure: AgentAdapterFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> AgentRuntimeAdapterGateResult:
    raw_prompt_refs = (
        [f"raw-prompt-leak:{fixture_id}:agent-adapter"]
        if missing_field == "raw_prompt_leak_refs"
        else []
    )
    canonical_state_refs = (
        [f"framework-state:{fixture_id}:canonical"]
        if missing_field == "framework_state_canonical_refs"
        else []
    )
    unsupported_refs = (
        [f"unsupported-framework:{fixture_id}:unknown"]
        if missing_field == "unsupported_framework_refs"
        else []
    )
    report = AgentRuntimeAdapterReport(
        id=f"agent-runtime-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
        verified_framework_names=[],
        policy_decision_refs=policy_refs,
        raw_prompt_leak_refs=raw_prompt_refs,
        framework_state_canonical_refs=canonical_state_refs,
        unsupported_framework_refs=unsupported_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return AgentRuntimeAdapterGateResult(execution_records=[], report=report)
