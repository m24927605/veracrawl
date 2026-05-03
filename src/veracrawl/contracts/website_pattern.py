"""Website pattern coverage contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetWebsitePattern,
    WebsitePatternCoverageFailureType,
)

TARGET_WEBSITE_PATTERNS: frozenset[TargetWebsitePattern] = frozenset(
    TargetWebsitePattern
)

_REQUIRED_PATTERN_SPECIFIC_REFS: dict[TargetWebsitePattern, frozenset[str]] = {
    TargetWebsitePattern.STATIC: frozenset(
        {"linked_page_refs", "schema_bound_output_refs"}
    ),
    TargetWebsitePattern.SITEMAP_RSS_FEED: frozenset(
        {"sitemap_or_feed_ref", "feed_delta_ref", "freshness_window_ref"}
    ),
    TargetWebsitePattern.LISTING_DETAIL: frozenset(
        {
            "listing_page_refs",
            "detail_page_refs",
            "pagination_refs",
            "canonical_dedup_refs",
        }
    ),
    TargetWebsitePattern.SEARCH: frozenset(
        {"bounded_query_refs", "search_result_page_refs", "budget_policy_ref"}
    ),
    TargetWebsitePattern.NON_DESTRUCTIVE_FORMS: frozenset(
        {"form_intent_ref", "non_destructive_policy_ref", "sandbox_ref"}
    ),
    TargetWebsitePattern.JAVASCRIPT_PAGES: frozenset(
        {"browser_artifact_refs", "dom_state_refs", "render_budget_ref"}
    ),
    TargetWebsitePattern.AUTHENTICATED_SOURCES: frozenset(
        {"credential_audit_refs", "origin_allowlist_ref", "redaction_ref"}
    ),
    TargetWebsitePattern.API_LIKE_ENDPOINTS: frozenset(
        {"api_payload_refs", "endpoint_provenance_refs", "schema_probe_refs"}
    ),
    TargetWebsitePattern.DOCUMENTS: frozenset(
        {"document_artifact_refs", "anchor_map_refs", "document_metadata_refs"}
    ),
    TargetWebsitePattern.MULTI_LANGUAGE_PAGES: frozenset(
        {"language_metadata_refs", "localized_field_refs"}
    ),
    TargetWebsitePattern.DRIFTED_SITES: frozenset(
        {"drift_event_refs", "repair_signal_refs", "review_decision_refs"}
    ),
    TargetWebsitePattern.HIGH_VOLUME_SITES: frozenset(
        {"queue_fairness_refs", "backpressure_refs", "retry_dedup_refs"}
    ),
}


class WebsitePatternCoverageRecord(TimestampedModel):
    id: str
    run_ref: Ref
    website_pattern: TargetWebsitePattern
    benchmark_fixture_ref: Ref | None = None
    source_adapter_refs: list[Ref] = Field(default_factory=list)
    source_evidence_refs: list[Ref] = Field(default_factory=list)
    site_model_refs: list[Ref] = Field(default_factory=list)
    page_type_refs: list[Ref] = Field(default_factory=list)
    expected_output_oracle_refs: list[Ref] = Field(default_factory=list)
    evidence_coverage_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    artifact_oracle_refs: list[Ref] = Field(default_factory=list)
    event_oracle_refs: list[Ref] = Field(default_factory=list)
    graph_oracle_refs: list[Ref] = Field(default_factory=list)
    pattern_specific_refs: dict[str, Ref] = Field(default_factory=dict)
    safety_refs: list[Ref] = Field(default_factory=list)
    diagnostic_single_site_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    unsupported_pattern_refs: list[Ref] = Field(default_factory=list)
    unsafe_interaction_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_pattern_coverage(self) -> WebsitePatternCoverageRecord:
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "benchmark_fixture_ref": self.benchmark_fixture_ref,
                "source_adapter_refs": self.source_adapter_refs,
                "source_evidence_refs": self.source_evidence_refs,
                "site_model_refs": self.site_model_refs,
                "page_type_refs": self.page_type_refs,
                "expected_output_oracle_refs": self.expected_output_oracle_refs,
                "evidence_coverage_refs": self.evidence_coverage_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "artifact_oracle_refs": self.artifact_oracle_refs,
                "event_oracle_refs": self.event_oracle_refs,
                "graph_oracle_refs": self.graph_oracle_refs,
                "safety_refs": self.safety_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            required_pattern_refs = _REQUIRED_PATTERN_SPECIFIC_REFS[
                self.website_pattern
            ]
            missing.extend(
                sorted(
                    ref_name
                    for ref_name in required_pattern_refs
                    if ref_name not in self.pattern_specific_refs
                )
            )
            if (
                missing
                or self.diagnostic_single_site_refs
                or self.scaffold_only_refs
                or self.unsupported_pattern_refs
                or self.unsafe_interaction_refs
                or self.missing_ref_fields
            ):
                raise ValueError(
                    f"passing website pattern coverage missing refs: {missing}"
                )
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not self.missing_ref_fields:
                raise ValueError("needs-review website pattern requires missing refs")
        elif not (
            self.diagnostic_single_site_refs
            or self.scaffold_only_refs
            or self.unsupported_pattern_refs
            or self.unsafe_interaction_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed website pattern coverage requires failure details")
        return self


class WebsitePatternCoverageReport(TimestampedModel):
    id: str
    run_ref: Ref
    coverage_record_refs: list[Ref] = Field(default_factory=list)
    covered_patterns: list[TargetWebsitePattern] = Field(default_factory=list)
    missing_patterns: list[TargetWebsitePattern] = Field(default_factory=list)
    unsupported_pattern_refs: list[Ref] = Field(default_factory=list)
    single_site_assumption_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    unsafe_interaction_refs: list[Ref] = Field(default_factory=list)
    missing_pattern_specific_refs: list[Ref] = Field(default_factory=list)
    missing_replay_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    failure_type: WebsitePatternCoverageFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_pattern_report(self) -> WebsitePatternCoverageReport:
        if self.completion_result == CompletenessResult.PASS:
            covered = set(self.covered_patterns)
            required: dict[str, object] = {
                "coverage_record_refs": self.coverage_record_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or covered != TARGET_WEBSITE_PATTERNS
                or self.missing_patterns
                or self.unsupported_pattern_refs
                or self.single_site_assumption_refs
                or self.scaffold_only_refs
                or self.unsafe_interaction_refs
                or self.missing_pattern_specific_refs
                or self.missing_replay_refs
                or self.missing_ref_fields
                or self.failure_type is not None
            ):
                raise ValueError(
                    f"passing website pattern report missing refs: {missing}"
                )
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review website pattern report requires refs")
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_patterns
                or self.unsupported_pattern_refs
                or self.single_site_assumption_refs
                or self.scaffold_only_refs
                or self.unsafe_interaction_refs
                or self.missing_pattern_specific_refs
                or self.missing_replay_refs
                or self.missing_ref_fields
            )
        ):
            raise ValueError("failed website pattern report requires failure details")
        return self


class WebsitePatternCoverageFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: WebsitePatternCoverageFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_website_pattern_fixture(self) -> WebsitePatternCoverageFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("website pattern fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative website pattern fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
