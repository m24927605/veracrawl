"""Deterministic agent framework contract adapters.

These adapters are adapter-owned and intentionally avoid importing real agent
framework SDKs. They prove canonical VeraCrawl mapping for framework families.
"""

from __future__ import annotations

from veracrawl.contracts.agent_adapter import (
    REQUIRED_AGENT_FRAMEWORKS,
    AgentAdapterExecutionRecord,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult


def framework_slug(framework_name: str) -> str:
    return framework_name.lower().replace(" ", "-")


def build_contract_execution_records(
    fixture_id: str,
    *,
    framework_names: list[str] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> list[AgentAdapterExecutionRecord]:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:agent-adapter"]
    return [
        build_contract_execution_record(
            fixture_id,
            framework_name=framework_name,
            policy_decision_refs=policy_refs,
        )
        for framework_name in (framework_names or list(REQUIRED_AGENT_FRAMEWORKS))
    ]


def build_contract_execution_record(
    fixture_id: str,
    *,
    framework_name: str,
    policy_decision_refs: list[Ref],
) -> AgentAdapterExecutionRecord:
    slug = framework_slug(framework_name)
    return AgentAdapterExecutionRecord(
        id=f"agent-adapter-execution:{fixture_id}:{slug}",
        framework_name=framework_name,
        runtime_spec_ref=f"agent-runtime-spec:{fixture_id}:{slug}",
        agent_run_request_ref=f"agent-run-request:{fixture_id}:{slug}",
        agent_run_result_ref=f"agent-run-result:{fixture_id}:{slug}",
        agent_action_trace_ref=f"agent-action-trace:{fixture_id}:{slug}",
        model_call_trace_refs=[f"model-call-trace:{fixture_id}:{slug}"],
        tool_call_trace_refs=[f"tool-call-trace:{fixture_id}:{slug}:read"],
        context_bundle_trace_ref=f"context-bundle-trace:{fixture_id}:{slug}",
        command_result_refs=[f"command-result:{fixture_id}:{slug}:read"],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:agent-adapter"],
        security_privacy_report_refs=[f"security-privacy-report:{fixture_id}:agent-adapter"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:agent-adapter",
        live_runtime_refs=[f"agent-runtime-instance:{fixture_id}:{slug}:contract"],
        contract_adapter_refs=[f"contract-adapter:{fixture_id}:{slug}"],
        diagnostic_framework_state_refs=[f"diagnostic-framework-state:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )
