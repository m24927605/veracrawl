"""Source acquisition runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    DynamicSourceRuntimeFailureType,
    RateLimitDecisionValue,
    SourceFailureType,
)

REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS = (
    AdapterType.HTTP,
    AdapterType.SITEMAP,
    AdapterType.RSS,
    AdapterType.BROWSER_SNAPSHOT,
    AdapterType.AUTHORIZED_SESSION,
    AdapterType.API_SOURCE,
    AdapterType.DOCUMENT_SOURCE,
    AdapterType.FILE_IMPORT,
    AdapterType.MANUAL_SEED,
    AdapterType.PRIOR_SNAPSHOT,
)

_NON_FETCH_RUNTIME_ADAPTERS = {
    AdapterType.AUTHORIZED_SESSION,
    AdapterType.FILE_IMPORT,
    AdapterType.MANUAL_SEED,
    AdapterType.PRIOR_SNAPSHOT,
}


class RateLimitDecision(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    decision: RateLimitDecisionValue
    rate_limit_policy_ref: Ref
    retry_after_ref: Ref | None = None
    reason_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rate_limit(self) -> RateLimitDecision:
        if self.decision == RateLimitDecisionValue.RATE_LIMIT:
            if not self.retry_after_ref or not self.reason_refs:
                raise ValueError("rate-limited decision requires retry_after and reasons")
        return self


class SourceFailureReport(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    failure_type: SourceFailureType
    operator_status: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    retry_refs: list[Ref] = Field(default_factory=list)
    diagnostic_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_failure(self) -> SourceFailureReport:
        if not self.operator_status or not self.diagnostic_refs:
            raise ValueError("source failure report requires operator status and diagnostics")
        return self


class SourceAcquisitionReport(TimestampedModel):
    id: str
    run_ref: Ref
    source_adapter_result_ref: Ref | None = None
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    frontier_item_ref: Ref
    lease_ref: Ref
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> SourceAcquisitionReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "source_adapter_result_ref": self.source_adapter_result_ref,
                "fetch_attempt_refs": self.fetch_attempt_refs,
                "fetch_result_refs": self.fetch_result_refs,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "recovery_report_refs": self.recovery_report_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing source acquisition report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError("non-pass source acquisition report requires failures or missing refs")
        return self


class SourceFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    adapter_type: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_result_type: str | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> SourceFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("source fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative source fixture must not expect pass")
        return self


class DynamicSourceRuntimeAdapterRecord(TimestampedModel):
    id: str
    adapter_type: AdapterType
    source_adapter_result_ref: Ref
    natural_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    browser_interaction_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    document_artifact_refs: list[Ref] = Field(default_factory=list)
    api_payload_refs: list[Ref] = Field(default_factory=list)
    file_artifact_refs: list[Ref] = Field(default_factory=list)
    seed_plan_refs: list[Ref] = Field(default_factory=list)
    prior_snapshot_refs: list[Ref] = Field(default_factory=list)
    command_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    live_runtime_refs: list[Ref] = Field(default_factory=list)
    contract_adapter_refs: list[Ref] = Field(default_factory=list)
    diagnostic_adapter_state_refs: list[Ref] = Field(default_factory=list)
    raw_secret_persisted: bool = False
    adapter_native_state_canonical: bool = False
    unsafe_browser_side_effect_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_dynamic_source_runtime_record(self) -> DynamicSourceRuntimeAdapterRecord:
        if self.raw_secret_persisted:
            raise ValueError("dynamic source runtime cannot persist raw secret")
        if self.adapter_native_state_canonical:
            raise ValueError("dynamic source runtime cannot canonicalize adapter-native state")
        if (
            self.adapter_type in _NON_FETCH_RUNTIME_ADAPTERS
            and (self.fetch_attempt_refs or self.page_snapshot_refs)
        ):
            raise ValueError("non-fetch source runtime must not fake fetch/page refs")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_adapter_result_ref": self.source_adapter_result_ref,
                "natural_result_refs": self.natural_result_refs,
                "command_result_refs": self.command_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            if self.adapter_type == AdapterType.HTTP:
                required["fetch_attempt_refs"] = self.fetch_attempt_refs
                required["page_snapshot_refs"] = self.page_snapshot_refs
            if self.adapter_type == AdapterType.BROWSER_SNAPSHOT:
                required["browser_interaction_refs"] = self.browser_interaction_refs
                required["page_snapshot_refs"] = self.page_snapshot_refs
            if self.adapter_type == AdapterType.AUTHORIZED_SESSION:
                required["credential_audit_refs"] = self.credential_audit_refs
            if self.adapter_type == AdapterType.API_SOURCE:
                required["api_payload_refs"] = self.api_payload_refs
            if self.adapter_type == AdapterType.DOCUMENT_SOURCE:
                required["document_artifact_refs"] = self.document_artifact_refs
            if self.adapter_type == AdapterType.FILE_IMPORT:
                required["file_artifact_refs"] = self.file_artifact_refs
            if self.adapter_type == AdapterType.MANUAL_SEED:
                required["seed_plan_refs"] = self.seed_plan_refs
            if self.adapter_type == AdapterType.PRIOR_SNAPSHOT:
                required["prior_snapshot_refs"] = self.prior_snapshot_refs
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing dynamic source runtime missing refs: {missing}")
            if self.unsafe_browser_side_effect_refs:
                raise ValueError(
                    "passing dynamic source runtime cannot include unsafe browser refs"
                )
            if not (self.live_runtime_refs or self.contract_adapter_refs):
                raise ValueError("passing dynamic source runtime requires runtime or contract refs")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_adapter_refs or self.missing_ref_fields):
                raise ValueError("needs-review dynamic source runtime requires review refs")
        return self


class DynamicSourceRuntimeReport(TimestampedModel):
    id: str
    run_ref: Ref
    adapter_record_refs: list[Ref] = Field(default_factory=list)
    required_adapter_types: list[AdapterType] = Field(
        default_factory=lambda: list(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS)
    )
    verified_adapter_types: list[AdapterType] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    natural_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    browser_interaction_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    document_artifact_refs: list[Ref] = Field(default_factory=list)
    api_payload_refs: list[Ref] = Field(default_factory=list)
    file_artifact_refs: list[Ref] = Field(default_factory=list)
    seed_plan_refs: list[Ref] = Field(default_factory=list)
    prior_snapshot_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    runtime_adapter_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    adapter_native_state_canonical_refs: list[Ref] = Field(default_factory=list)
    unsafe_browser_side_effect_refs: list[Ref] = Field(default_factory=list)
    unsupported_adapter_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_dynamic_source_runtime_report(self) -> DynamicSourceRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "adapter_record_refs": self.adapter_record_refs,
                "source_adapter_result_refs": self.source_adapter_result_refs,
                "natural_result_refs": self.natural_result_refs,
                "fetch_attempt_refs": self.fetch_attempt_refs,
                "page_snapshot_refs": self.page_snapshot_refs,
                "browser_interaction_refs": self.browser_interaction_refs,
                "credential_audit_refs": self.credential_audit_refs,
                "document_artifact_refs": self.document_artifact_refs,
                "api_payload_refs": self.api_payload_refs,
                "file_artifact_refs": self.file_artifact_refs,
                "seed_plan_refs": self.seed_plan_refs,
                "prior_snapshot_refs": self.prior_snapshot_refs,
                "command_record_refs": self.command_record_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "runtime_adapter_refs": self.runtime_adapter_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            adapter_gap = set(self.required_adapter_types) - set(self.verified_adapter_types)
            if (
                missing
                or adapter_gap
                or self.contract_only_refs
                or self.missing_runtime_refs
                or self.raw_secret_leak_refs
                or self.adapter_native_state_canonical_refs
                or self.unsafe_browser_side_effect_refs
                or self.unsupported_adapter_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    "passing dynamic source runtime report missing refs: "
                    f"{missing}, adapter_gap={sorted(adapter_gap)}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review dynamic source runtime report requires review refs")
        elif not (
            self.raw_secret_leak_refs
            or self.adapter_native_state_canonical_refs
            or self.unsafe_browser_side_effect_refs
            or self.unsupported_adapter_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed dynamic source runtime report requires failure details")
        return self


class DynamicSourceRuntimeFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: DynamicSourceRuntimeFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_dynamic_source_fixture(self) -> DynamicSourceRuntimeFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("dynamic source runtime fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative dynamic source runtime fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
