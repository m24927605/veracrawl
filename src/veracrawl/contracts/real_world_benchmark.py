"""Real-world benchmark corpus contracts."""

from __future__ import annotations

import re
from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldBenchmarkFailureType,
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


class RealWorldBenchmarkSiteSpec(TimestampedModel):
    id: str
    target_url: str
    robots_url: str
    allowed_origin: str
    expected_status_code: int
    expected_content_type: str
    min_body_size_bytes: int
    required_title_fragments: list[str] = Field(default_factory=list)
    required_body_fragments: list[str] = Field(default_factory=list)
    required_regex_counts: dict[str, int] = Field(default_factory=dict)
    allowed_robots_status_codes: list[int] = Field(default_factory=lambda: [200])
    timeout_ms: int = 10000
    size_budget_bytes: int = 65536
    pattern_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_site_spec(self) -> RealWorldBenchmarkSiteSpec:
        if not _is_http_url(self.target_url) or not _is_http_url(self.robots_url):
            raise ValueError("real-world benchmark URLs must be absolute http(s)")
        if _is_private_network_url(self.target_url) or _is_private_network_url(
            self.robots_url
        ):
            raise ValueError("real-world benchmark URLs cannot target private networks")
        if self.allowed_origin != _origin(self.target_url):
            raise ValueError("site allowed_origin must match target_url origin")
        if self.allowed_origin != _origin(self.robots_url):
            raise ValueError("robots_url must share the allowed origin")
        if self.expected_status_code < 100 or self.expected_status_code > 599:
            raise ValueError("expected_status_code must be a valid HTTP status")
        if not self.expected_content_type:
            raise ValueError("expected_content_type is required")
        if self.min_body_size_bytes < 1:
            raise ValueError("min_body_size_bytes must be positive")
        if self.timeout_ms < 1 or self.size_budget_bytes < 1:
            raise ValueError("real-world benchmark budgets must be positive")
        if not self.allowed_robots_status_codes:
            raise ValueError("allowed_robots_status_codes is required")
        for status_code in self.allowed_robots_status_codes:
            if status_code < 100 or status_code > 599:
                raise ValueError("allowed robots status codes must be valid HTTP")
        for pattern, minimum in self.required_regex_counts.items():
            if minimum < 1:
                raise ValueError("required regex counts must be positive")
            re.compile(pattern)
        if not (
            self.required_title_fragments
            or self.required_body_fragments
            or self.required_regex_counts
        ):
            raise ValueError("site spec requires at least one content observation")
        if not self.pattern_refs:
            raise ValueError("site spec requires target pattern refs")
        return self


class RealWorldBenchmarkSiteObservation(TimestampedModel):
    id: str
    site_spec_ref: Ref
    target_url: str
    robots_policy_ref: Ref | None = None
    live_http_report_ref: Ref | None = None
    network_response_ref: Ref | None = None
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    status_code: int | None = None
    content_type: str | None = None
    body_size_bytes: int | None = None
    content_digest: str | None = None
    matched_observation_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldBenchmarkFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_observation(self) -> RealWorldBenchmarkSiteObservation:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "robots_policy_ref": self.robots_policy_ref,
                "live_http_report_ref": self.live_http_report_ref,
                "network_response_ref": self.network_response_ref,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
                "status_code": self.status_code,
                "content_type": self.content_type,
                "body_size_bytes": self.body_size_bytes,
                "content_digest": self.content_digest,
                "matched_observation_refs": self.matched_observation_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing real-world site observation missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass real-world observation requires typed diagnostics")
        return self


class RealWorldBenchmarkRunReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    benchmark_corpus_ref: Ref | None = None
    benchmark_run_refs: list[Ref] = Field(default_factory=list)
    site_observation_refs: list[Ref] = Field(default_factory=list)
    live_http_report_refs: list[Ref] = Field(default_factory=list)
    network_response_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    observation_summary_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: RealWorldBenchmarkFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_run_report(self) -> RealWorldBenchmarkRunReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "benchmark_corpus_ref": self.benchmark_corpus_ref,
                "benchmark_run_refs": self.benchmark_run_refs,
                "site_observation_refs": self.site_observation_refs,
                "live_http_report_refs": self.live_http_report_refs,
                "network_response_refs": self.network_response_refs,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
                "observation_summary_refs": self.observation_summary_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing real-world benchmark report missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass real-world benchmark report requires diagnostics")
        return self


class RealWorldBenchmarkCorpusManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    site_specs: list[RealWorldBenchmarkSiteSpec] = Field(default_factory=list)
    allowed_origin_refs: list[Ref] = Field(default_factory=list)
    rate_budget_ref: Ref
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: RealWorldBenchmarkFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> RealWorldBenchmarkCorpusManifest:
        if "target" not in self.profile_refs:
            raise ValueError("real-world benchmark corpus must support target profile")
        if not self.site_specs:
            raise ValueError("real-world benchmark corpus requires site specs")
        if not self.allowed_origin_refs:
            raise ValueError("real-world benchmark corpus requires allowed origins")
        allowed = set(self.allowed_origin_refs)
        missing_origins = [
            site.allowed_origin for site in self.site_specs if site.allowed_origin not in allowed
        ]
        if missing_origins:
            raise ValueError(f"site origins missing from corpus allowlist: {missing_origins}")
        if not self.required_ref_types:
            raise ValueError("real-world benchmark corpus requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative real-world corpus cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative real-world corpus requires failure type")
        return self
