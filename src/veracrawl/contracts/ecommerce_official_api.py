"""Official ecommerce API product availability benchmark contracts."""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult

EcommerceOfficialApiPlatform = Literal["amazon", "ebay"]


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _origin(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}"


class EcommerceOfficialApiTargetSpec(TimestampedModel):
    id: str
    site_name: str
    platform: EcommerceOfficialApiPlatform
    api_family: str
    allowed_origin: str
    entry_point_url: str
    product_identifier_type: str
    product_identifier: str
    required_identity_terms: list[str] = Field(default_factory=list)
    credential_env_vars: list[str] = Field(default_factory=list)
    required_evidence_types: list[str] = Field(default_factory=list)
    timeout_ms: int = 30000
    size_budget_bytes: int = 768 * 1024
    expected_site_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_target(self) -> EcommerceOfficialApiTargetSpec:
        if not _is_http_url(self.allowed_origin) or not _is_http_url(self.entry_point_url):
            raise ValueError("official ecommerce API URLs must be absolute http(s)")
        if _origin(self.entry_point_url) != self.allowed_origin:
            raise ValueError("official ecommerce API entry point must stay inside allowed origin")
        if not self.required_identity_terms:
            raise ValueError("official ecommerce API target requires identity terms")
        if not self.credential_env_vars:
            raise ValueError("official ecommerce API target requires credential env vars")
        if not self.required_evidence_types:
            raise ValueError("official ecommerce API target requires evidence types")
        if self.timeout_ms < 1 or self.size_budget_bytes < 1:
            raise ValueError("official ecommerce API target budgets must be positive")
        return self


class EcommerceOfficialApiSourceFetch(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    platform: EcommerceOfficialApiPlatform
    request_url: str
    final_url: str
    status_code: int
    content_type: str
    byte_count: int
    content_hash_ref: Ref
    redacted_artifact_ref: Ref
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    credential_grant_ref: Ref
    credential_audit_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref

    @model_validator(mode="after")
    def validate_source_fetch(self) -> EcommerceOfficialApiSourceFetch:
        if not _is_http_url(self.request_url) or not _is_http_url(self.final_url):
            raise ValueError("official ecommerce API source fetch URLs must be http(s)")
        if self.status_code < 100 or self.status_code > 599:
            raise ValueError("official ecommerce API source fetch status must be HTTP")
        required: dict[str, object] = {
            "content_hash_ref": self.content_hash_ref,
            "redacted_artifact_ref": self.redacted_artifact_ref,
            "source_anchor_refs": self.source_anchor_refs,
            "credential_grant_ref": self.credential_grant_ref,
            "credential_audit_ref": self.credential_audit_ref,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"official ecommerce API source fetch missing refs: {missing}")
        return self


class EcommerceOfficialApiRedactedArtifact(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    platform: EcommerceOfficialApiPlatform
    source_url: str
    status_code: int
    content_type: str
    byte_count: int
    content_hash_ref: Ref
    redaction_policy_refs: list[Ref] = Field(default_factory=list)
    body_preview: str
    body_preview_truncated: bool

    @model_validator(mode="after")
    def validate_redacted_artifact(self) -> EcommerceOfficialApiRedactedArtifact:
        if not _is_http_url(self.source_url):
            raise ValueError("official ecommerce API redacted artifact URL must be http(s)")
        if not self.content_hash_ref or not self.redaction_policy_refs:
            raise ValueError("official ecommerce API redacted artifact requires refs")
        return self


class EcommerceOfficialApiFieldEvidence(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    field_name: str
    raw_text: str
    normalized_value: str
    amount: float | None = None
    currency: str | None = None
    source_anchor_ref: Ref
    redacted_artifact_ref: Ref
    content_hash_ref: Ref
    credential_audit_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_field(self) -> EcommerceOfficialApiFieldEvidence:
        if self.field_name not in {"identity", "price", "availability"}:
            raise ValueError("unsupported official ecommerce API field")
        if self.completion_result != CompletenessResult.PASS:
            raise ValueError("official ecommerce API field evidence must be passing")
        required: dict[str, object] = {
            "raw_text": self.raw_text,
            "normalized_value": self.normalized_value,
            "source_anchor_ref": self.source_anchor_ref,
            "redacted_artifact_ref": self.redacted_artifact_ref,
            "content_hash_ref": self.content_hash_ref,
            "credential_audit_ref": self.credential_audit_ref,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"official ecommerce API field missing refs: {missing}")
        if self.field_name == "price" and (self.amount is None or not self.currency):
            raise ValueError("official ecommerce API price evidence requires amount and currency")
        if self.llm_output_evidence_refs:
            raise ValueError("LLM output cannot be official ecommerce API source evidence")
        return self


class EcommerceOfficialApiSiteResult(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    platform: EcommerceOfficialApiPlatform
    api_family: str
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    identity_evidence_ref: Ref | None = None
    price_evidence_ref: Ref | None = None
    availability_evidence_ref: Ref | None = None
    price_raw_text: str | None = None
    price_amount: float | None = None
    price_currency: str | None = None
    availability_raw_text: str | None = None
    availability_status: str | None = None
    authorized_source_ref: Ref | None = None
    redacted_artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    failure_type: str | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_site(self) -> EcommerceOfficialApiSiteResult:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "field_evidence_refs": self.field_evidence_refs,
                "identity_evidence_ref": self.identity_evidence_ref,
                "price_evidence_ref": self.price_evidence_ref,
                "availability_evidence_ref": self.availability_evidence_ref,
                "price_raw_text": self.price_raw_text,
                "availability_status": self.availability_status,
                "authorized_source_ref": self.authorized_source_ref,
                "redacted_artifact_refs": self.redacted_artifact_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "content_hash_refs": self.content_hash_refs,
                "credential_audit_refs": self.credential_audit_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.blocked_source_refs:
                raise ValueError(f"passing official ecommerce API site missing refs: {missing}")
        elif not (self.failure_type and self.diagnostics and self.missing_ref_fields):
            raise ValueError("non-pass official ecommerce API site requires typed diagnostics")
        return self


class EcommerceOfficialApiBenchmarkReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    target_site_count: int
    site_result_refs: list[Ref] = Field(default_factory=list)
    passing_site_result_refs: list[Ref] = Field(default_factory=list)
    blocked_site_result_refs: list[Ref] = Field(default_factory=list)
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    authorized_source_refs: list[Ref] = Field(default_factory=list)
    redacted_artifact_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    credential_audit_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    source_fetch_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    failure_type: str | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> EcommerceOfficialApiBenchmarkReport:
        if self.target_site_count < 1:
            raise ValueError("official ecommerce API benchmark target count must be positive")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "site_result_refs": self.site_result_refs,
                "passing_site_result_refs": self.passing_site_result_refs,
                "field_evidence_refs": self.field_evidence_refs,
                "authorized_source_refs": self.authorized_source_refs,
                "redacted_artifact_refs": self.redacted_artifact_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "content_hash_refs": self.content_hash_refs,
                "credential_audit_refs": self.credential_audit_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
                "source_fetch_refs": self.source_fetch_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.blocked_site_result_refs or self.failure_type:
                raise ValueError(f"passing official ecommerce API report missing refs: {missing}")
        elif not self.diagnostics:
            raise ValueError("non-pass official ecommerce API report requires diagnostics")
        return self


class EcommerceOfficialApiBenchmarkManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    objective: str
    target_specs: list[EcommerceOfficialApiTargetSpec] = Field(default_factory=list)
    required_ref_types: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult = CompletenessResult.NEEDS_REVIEW
    expected_operator_status: str = "ecommerce_official_api_credentials_required"
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_manifest(self) -> EcommerceOfficialApiBenchmarkManifest:
        if "target" not in self.profile_refs:
            raise ValueError("official ecommerce API benchmark must support target profile")
        if not self.target_specs:
            raise ValueError("official ecommerce API benchmark requires targets")
        if not self.required_ref_types:
            raise ValueError("official ecommerce API benchmark requires ref types")
        return self
