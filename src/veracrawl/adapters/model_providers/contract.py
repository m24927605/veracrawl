"""Deterministic model provider contract adapters."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.model_provider_adapter import (
    REQUIRED_MODEL_PROVIDERS,
    ModelProviderAdapterExecutionRecord,
)


def provider_slug(provider_name: str) -> str:
    return provider_name.lower().replace(" ", "-")


def build_contract_execution_records(
    fixture_id: str,
    *,
    provider_names: list[str] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> list[ModelProviderAdapterExecutionRecord]:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:model-provider"]
    return [
        build_contract_execution_record(
            fixture_id,
            provider_name=provider_name,
            policy_decision_refs=policy_refs,
        )
        for provider_name in (provider_names or list(REQUIRED_MODEL_PROVIDERS))
    ]


def build_contract_execution_record(
    fixture_id: str,
    *,
    provider_name: str,
    policy_decision_refs: list[Ref],
) -> ModelProviderAdapterExecutionRecord:
    slug = provider_slug(provider_name)
    return ModelProviderAdapterExecutionRecord(
        id=f"model-provider-execution:{fixture_id}:{slug}",
        provider_name=provider_name,
        runtime_spec_ref=f"agent-runtime-spec:{fixture_id}:{slug}:model-provider",
        model_request_ref=f"model-request:{fixture_id}:{slug}",
        model_response_ref=f"model-response:{fixture_id}:{slug}",
        model_call_trace_ref=f"model-call-trace:{fixture_id}:{slug}",
        context_bundle_trace_ref=f"context-bundle-trace:{fixture_id}:{slug}",
        agent_run_request_ref=f"agent-run-request:{fixture_id}:{slug}",
        agent_run_result_ref=f"agent-run-result:{fixture_id}:{slug}",
        agent_action_trace_ref=f"agent-action-trace:{fixture_id}:{slug}",
        command_result_refs=[f"command-result:{fixture_id}:{slug}:model"],
        policy_decision_refs=policy_decision_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:model-provider"],
        security_privacy_report_refs=[f"security-privacy-report:{fixture_id}:model-provider"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:model-provider",
        live_runtime_refs=[f"model-provider-runtime:{fixture_id}:{slug}:contract"],
        contract_adapter_refs=[f"model-provider-contract-adapter:{fixture_id}:{slug}"],
        diagnostic_provider_state_refs=[f"diagnostic-provider-state:{fixture_id}:{slug}"],
        result=CompletenessResult.PASS,
    )
