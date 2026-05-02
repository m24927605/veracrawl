"""Basic site graph contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, GraphEdgeType, GraphNodeType


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
