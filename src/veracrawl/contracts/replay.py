"""Replay contract models."""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, ReplayMissingRefBehavior, ReplayMode


class ReplayBundleManifest(TimestampedModel):
    id: str
    run_id: str
    objective_id: str
    crawl_plan_id: str
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    event_schema_versions: list[str] = Field(default_factory=list)
    contract_schema_versions: list[str] = Field(default_factory=list)
    artifact_hash_refs: list[Ref] = Field(default_factory=list)
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    command_result_refs: list[Ref] = Field(default_factory=list)
    agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    model_call_trace_refs: list[Ref] = Field(default_factory=list)
    tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    projection_watermark_refs: list[Ref] = Field(default_factory=list)
    memory_retrieval_trace_refs: list[Ref] = Field(default_factory=list)
    graph_build_manifest_refs: list[Ref] = Field(default_factory=list)
    export_receipt_refs: list[Ref] = Field(default_factory=list)
    deterministic_clock_ref: Ref | None = None
    randomness_seed_ref: Ref | None = None
    redaction_map_ref: Ref | None = None
    missing_ref_behavior: ReplayMissingRefBehavior = ReplayMissingRefBehavior.FAIL_REPLAY
    replay_mode: ReplayMode = ReplayMode.STRUCTURAL
    completeness_result: CompletenessResult = CompletenessResult.NEEDS_REVIEW


class ReplayValidationReport(TimestampedModel):
    id: str
    manifest_id: str
    completeness_result: CompletenessResult
    missing_ref_fields: list[str] = Field(default_factory=list)
    gap_report_ref: Ref | None = None
