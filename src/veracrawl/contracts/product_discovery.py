"""Query-driven product discovery contracts."""

from __future__ import annotations

import re
from ipaddress import ip_address
from urllib.parse import quote, quote_plus, urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductDiscoveryFailureType,
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


class ProductDiscoverySourceSpec(TimestampedModel):
    id: str
    site_name: str
    search_url: str
    robots_url: str
    allowed_origin: str
    query: str
    required_identity_terms: list[str] = Field(default_factory=list)
    rejected_identity_terms: list[str] = Field(default_factory=list)
    candidate_url_patterns: list[str] = Field(default_factory=list)
    exclude_url_patterns: list[str] = Field(default_factory=list)
    allowed_robots_status_codes: list[int] = Field(default_factory=lambda: [200])
    max_candidates: int = 10
    timeout_ms: int = 30000
    size_budget_bytes: int = 2_500_000
    expected_source_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_source_spec(self) -> ProductDiscoverySourceSpec:
        if not _is_http_url(self.search_url) or not _is_http_url(self.robots_url):
            raise ValueError("product discovery source URLs must be absolute http(s)")
        if _is_private_network_url(self.search_url) or _is_private_network_url(self.robots_url):
            raise ValueError("product discovery sources cannot use private networks")
        if self.allowed_origin != _origin(self.search_url):
            raise ValueError("allowed_origin must match search_url origin")
        if self.allowed_origin != _origin(self.robots_url):
            raise ValueError("robots_url must share search origin")
        if not self.query.strip():
            raise ValueError("product discovery source requires query text")
        if not self.required_identity_terms:
            raise ValueError("product discovery source requires identity terms")
        if not self.candidate_url_patterns:
            raise ValueError("product discovery source requires candidate URL patterns")
        if self.max_candidates < 1 or self.timeout_ms < 1 or self.size_budget_bytes < 1:
            raise ValueError("product discovery source budgets must be positive")
        if not self.allowed_robots_status_codes:
            raise ValueError("allowed robots status codes are required")
        for status_code in self.allowed_robots_status_codes:
            if status_code < 100 or status_code > 599:
                raise ValueError("allowed robots status codes must be valid HTTP")
        for pattern in self.candidate_url_patterns + self.exclude_url_patterns:
            re.compile(pattern)
        if not _url_contains_query_signal(self.search_url, self.query):
            raise ValueError("search_url must include the query or an encoded query signal")
        return self


class ProductDiscoveryCandidate(TimestampedModel):
    id: str
    fixture_id: str
    source_spec_ref: Ref
    site_name: str
    query: str
    search_url: str
    candidate_url: str
    candidate_rank: int
    raw_anchor_text: str
    matched_identity_terms: list[str] = Field(default_factory=list)
    source_anchor_ref: Ref
    artifact_ref: Ref
    content_hash_ref: Ref
    canonical_url_ref: Ref
    model_call_trace_ref: Ref
    agent_action_trace_ref: Ref
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref
    llm_output_evidence_refs: list[Ref] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_candidate(self) -> ProductDiscoveryCandidate:
        if self.candidate_rank < 1:
            raise ValueError("candidate rank must be positive")
        if not _is_http_url(self.candidate_url):
            raise ValueError("candidate_url must be absolute http(s)")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_spec_ref": self.source_spec_ref,
                "search_url": self.search_url,
                "candidate_url": self.candidate_url,
                "source_anchor_ref": self.source_anchor_ref,
                "artifact_ref": self.artifact_ref,
                "content_hash_ref": self.content_hash_ref,
                "canonical_url_ref": self.canonical_url_ref,
                "model_call_trace_ref": self.model_call_trace_ref,
                "agent_action_trace_ref": self.agent_action_trace_ref,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_ref": self.context_bundle_trace_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"passing product discovery candidate missing refs: {missing}")
            if self.llm_output_evidence_refs:
                raise ValueError("LLM output cannot be product discovery source evidence")
        return self


class ProductDiscoveryRunReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    query: str
    product_name: str
    source_count: int
    source_result_refs: list[Ref] = Field(default_factory=list)
    discovered_candidate_refs: list[Ref] = Field(default_factory=list)
    accepted_candidate_refs: list[Ref] = Field(default_factory=list)
    blocked_source_refs: list[Ref] = Field(default_factory=list)
    derived_product_availability_manifest_ref: Ref | None = None
    product_availability_report_ref: Ref | None = None
    offer_projection_report_ref: Ref | None = None
    ranked_offer_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: ProductDiscoveryFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_report(self) -> ProductDiscoveryRunReport:
        if self.source_count < 1:
            raise ValueError("product discovery report source_count must be positive")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "source_result_refs": self.source_result_refs,
                "discovered_candidate_refs": self.discovered_candidate_refs,
                "accepted_candidate_refs": self.accepted_candidate_refs,
                "derived_product_availability_manifest_ref": (
                    self.derived_product_availability_manifest_ref
                ),
                "product_availability_report_ref": self.product_availability_report_ref,
                "offer_projection_report_ref": self.offer_projection_report_ref,
                "ranked_offer_refs": self.ranked_offer_refs,
                "model_call_trace_refs": self.model_call_trace_refs,
                "agent_action_trace_refs": self.agent_action_trace_refs,
                "tool_call_trace_refs": self.tool_call_trace_refs,
                "context_bundle_trace_refs": self.context_bundle_trace_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing product discovery report missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.discovered_candidate_refs or self.blocked_source_refs):
                raise ValueError("needs-review discovery report requires refs")
            if not self.diagnostics:
                raise ValueError("needs-review discovery report requires diagnostics")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("failed product discovery report requires typed diagnostics")
        return self


class ProductDiscoveryBenchmarkManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    product_name: str
    brand: str
    query: str
    required_identity_terms: list[str] = Field(default_factory=list)
    rejected_identity_terms: list[str] = Field(default_factory=list)
    source_specs: list[ProductDiscoverySourceSpec] = Field(default_factory=list)
    max_total_candidates: int = 20
    ranking_limit: int = 10
    provider_names: list[str] = Field(default_factory=list)
    framework_names: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: ProductDiscoveryFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> ProductDiscoveryBenchmarkManifest:
        if "target" not in self.profile_refs:
            raise ValueError("product discovery benchmark must support target profile")
        if not self.product_name or not self.brand or not self.query.strip():
            raise ValueError("product discovery manifest requires product name, brand, and query")
        if not self.required_identity_terms:
            raise ValueError("product discovery manifest requires identity terms")
        if not self.source_specs:
            raise ValueError("product discovery manifest requires search/listing sources")
        if self.max_total_candidates < 1 or self.ranking_limit < 1:
            raise ValueError("product discovery candidate and ranking limits must be positive")
        if not self.required_ref_types:
            raise ValueError("product discovery manifest requires ref type declarations")
        for source in self.source_specs:
            if source.query != self.query:
                raise ValueError("source query must match manifest query")
        if self.negative_case and self.expected_completion_result == CompletenessResult.PASS:
            raise ValueError("negative product discovery fixture cannot expect pass")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative product discovery fixture requires failure type")
        return self


def _url_contains_query_signal(url: str, query: str) -> bool:
    folded_url = url.casefold()
    folded_query = query.strip().casefold()
    if folded_query in folded_url:
        return True
    quoted = quote(query.strip(), safe="").casefold()
    quoted_plus = quote_plus(query.strip()).casefold()
    compact = query.strip().replace(" ", "").casefold()
    return quoted in folded_url or quoted_plus in folded_url or compact in folded_url
