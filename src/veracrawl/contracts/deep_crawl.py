"""Multi-page deep crawl frontier benchmark contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    DeepCrawlFailureType,
    DeepCrawlFrontierAction,
    DeepCrawlPageType,
    DeepCrawlStopReason,
)


class DeepCrawlPageSpec(TimestampedModel):
    id: str
    url: str
    allowed_origin: str
    canonical_url: str
    page_type: DeepCrawlPageType
    depth: int
    link_urls: list[str] = Field(default_factory=list)
    required_for_coverage: bool = True
    robots_allowed: bool = True
    private_network: bool = False
    ai_prioritized: bool = False
    artifact_ref: Ref | None = None
    content_hash_ref: Ref | None = None
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    model_call_refs: list[Ref] = Field(default_factory=list)
    agent_action_refs: list[Ref] = Field(default_factory=list)
    tool_call_refs: list[Ref] = Field(default_factory=list)
    context_bundle_refs: list[Ref] = Field(default_factory=list)
    graph_frontier_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_page_spec(self) -> DeepCrawlPageSpec:
        for field_name, value in {
            "url": self.url,
            "allowed_origin": self.allowed_origin,
            "canonical_url": self.canonical_url,
        }.items():
            if not value.startswith(("http://", "https://")):
                raise ValueError(f"deep crawl {field_name} must be http or https")
        if self.depth < 0:
            raise ValueError("deep crawl page depth cannot be negative")
        if self.required_for_coverage and not (
            self.artifact_ref and self.content_hash_ref and self.source_anchor_refs
        ):
            raise ValueError("required deep crawl page requires source refs")
        if self.ai_prioritized and not (
            self.model_call_refs
            and self.agent_action_refs
            and self.tool_call_refs
            and self.context_bundle_refs
        ):
            raise ValueError("AI-prioritized page requires framework-neutral trace refs")
        return self


class DeepCrawlSiteSpec(TimestampedModel):
    id: str
    allowed_origin: str
    seed_urls: list[str] = Field(default_factory=list)
    page_specs: list[DeepCrawlPageSpec] = Field(default_factory=list)
    generated_page_count: int = 0
    max_depth: int = 4
    max_pages: int = 12
    expected_required_page_count: int = 0
    expected_page_type_refs: list[DeepCrawlPageType] = Field(default_factory=list)
    rate_budget_ref: Ref
    robots_policy_ref: Ref
    private_network_policy_ref: Ref

    @model_validator(mode="after")
    def validate_site_spec(self) -> DeepCrawlSiteSpec:
        if not self.allowed_origin.startswith(("http://", "https://")):
            raise ValueError("deep crawl allowed_origin must be http or https")
        if self.max_depth < 1 or self.max_pages < 1:
            raise ValueError("deep crawl site budgets must be positive")
        if not self.page_specs and self.generated_page_count < 1:
            raise ValueError("deep crawl site requires page specs or generated pages")
        if self.generated_page_count and self.generated_page_count < 10:
            raise ValueError("generated deep crawl sites require at least 10 pages")
        if self.page_specs and not self.seed_urls:
            raise ValueError("explicit deep crawl sites require seed urls")
        if self.expected_required_page_count < 0:
            raise ValueError("expected page count cannot be negative")
        return self


class FrontierDecisionTrace(TimestampedModel):
    id: str
    site_ref: Ref
    target_url: str
    canonical_url: str | None = None
    source_page_ref: Ref | None = None
    depth: int
    action: DeepCrawlFrontierAction
    reason: str
    ai_prioritized: bool = False
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_refs: list[Ref] = Field(default_factory=list)
    skipped_link_refs: list[Ref] = Field(default_factory=list)
    graph_frontier_refs: list[Ref] = Field(default_factory=list)
    memory_refs: list[Ref] = Field(default_factory=list)
    model_call_refs: list[Ref] = Field(default_factory=list)
    agent_action_refs: list[Ref] = Field(default_factory=list)
    tool_call_refs: list[Ref] = Field(default_factory=list)
    context_bundle_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: DeepCrawlFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_decision(self) -> FrontierDecisionTrace:
        if self.depth < 0:
            raise ValueError("frontier decision depth cannot be negative")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            if self.action != DeepCrawlFrontierAction.STOP:
                required["link_provenance_or_anchor_refs"] = (
                    self.link_provenance_refs
                    or self.source_anchor_refs
                    or self.graph_frontier_refs
                )
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing frontier decision missing refs: {missing}")
            if self.ai_prioritized and not (
                self.model_call_refs
                and self.agent_action_refs
                and self.tool_call_refs
                and self.context_bundle_refs
            ):
                raise ValueError("AI-prioritized frontier decision missing trace refs")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass frontier decision requires diagnostics")
        return self


class DeepCrawlPageObservation(TimestampedModel):
    id: str
    site_ref: Ref
    page_spec_ref: Ref
    url: str
    canonical_url: str
    page_type: DeepCrawlPageType
    depth: int
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_refs: list[Ref] = Field(default_factory=list)
    graph_page_refs: list[Ref] = Field(default_factory=list)
    graph_frontier_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: DeepCrawlFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_observation(self) -> DeepCrawlPageObservation:
        if self.depth < 0:
            raise ValueError("deep crawl observation depth cannot be negative")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "link_provenance_refs": self.link_provenance_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "graph_page_refs": self.graph_page_refs,
                "graph_frontier_refs": self.graph_frontier_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing deep crawl observation missing refs: {missing}")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass deep crawl observation requires diagnostics")
        return self


class DeepCrawlStopReasonRecord(TimestampedModel):
    id: str
    site_ref: Ref
    reason: DeepCrawlStopReason
    frontier_remaining_count: int
    page_count: int
    max_depth: int
    max_pages: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    diagnostics: list[str] = Field(default_factory=list)
    completion_result: CompletenessResult = CompletenessResult.PASS

    @model_validator(mode="after")
    def validate_stop_reason(self) -> DeepCrawlStopReasonRecord:
        if self.frontier_remaining_count < 0 or self.page_count < 0:
            raise ValueError("deep crawl stop reason counts cannot be negative")
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"passing deep crawl stop reason missing refs: {missing}")
        return self


class DeepCrawlQualityReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    site_count: int = 0
    required_page_count: int = 0
    covered_page_count: int = 0
    observed_page_count: int = 0
    frontier_decision_count: int = 0
    skipped_link_count: int = 0
    duplicate_suppressed_count: int = 0
    off_origin_skip_count: int = 0
    robots_denied_skip_count: int = 0
    private_network_skip_count: int = 0
    stop_reason_count: int = 0
    minimum_site_count: int = 5
    minimum_required_page_count: int = 50
    observation_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    stop_reason_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    link_provenance_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    duplicate_suppression_refs: list[Ref] = Field(default_factory=list)
    graph_refs: list[Ref] = Field(default_factory=list)
    ai_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: DeepCrawlFailureType | None = None
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> DeepCrawlQualityReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "observation_refs": self.observation_refs,
                "frontier_decision_refs": self.frontier_decision_refs,
                "stop_reason_refs": self.stop_reason_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "source_anchor_refs": self.source_anchor_refs,
                "link_provenance_refs": self.link_provenance_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "duplicate_suppression_refs": self.duplicate_suppression_refs,
                "graph_refs": self.graph_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_refs": self.replay_bundle_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.failure_type or self.failure_report_refs:
                raise ValueError(f"passing deep crawl report missing refs: {missing}")
            if self.site_count < self.minimum_site_count:
                raise ValueError("passing deep crawl report below site minimum")
            if self.covered_page_count < self.minimum_required_page_count:
                raise ValueError("passing deep crawl report below page minimum")
            if self.covered_page_count != self.required_page_count:
                raise ValueError("passing deep crawl report has page coverage gap")
            if self.stop_reason_count < self.site_count:
                raise ValueError("passing deep crawl report missing stop reasons")
        elif not (
            self.failure_type
            and (self.failure_report_refs or self.missing_ref_fields)
            and self.diagnostics
        ):
            raise ValueError("non-pass deep crawl report requires diagnostics")
        return self


class DeepCrawlQualityManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    site_specs: list[DeepCrawlSiteSpec] = Field(default_factory=list)
    minimum_site_count: int = 5
    minimum_required_page_count: int = 50
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: DeepCrawlFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_manifest(self) -> DeepCrawlQualityManifest:
        if "quality" not in self.profile_refs:
            raise ValueError("deep crawl manifest must support quality profile")
        if not self.site_specs:
            raise ValueError("deep crawl manifest requires site specs")
        if self.minimum_site_count < 1 or self.minimum_required_page_count < 1:
            raise ValueError("deep crawl minimum thresholds must be positive")
        if not self.required_ref_types:
            raise ValueError("deep crawl manifest requires ref type declarations")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative deep crawl fixture cannot expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative deep crawl fixture requires failure type")
        elif self.expected_completion_result != CompletenessResult.PASS:
            raise ValueError("positive deep crawl fixture must expect pass")
        return self
