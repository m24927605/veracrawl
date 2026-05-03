"""Graph and memory production runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphMemoryProductionFailureType,
)


class GraphMemoryProductionRuntimeReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    live_normalization_runtime_report_ref: Ref | None = None
    live_evidence_verification_runtime_report_ref: Ref | None = None
    multi_agent_repair_report_ref: Ref | None = None
    advanced_graph_projection_report_ref: Ref | None = None
    graph_frontier_review_runtime_report_ref: Ref | None = None
    temporal_kg_runtime_report_ref: Ref | None = None
    memory_kernel_report_ref: Ref | None = None
    url_graph_refs: list[Ref] = Field(default_factory=list)
    redirect_graph_refs: list[Ref] = Field(default_factory=list)
    canonical_graph_refs: list[Ref] = Field(default_factory=list)
    page_structure_graph_refs: list[Ref] = Field(default_factory=list)
    entity_graph_refs: list[Ref] = Field(default_factory=list)
    task_graph_refs: list[Ref] = Field(default_factory=list)
    temporal_graph_refs: list[Ref] = Field(default_factory=list)
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    site_memory_event_refs: list[Ref] = Field(default_factory=list)
    task_memory_event_refs: list[Ref] = Field(default_factory=list)
    repair_memory_event_refs: list[Ref] = Field(default_factory=list)
    run_diary_memory_event_refs: list[Ref] = Field(default_factory=list)
    memory_retrieval_trace_refs: list[Ref] = Field(default_factory=list)
    memory_write_refs: list[Ref] = Field(default_factory=list)
    memory_freshness_refs: list[Ref] = Field(default_factory=list)
    memory_invalidation_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    repair_explanation_refs: list[Ref] = Field(default_factory=list)
    operator_explanation_refs: list[Ref] = Field(default_factory=list)
    owner_command_refs: list[Ref] = Field(default_factory=list)
    review_escalation_refs: list[Ref] = Field(default_factory=list)
    source_evidence_refs: list[Ref] = Field(default_factory=list)
    verification_decision_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_type: GraphMemoryProductionFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    graph_as_evidence_refs: list[Ref] = Field(default_factory=list)
    memory_as_evidence_refs: list[Ref] = Field(default_factory=list)
    stale_memory_refs: list[Ref] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_graph_memory_production_report(
        self,
    ) -> GraphMemoryProductionRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "live_normalization_runtime_report_ref": (
                    self.live_normalization_runtime_report_ref
                ),
                "live_evidence_verification_runtime_report_ref": (
                    self.live_evidence_verification_runtime_report_ref
                ),
                "multi_agent_repair_report_ref": self.multi_agent_repair_report_ref,
                "advanced_graph_projection_report_ref": (
                    self.advanced_graph_projection_report_ref
                ),
                "graph_frontier_review_runtime_report_ref": (
                    self.graph_frontier_review_runtime_report_ref
                ),
                "temporal_kg_runtime_report_ref": self.temporal_kg_runtime_report_ref,
                "memory_kernel_report_ref": self.memory_kernel_report_ref,
                "url_graph_refs": self.url_graph_refs,
                "redirect_graph_refs": self.redirect_graph_refs,
                "canonical_graph_refs": self.canonical_graph_refs,
                "page_structure_graph_refs": self.page_structure_graph_refs,
                "entity_graph_refs": self.entity_graph_refs,
                "task_graph_refs": self.task_graph_refs,
                "temporal_graph_refs": self.temporal_graph_refs,
                "graph_signal_refs": self.graph_signal_refs,
                "projection_watermark_refs": self.projection_watermark_refs,
                "site_memory_event_refs": self.site_memory_event_refs,
                "task_memory_event_refs": self.task_memory_event_refs,
                "repair_memory_event_refs": self.repair_memory_event_refs,
                "run_diary_memory_event_refs": self.run_diary_memory_event_refs,
                "memory_retrieval_trace_refs": self.memory_retrieval_trace_refs,
                "memory_write_refs": self.memory_write_refs,
                "memory_freshness_refs": self.memory_freshness_refs,
                "memory_invalidation_refs": self.memory_invalidation_refs,
                "frontier_decision_refs": self.frontier_decision_refs,
                "repair_explanation_refs": self.repair_explanation_refs,
                "operator_explanation_refs": self.operator_explanation_refs,
                "owner_command_refs": self.owner_command_refs,
                "review_escalation_refs": self.review_escalation_refs,
                "source_evidence_refs": self.source_evidence_refs,
                "verification_decision_refs": self.verification_decision_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "privacy_lifecycle_refs": self.privacy_lifecycle_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
                or self.graph_as_evidence_refs
                or self.memory_as_evidence_refs
                or self.stale_memory_refs
            ):
                raise ValueError(
                    f"passing graph/memory production report missing refs: {missing}"
                )
        elif not (
            self.failure_type
            and (
                self.failure_report_refs
                or self.missing_ref_fields
                or self.graph_as_evidence_refs
                or self.memory_as_evidence_refs
                or self.stale_memory_refs
            )
        ):
            raise ValueError("non-pass graph/memory production report requires diagnostics")
        return self


class GraphMemoryProductionFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: GraphMemoryProductionFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph_memory_fixture(self) -> GraphMemoryProductionFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("graph/memory fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("graph/memory fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative graph/memory fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative graph/memory fixture requires failure type")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
