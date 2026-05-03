"""Source coverage adapter operational gate contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
    SourceCoverageFailureType,
)

REQUIRED_SOURCE_COVERAGE_ADAPTERS = (
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

REQUIRED_SOURCE_ADAPTER_TYPES = REQUIRED_SOURCE_COVERAGE_ADAPTERS

EXPECTED_NATURAL_RESULT_TYPES = {
    AdapterType.HTTP: SourceAdapterResultType.FETCH_RESULT,
    AdapterType.SITEMAP: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.RSS: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.BROWSER_SNAPSHOT: SourceAdapterResultType.BROWSER_SNAPSHOT,
    AdapterType.AUTHORIZED_SESSION: SourceAdapterResultType.SESSION_STATE,
    AdapterType.API_SOURCE: SourceAdapterResultType.API_PAYLOAD,
    AdapterType.DOCUMENT_SOURCE: SourceAdapterResultType.DOCUMENT_ARTIFACT,
    AdapterType.FILE_IMPORT: SourceAdapterResultType.FILE_ARTIFACT,
    AdapterType.MANUAL_SEED: SourceAdapterResultType.SEED_PLAN,
    AdapterType.PRIOR_SNAPSHOT: SourceAdapterResultType.PRIOR_SNAPSHOT_REF,
}


class SourceCoverageAdapterExecutionRecord(TimestampedModel):
    id: str
    adapter_type: AdapterType
    natural_result_type: SourceAdapterResultType
    source_adapter_spec_ref: Ref
    source_adapter_result_ref: Ref
    natural_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    browser_interaction_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    document_artifact_refs: list[Ref] = Field(default_factory=list)
    api_payload_refs: list[Ref] = Field(default_factory=list)
    command_result_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
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
    def validate_execution_record(self) -> SourceCoverageAdapterExecutionRecord:
        if self.raw_secret_persisted:
            raise ValueError("source coverage execution cannot persist raw secret")
        if self.adapter_native_state_canonical:
            raise ValueError("adapter-native state cannot be canonical")
        if self.natural_result_type != EXPECTED_NATURAL_RESULT_TYPES[self.adapter_type]:
            raise ValueError("source coverage natural result type mismatch")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_adapter_spec_ref": self.source_adapter_spec_ref,
                "source_adapter_result_ref": self.source_adapter_result_ref,
                "natural_result_refs": self.natural_result_refs,
                "command_result_refs": self.command_result_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
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
            if self.adapter_type in {AdapterType.DOCUMENT_SOURCE, AdapterType.FILE_IMPORT}:
                required["document_artifact_refs"] = self.document_artifact_refs
            if self.adapter_type == AdapterType.API_SOURCE:
                required["api_payload_refs"] = self.api_payload_refs
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing source coverage execution missing refs: {missing}")
            if self.unsafe_browser_side_effect_refs:
                raise ValueError("passing source coverage cannot include unsafe browser refs")
            if not (self.live_runtime_refs or self.contract_adapter_refs):
                raise ValueError("passing source coverage requires runtime or contract refs")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_adapter_refs or self.missing_ref_fields):
                raise ValueError("needs-review source coverage execution requires review refs")
        return self


class SourceCoverageAdapterReport(TimestampedModel):
    id: str
    run_ref: Ref
    adapter_execution_refs: list[Ref] = Field(default_factory=list)
    required_adapter_types: list[AdapterType] = Field(
        default_factory=lambda: list(REQUIRED_SOURCE_ADAPTER_TYPES)
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
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    security_privacy_report_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
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
    def validate_report(self) -> SourceCoverageAdapterReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "adapter_execution_refs": self.adapter_execution_refs,
                "source_adapter_result_refs": self.source_adapter_result_refs,
                "natural_result_refs": self.natural_result_refs,
                "fetch_attempt_refs": self.fetch_attempt_refs,
                "page_snapshot_refs": self.page_snapshot_refs,
                "browser_interaction_refs": self.browser_interaction_refs,
                "credential_audit_refs": self.credential_audit_refs,
                "document_artifact_refs": self.document_artifact_refs,
                "api_payload_refs": self.api_payload_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "observability_report_refs": self.observability_report_refs,
                "security_privacy_report_refs": self.security_privacy_report_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
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
                    "passing source coverage report missing refs: "
                    f"{missing}, adapter_gap={sorted(adapter_gap)}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review source coverage report requires review refs")
        elif not (
            self.raw_secret_leak_refs
            or self.adapter_native_state_canonical_refs
            or self.unsafe_browser_side_effect_refs
            or self.unsupported_adapter_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed source coverage report requires failure details")
        return self


class SourceCoverageAdapterFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: SourceCoverageFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> SourceCoverageAdapterFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("source coverage fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative source coverage fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
