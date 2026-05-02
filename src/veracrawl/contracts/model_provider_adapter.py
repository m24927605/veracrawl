"""Model provider adapter operational gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, ModelProviderAdapterFailureType

REQUIRED_MODEL_PROVIDERS = (
    "OpenAI",
    "Anthropic",
    "Google Gemini",
    "OpenAI-compatible endpoint",
    "Local model runtime",
    "FutureProvider",
)


class ModelProviderAdapterExecutionRecord(TimestampedModel):
    id: str
    provider_name: str
    runtime_spec_ref: Ref
    model_request_ref: Ref
    model_response_ref: Ref
    model_call_trace_ref: Ref
    context_bundle_trace_ref: Ref
    agent_run_request_ref: Ref
    agent_run_result_ref: Ref
    agent_action_trace_ref: Ref
    command_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    live_runtime_refs: list[Ref] = Field(default_factory=list)
    contract_adapter_refs: list[Ref] = Field(default_factory=list)
    diagnostic_provider_state_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_credential_persisted: bool = False
    provider_transcript_canonical: bool = False
    unsafe_tool_suggestion_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_execution_record(self) -> ModelProviderAdapterExecutionRecord:
        if self.raw_prompt_persisted:
            raise ValueError("model provider adapter execution cannot persist raw prompt")
        if self.raw_response_persisted:
            raise ValueError("model provider adapter execution cannot persist raw response")
        if self.raw_credential_persisted:
            raise ValueError("model provider adapter execution cannot persist raw credential")
        if self.provider_transcript_canonical:
            raise ValueError("provider-native transcript cannot be canonical")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "runtime_spec_ref": self.runtime_spec_ref,
                "model_request_ref": self.model_request_ref,
                "model_response_ref": self.model_response_ref,
                "model_call_trace_ref": self.model_call_trace_ref,
                "context_bundle_trace_ref": self.context_bundle_trace_ref,
                "agent_run_request_ref": self.agent_run_request_ref,
                "agent_run_result_ref": self.agent_run_result_ref,
                "agent_action_trace_ref": self.agent_action_trace_ref,
                "command_result_refs": self.command_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing model provider execution missing refs: {missing}")
            if self.unsafe_tool_suggestion_refs:
                raise ValueError("passing model provider execution cannot include unsafe tool refs")
            if not (self.live_runtime_refs or self.contract_adapter_refs):
                raise ValueError(
                    "passing model provider execution requires runtime or contract refs"
                )
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_adapter_refs or self.missing_ref_fields):
                raise ValueError("needs-review provider execution requires review refs")
        return self


class ModelProviderAdapterReport(TimestampedModel):
    id: str
    run_ref: Ref
    provider_execution_refs: list[Ref] = Field(default_factory=list)
    required_provider_names: list[str] = Field(
        default_factory=lambda: list(REQUIRED_MODEL_PROVIDERS)
    )
    verified_provider_names: list[str] = Field(default_factory=list)
    model_request_refs: list[Ref] = Field(default_factory=list)
    model_response_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    agent_run_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    raw_prompt_leak_refs: list[Ref] = Field(default_factory=list)
    raw_response_leak_refs: list[Ref] = Field(default_factory=list)
    raw_credential_leak_refs: list[Ref] = Field(default_factory=list)
    provider_transcript_canonical_refs: list[Ref] = Field(default_factory=list)
    unsafe_tool_suggestion_refs: list[Ref] = Field(default_factory=list)
    unsupported_provider_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> ModelProviderAdapterReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "provider_execution_refs": self.provider_execution_refs,
                "model_request_refs": self.model_request_refs,
                "model_response_refs": self.model_response_refs,
                "model_call_trace_refs": self.model_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "agent_run_refs": self.agent_run_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            provider_gap = set(self.required_provider_names) - set(self.verified_provider_names)
            if (
                missing
                or provider_gap
                or self.contract_only_refs
                or self.missing_runtime_refs
                or self.raw_prompt_leak_refs
                or self.raw_response_leak_refs
                or self.raw_credential_leak_refs
                or self.provider_transcript_canonical_refs
                or self.unsafe_tool_suggestion_refs
                or self.unsupported_provider_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    "passing model provider adapter report missing refs: "
                    f"{missing}, provider_gap={sorted(provider_gap)}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review provider report requires review refs")
        elif not (
            self.raw_prompt_leak_refs
            or self.raw_response_leak_refs
            or self.raw_credential_leak_refs
            or self.provider_transcript_canonical_refs
            or self.unsafe_tool_suggestion_refs
            or self.unsupported_provider_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed provider report requires failure details")
        return self


class ModelProviderAdapterFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ModelProviderAdapterFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ModelProviderAdapterFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("model provider adapter fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative model provider adapter fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
