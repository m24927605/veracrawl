"""Graph and graph projection contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    GraphEdgeType,
    GraphFrontierDecisionType,
    GraphFrontierReviewFailureType,
    GraphNodeType,
    GraphReviewRouteType,
    GraphSignalType,
    ProjectionJobStatus,
    ReviewPriority,
)


class GraphNode(TimestampedModel):
    id: str
    run_ref: Ref
    node_key: str
    node_type: GraphNodeType
    label: str
    source_ref: Ref
    property_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_node(self) -> GraphNode:
        if not self.node_key or not self.label:
            raise ValueError("graph node requires key and label")
        return self


class GraphEdge(TimestampedModel):
    id: str
    run_ref: Ref
    from_node_ref: Ref
    to_node_ref: Ref
    edge_type: GraphEdgeType
    provenance_ref: Ref
    property_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_edge(self) -> GraphEdge:
        if self.from_node_ref == self.to_node_ref and self.edge_type == GraphEdgeType.HYPERLINK:
            raise ValueError("hyperlink edge cannot self-link")
        if not self.provenance_ref:
            raise ValueError("graph edge requires provenance")
        return self


class GraphEdgeProvenance(TimestampedModel):
    id: str
    edge_ref: Ref
    input_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    evidence_ref_allowed: bool = False

    @model_validator(mode="after")
    def validate_provenance(self) -> GraphEdgeProvenance:
        if not self.input_refs:
            raise ValueError("graph edge provenance requires input refs")
        if not self.policy_decision_refs:
            raise ValueError("graph edge provenance requires policy refs")
        return self


class ProjectionWatermark(TimestampedModel):
    id: str
    projection_ref: Ref
    input_manifest_ref: Ref
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    rebuild_hash: str
    freshness_ref: Ref

    @model_validator(mode="after")
    def validate_watermark(self) -> ProjectionWatermark:
        if not self.event_cursor_refs:
            raise ValueError("projection watermark requires event cursors")
        if not self.rebuild_hash:
            raise ValueError("projection watermark requires rebuild hash")
        return self


class ProjectionSpec(TimestampedModel):
    id: str
    run_ref: Ref
    projection_name: str
    input_manifest_refs: list[Ref] = Field(default_factory=list)
    graph_version: str
    rebuild_policy_ref: Ref
    owner_service_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_projection_spec(self) -> ProjectionSpec:
        if not self.projection_name or not self.graph_version:
            raise ValueError("projection spec requires name and graph version")
        if not self.input_manifest_refs:
            raise ValueError("projection spec requires input manifests")
        if not self.rebuild_policy_ref or not self.owner_service_ref:
            raise ValueError("projection spec requires rebuild policy and owner refs")
        if not self.policy_decision_refs:
            raise ValueError("projection spec requires policy refs")
        return self


class ProjectionRebuildJob(TimestampedModel):
    id: str
    run_ref: Ref
    projection_spec_ref: Ref
    input_manifest_refs: list[Ref] = Field(default_factory=list)
    expected_rebuild_hash: str
    actual_rebuild_hash: str
    watermark_ref: Ref | None = None
    status: ProjectionJobStatus
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rebuild_job(self) -> ProjectionRebuildJob:
        if not self.projection_spec_ref or not self.input_manifest_refs:
            raise ValueError("projection rebuild job requires projection and input refs")
        if not self.expected_rebuild_hash or not self.actual_rebuild_hash:
            raise ValueError("projection rebuild job requires expected and actual hashes")
        if self.status == ProjectionJobStatus.REBUILT:
            if self.expected_rebuild_hash != self.actual_rebuild_hash:
                raise ValueError("rebuilt projection job hash mismatch")
            if not self.watermark_ref:
                raise ValueError("rebuilt projection job requires watermark")
        if self.status == ProjectionJobStatus.MISMATCH and (
            self.expected_rebuild_hash == self.actual_rebuild_hash
        ):
            raise ValueError("mismatch projection job requires different hashes")
        if not self.policy_decision_refs:
            raise ValueError("projection rebuild job requires policy refs")
        return self


class ProjectionMismatchReport(TimestampedModel):
    id: str
    run_ref: Ref
    projection_rebuild_job_ref: Ref
    expected_rebuild_hash: str
    actual_rebuild_hash: str
    mismatch_ref: Ref
    operator_status: str

    @model_validator(mode="after")
    def validate_mismatch(self) -> ProjectionMismatchReport:
        if self.expected_rebuild_hash == self.actual_rebuild_hash:
            raise ValueError("projection mismatch report requires differing hashes")
        if not self.mismatch_ref or not self.operator_status:
            raise ValueError("projection mismatch report requires mismatch and status refs")
        return self


class GraphSignal(TimestampedModel):
    id: str
    run_ref: Ref
    signal_type: GraphSignalType
    subject_ref: Ref
    score: float = Field(ge=0.0, le=1.0)
    source_graph_refs: list[Ref] = Field(default_factory=list)
    explanation_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    evidence_ref_allowed: bool = False

    @model_validator(mode="after")
    def validate_signal(self) -> GraphSignal:
        if not self.subject_ref or not self.explanation_ref:
            raise ValueError("graph signal requires subject and explanation refs")
        if not self.source_graph_refs:
            raise ValueError("graph signal requires source graph refs")
        if not self.policy_decision_refs:
            raise ValueError("graph signal requires policy refs")
        if self.evidence_ref_allowed:
            raise ValueError("graph signals cannot satisfy source evidence requirements")
        return self


_SUPPORTED_FRONTIER_SIGNAL_TYPES = {
    GraphSignalType.FRONTIER_PRIORITY,
    GraphSignalType.DEDUP_HINT,
    GraphSignalType.DRIFT_RISK,
}

_SUPPORTED_REVIEW_SIGNAL_TYPES = {
    GraphSignalType.REVIEW_ROUTE,
    GraphSignalType.DRIFT_RISK,
    GraphSignalType.QUALITY_WARNING,
}


class GraphFrontierDecisionRecord(TimestampedModel):
    id: str
    run_ref: Ref
    graph_signal_ref: Ref
    signal_type: GraphSignalType
    decision_type: GraphFrontierDecisionType
    frontier_item_ref: Ref
    before_priority: int
    after_priority: int
    generated_frontier_item_refs: list[Ref] = Field(default_factory=list)
    retry_frontier_item_refs: list[Ref] = Field(default_factory=list)
    retired_frontier_item_refs: list[Ref] = Field(default_factory=list)
    source_graph_refs: list[Ref] = Field(default_factory=list)
    explanation_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    evidence_ref_allowed: bool = False
    unauthorized_mutation_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_frontier_decision(self) -> GraphFrontierDecisionRecord:
        if self.evidence_ref_allowed:
            raise ValueError("graph frontier decision cannot satisfy evidence")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "graph_signal_ref": self.graph_signal_ref,
                "frontier_item_ref": self.frontier_item_ref,
                "source_graph_refs": self.source_graph_refs,
                "explanation_ref": self.explanation_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            if self.signal_type not in _SUPPORTED_FRONTIER_SIGNAL_TYPES:
                raise ValueError("unsupported graph signal for frontier decision")
            if self.decision_type == GraphFrontierDecisionType.PRIORITIZE:
                if self.after_priority == self.before_priority:
                    raise ValueError("prioritize decision must change priority")
            if self.decision_type == GraphFrontierDecisionType.EXPAND:
                required["generated_frontier_item_refs"] = self.generated_frontier_item_refs
            if self.decision_type == GraphFrontierDecisionType.RETRY:
                required["retry_frontier_item_refs"] = self.retry_frontier_item_refs
            if self.decision_type == GraphFrontierDecisionType.RETIRE:
                required["retired_frontier_item_refs"] = self.retired_frontier_item_refs
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing graph frontier decision missing refs: {missing}")
            if self.unauthorized_mutation_refs:
                raise ValueError("passing graph frontier decision has unauthorized mutation refs")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not self.missing_ref_fields:
                raise ValueError("needs-review graph frontier decision requires missing refs")
        elif not (self.unauthorized_mutation_refs or self.missing_ref_fields):
            raise ValueError("failed graph frontier decision requires failure details")
        return self


class GraphReviewRouteDecisionRecord(TimestampedModel):
    id: str
    run_ref: Ref
    graph_signal_ref: Ref
    signal_type: GraphSignalType
    route_type: GraphReviewRouteType
    review_item_ref: Ref
    review_priority: ReviewPriority
    source_graph_refs: list[Ref] = Field(default_factory=list)
    explanation_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    evidence_ref_allowed: bool = False
    missing_ref_fields: list[str] = Field(default_factory=list)
    result: CompletenessResult

    @model_validator(mode="after")
    def validate_review_route_decision(self) -> GraphReviewRouteDecisionRecord:
        if self.evidence_ref_allowed:
            raise ValueError("graph review route decision cannot satisfy evidence")
        if self.result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "graph_signal_ref": self.graph_signal_ref,
                "review_item_ref": self.review_item_ref,
                "source_graph_refs": self.source_graph_refs,
                "explanation_ref": self.explanation_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            if self.signal_type not in _SUPPORTED_REVIEW_SIGNAL_TYPES:
                raise ValueError("unsupported graph signal for review route decision")
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing graph review route missing refs: {missing}")
        elif self.result == CompletenessResult.NEEDS_REVIEW:
            if not self.missing_ref_fields:
                raise ValueError("needs-review graph review route requires missing refs")
        elif not self.missing_ref_fields:
            raise ValueError("failed graph review route requires failure details")
        return self


class GraphFrontierReviewRuntimeReport(TimestampedModel):
    id: str
    run_ref: Ref
    graph_signal_refs: list[Ref] = Field(default_factory=list)
    frontier_decision_refs: list[Ref] = Field(default_factory=list)
    review_route_decision_refs: list[Ref] = Field(default_factory=list)
    frontier_item_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    source_graph_refs: list[Ref] = Field(default_factory=list)
    explanation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    graph_signal_as_evidence_refs: list[Ref] = Field(default_factory=list)
    missing_source_graph_refs: list[Ref] = Field(default_factory=list)
    missing_explanation_refs: list[Ref] = Field(default_factory=list)
    unauthorized_frontier_mutation_refs: list[Ref] = Field(default_factory=list)
    missing_review_route_refs: list[Ref] = Field(default_factory=list)
    unsupported_signal_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_frontier_review_report(self) -> GraphFrontierReviewRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "graph_signal_refs": self.graph_signal_refs,
                "frontier_decision_refs": self.frontier_decision_refs,
                "review_route_decision_refs": self.review_route_decision_refs,
                "frontier_item_refs": self.frontier_item_refs,
                "review_item_refs": self.review_item_refs,
                "source_graph_refs": self.source_graph_refs,
                "explanation_refs": self.explanation_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.contract_only_refs
                or self.missing_runtime_refs
                or self.graph_signal_as_evidence_refs
                or self.missing_source_graph_refs
                or self.missing_explanation_refs
                or self.unauthorized_frontier_mutation_refs
                or self.missing_review_route_refs
                or self.unsupported_signal_refs
                or self.missing_ref_fields
            ):
                raise ValueError(f"passing graph frontier/review report missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_runtime_refs):
                raise ValueError("needs-review graph frontier/review report requires review refs")
        elif not (
            self.graph_signal_as_evidence_refs
            or self.missing_source_graph_refs
            or self.missing_explanation_refs
            or self.unauthorized_frontier_mutation_refs
            or self.missing_review_route_refs
            or self.unsupported_signal_refs
            or self.missing_ref_fields
        ):
            raise ValueError("failed graph frontier/review report requires failure details")
        return self


class GraphFrontierReviewFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: GraphFrontierReviewFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_frontier_review_fixture(self) -> GraphFrontierReviewFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("graph frontier/review fixture must support target profile")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative graph frontier/review fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self


class GraphDeltaReport(TimestampedModel):
    id: str
    run_ref: Ref
    previous_manifest_ref: Ref
    current_manifest_ref: Ref
    added_node_refs: list[Ref] = Field(default_factory=list)
    removed_node_refs: list[Ref] = Field(default_factory=list)
    added_edge_refs: list[Ref] = Field(default_factory=list)
    removed_edge_refs: list[Ref] = Field(default_factory=list)
    changed_signal_refs: list[Ref] = Field(default_factory=list)
    rebuild_hash: str

    @model_validator(mode="after")
    def validate_delta(self) -> GraphDeltaReport:
        if not self.previous_manifest_ref or not self.current_manifest_ref:
            raise ValueError("graph delta report requires previous and current manifests")
        if not self.rebuild_hash:
            raise ValueError("graph delta report requires rebuild hash")
        return self


class GraphQualityReport(TimestampedModel):
    id: str
    run_ref: Ref
    graph_manifest_ref: Ref
    metric_refs: list[Ref] = Field(default_factory=list)
    score_refs: list[Ref] = Field(default_factory=list)
    warning_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_quality(self) -> GraphQualityReport:
        if not self.graph_manifest_ref:
            raise ValueError("graph quality report requires graph manifest")
        if not self.metric_refs or not self.score_refs:
            raise ValueError("graph quality report requires metric and score refs")
        if not self.policy_decision_refs:
            raise ValueError("graph quality report requires policy refs")
        return self


class TemporalGraphProjectionRecord(TimestampedModel):
    id: str
    run_ref: Ref
    source_output_refs: list[Ref] = Field(default_factory=list)
    valid_from_ref: Ref
    valid_to_ref: Ref | None = None
    entity_identity_ref: Ref
    evidence_packet_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_ref: Ref

    @model_validator(mode="after")
    def validate_temporal_record(self) -> TemporalGraphProjectionRecord:
        if not self.source_output_refs:
            raise ValueError("temporal graph record requires source output refs")
        if not self.evidence_packet_refs:
            raise ValueError("temporal graph record requires evidence packet refs")
        required = [self.valid_from_ref, self.entity_identity_ref, self.projection_watermark_ref]
        if not all(required):
            raise ValueError(
                "temporal graph record requires validity, identity, and watermark refs"
            )
        return self


class GraphBuildManifest(TimestampedModel):
    id: str
    run_ref: Ref
    input_refs: list[Ref] = Field(default_factory=list)
    graph_version: str
    node_refs: list[Ref] = Field(default_factory=list)
    edge_refs: list[Ref] = Field(default_factory=list)
    provenance_refs: list[Ref] = Field(default_factory=list)
    watermark_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    rebuild_hash: str

    @model_validator(mode="after")
    def validate_manifest(self) -> GraphBuildManifest:
        if not self.input_refs:
            raise ValueError("graph build manifest requires input refs")
        if not self.node_refs or not self.edge_refs or not self.provenance_refs:
            raise ValueError("graph build manifest requires graph refs")
        if not self.policy_decision_refs:
            raise ValueError("graph build manifest requires policy refs")
        if not self.rebuild_hash:
            raise ValueError("graph build manifest requires rebuild hash")
        return self


class GraphBuildReport(TimestampedModel):
    id: str
    run_ref: Ref
    manifest_ref: Ref | None = None
    node_refs: list[Ref] = Field(default_factory=list)
    edge_refs: list[Ref] = Field(default_factory=list)
    provenance_refs: list[Ref] = Field(default_factory=list)
    watermark_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> GraphBuildReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "manifest_ref": self.manifest_ref,
                "node_refs": self.node_refs,
                "edge_refs": self.edge_refs,
                "provenance_refs": self.provenance_refs,
                "watermark_ref": self.watermark_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing graph report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError("non-pass graph report requires failures or missing refs")
        return self


class AdvancedGraphProjectionReport(TimestampedModel):
    id: str
    run_ref: Ref
    projection_spec_ref: Ref | None = None
    rebuild_job_ref: Ref | None = None
    delta_report_ref: Ref | None = None
    quality_report_ref: Ref | None = None
    signal_refs: list[Ref] = Field(default_factory=list)
    temporal_record_refs: list[Ref] = Field(default_factory=list)
    mismatch_report_ref: Ref | None = None
    watermark_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_projection_report(self) -> AdvancedGraphProjectionReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "projection_spec_ref": self.projection_spec_ref,
                "rebuild_job_ref": self.rebuild_job_ref,
                "delta_report_ref": self.delta_report_ref,
                "quality_report_ref": self.quality_report_ref,
                "signal_refs": self.signal_refs,
                "temporal_record_refs": self.temporal_record_refs,
                "watermark_ref": self.watermark_ref,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(
                    f"passing advanced graph projection report missing refs: {missing}"
                )
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields or self.mismatch_report_ref
        ):
            raise ValueError(
                "non-pass advanced graph projection report requires failures or missing refs"
            )
        return self


class GraphFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> GraphFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("graph fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative graph fixture must not expect pass")
        return self


class AdvancedGraphFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> AdvancedGraphFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("advanced graph fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative advanced graph fixture must not expect pass")
        return self
