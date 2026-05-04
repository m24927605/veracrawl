"""Product price and availability benchmark contracts."""

from __future__ import annotations

import re
from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductAvailabilityFailureType,
    ProductAvailabilityStatus,
)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _origin(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_private_network_url(value: str) -> bool:
    host = urlparse(value).hostname
    if host is None:
        return True
    if host == "localhost":
        return True
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    )


class ProductAvailabilityTargetSpec(TimestampedModel):
    id: str
    site_name: str
    target_url: str
    robots_url: str
    allowed_origin: str
    expected_status_code: int = 200
    expected_content_type: str = "text/html"
    required_identity_terms: list[str] = Field(default_factory=list)
    rejected_identity_terms: list[str] = Field(default_factory=list)
    allowed_robots_status_codes: list[int] = Field(default_factory=lambda: [200])
    timeout_ms: int = 30000
    size_budget_bytes: int = 2_500_000
    expected_site_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_target_spec(self) -> ProductAvailabilityTargetSpec:
        if not _is_http_url(self.target_url) or not _is_http_url(self.robots_url):
            raise ValueError("product availability target URLs must be absolute http(s)")
        if _is_private_network_url(self.target_url) or _is_private_network_url(self.robots_url):
            raise ValueError("product availability targets cannot use private networks")
        if self.allowed_origin != _origin(self.target_url):
            raise ValueError("allowed_origin must match target_url origin")
        if self.allowed_origin != _origin(self.robots_url):
            raise ValueError("robots_url must share target origin")
        if not self.required_identity_terms:
            raise ValueError("product target requires identity terms")
        if self.expected_status_code < 100 or self.expected_status_code > 599:
            raise ValueError("expected_status_code must be valid HTTP")
        if not self.expected_content_type:
            raise ValueError("expected_content_type is required")
        if not self.allowed_robots_status_codes:
            raise ValueError("allowed_robots_status_codes is required")
        for status_code in self.allowed_robots_status_codes:
            if status_code < 100 or status_code > 599:
                raise ValueError("allowed robots status codes must be valid HTTP")
        if self.timeout_ms < 1 or self.size_budget_bytes < 1:
            raise ValueError("product availability budgets must be positive")
        return self


class ProductAvailabilityFieldEvidence(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    target_url: str
    field_name: str
    raw_text: str
    normalized_value: str
    amount: float | None = None
    currency: str | None = None
    source_anchor_ref: Ref
    artifact_ref: Ref
    content_hash_ref: Ref
    canonical_url_ref: Ref
    model_call_trace_ref: Ref
    agent_action_trace_ref: Ref
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_ref: Ref
    evidence_packet_ref: Ref
    evidence_anchor_ref: Ref
    verification_decision_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_field_evidence(self) -> ProductAvailabilityFieldEvidence:
        if self.field_name not in {
            "identity",
            "price",
            "availability",
            "delivery_eta",
            "shipping_fee",
        }:
            raise ValueError("unsupported product availability field")
        if self.completion_result != CompletenessResult.PASS:
            raise ValueError("field evidence rows must be passing source-backed rows")
        required: dict[str, object] = {
            "raw_text": self.raw_text,
            "normalized_value": self.normalized_value,
            "source_anchor_ref": self.source_anchor_ref,
            "artifact_ref": self.artifact_ref,
            "content_hash_ref": self.content_hash_ref,
            "canonical_url_ref": self.canonical_url_ref,
            "model_call_trace_ref": self.model_call_trace_ref,
            "agent_action_trace_ref": self.agent_action_trace_ref,
            "tool_call_trace_refs": self.tool_call_trace_refs,
            "context_bundle_trace_ref": self.context_bundle_trace_ref,
            "evidence_packet_ref": self.evidence_packet_ref,
            "evidence_anchor_ref": self.evidence_anchor_ref,
            "verification_decision_ref": self.verification_decision_ref,
            "policy_decision_refs": self.policy_decision_refs,
            "command_record_refs": self.command_record_refs,
            "event_cursor_refs": self.event_cursor_refs,
            "outbox_refs": self.outbox_refs,
            "replay_bundle_ref": self.replay_bundle_ref,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"field evidence missing refs: {missing}")
        if self.field_name in {"price", "shipping_fee"} and (
            self.amount is None or not self.currency
        ):
            raise ValueError("price evidence requires amount and currency")
        if self.field_name == "availability":
            ProductAvailabilityStatus(self.normalized_value)
        if self.llm_output_evidence_refs:
            raise ValueError("LLM output cannot be product field source evidence")
        return self


class ProductAvailabilitySiteResult(TimestampedModel):
    id: str
    fixture_id: str
    target_spec_ref: Ref
    site_name: str
    target_url: str
    live_http_report_ref: Ref | None = None
    network_response_ref: Ref | None = None
    status_code: int | None = None
    content_type: str | None = None
    body_size_bytes: int | None = None
    content_digest: str | None = None
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    identity_terms_matched: list[str] = Field(default_factory=list)
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    identity_evidence_ref: Ref | None = None
    price_evidence_ref: Ref | None = None
    availability_evidence_ref: Ref | None = None
    price_raw_text: str | None = None
    price_amount: float | None = None
    price_currency: str | None = None
    availability_status: ProductAvailabilityStatus | None = None
    availability_raw_text: str | None = None
    delivery_evidence_ref: Ref | None = None
    delivery_eta_raw_text: str | None = None
    delivery_eta_min_days: int | None = None
    delivery_eta_max_days: int | None = None
    shipping_fee_evidence_ref: Ref | None = None
    shipping_fee_raw_text: str | None = None
    shipping_fee_amount: float | None = None
    shipping_fee_currency: str | None = None
    total_price_amount: float | None = None
    total_price_currency: str | None = None
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    publication_gate_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ProductAvailabilityFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_site_result(self) -> ProductAvailabilitySiteResult:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_http_report_ref": self.live_http_report_ref,
                "network_response_ref": self.network_response_ref,
                "status_code": self.status_code,
                "content_type": self.content_type,
                "body_size_bytes": self.body_size_bytes,
                "content_digest": self.content_digest,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "identity_terms_matched": self.identity_terms_matched,
                "field_evidence_refs": self.field_evidence_refs,
                "identity_evidence_ref": self.identity_evidence_ref,
                "price_evidence_ref": self.price_evidence_ref,
                "availability_evidence_ref": self.availability_evidence_ref,
                "price_raw_text": self.price_raw_text,
                "availability_status": self.availability_status,
                "model_call_trace_refs": self.model_call_trace_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "publication_gate_refs": self.publication_gate_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing product site result missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass product site result requires typed diagnostics")
        return self


class ProductAvailabilityBenchmarkReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    product_name: str
    target_site_count: int
    site_result_refs: list[Ref] = Field(default_factory=list)
    passing_site_result_refs: list[Ref] = Field(default_factory=list)
    blocked_site_result_refs: list[Ref] = Field(default_factory=list)
    field_evidence_refs: list[Ref] = Field(default_factory=list)
    price_evidence_refs: list[Ref] = Field(default_factory=list)
    availability_evidence_refs: list[Ref] = Field(default_factory=list)
    delivery_evidence_refs: list[Ref] = Field(default_factory=list)
    shipping_fee_evidence_refs: list[Ref] = Field(default_factory=list)
    offer_projection_report_ref: Ref | None = None
    offer_record_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ProductAvailabilityFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self) -> ProductAvailabilityBenchmarkReport:
        if self.target_site_count < 1:
            raise ValueError("target_site_count must be positive")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "site_result_refs": self.site_result_refs,
                "passing_site_result_refs": self.passing_site_result_refs,
                "field_evidence_refs": self.field_evidence_refs,
                "price_evidence_refs": self.price_evidence_refs,
                "availability_evidence_refs": self.availability_evidence_refs,
                "model_call_trace_refs": self.model_call_trace_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "evidence_packet_refs": self.evidence_packet_refs,
                "evidence_anchor_refs": self.evidence_anchor_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type
                or self.failure_report_refs
                or self.blocked_site_result_refs
            ):
                raise ValueError(f"passing product report missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not self.passing_site_result_refs or not self.blocked_site_result_refs:
                raise ValueError("needs-review product report requires pass and blocked refs")
            if not self.diagnostics:
                raise ValueError("needs-review product report requires diagnostics")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("failed product report requires typed diagnostics")
        return self


class ProductAvailabilityBenchmarkManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    product_name: str
    brand: str
    required_identity_terms: list[str] = Field(default_factory=list)
    rejected_identity_terms: list[str] = Field(default_factory=list)
    target_specs: list[ProductAvailabilityTargetSpec] = Field(default_factory=list)
    provider_names: list[str] = Field(default_factory=list)
    framework_names: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ProductAvailabilityFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> ProductAvailabilityBenchmarkManifest:
        if "target" not in self.profile_refs:
            raise ValueError("product availability benchmark must support target profile")
        if not self.product_name or not self.brand:
            raise ValueError("product name and brand are required")
        if not self.required_identity_terms:
            raise ValueError("manifest requires identity terms")
        if not self.target_specs:
            raise ValueError("manifest requires product targets")
        if not self.required_ref_types:
            raise ValueError("manifest requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative product availability fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative fixture requires failure type")
        for pattern in self.rejected_identity_terms:
            re.compile(re.escape(pattern))
        return self
