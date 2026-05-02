"""Deterministic fixture and oracle contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import ComparisonMode, CompletenessResult, ReplayMissingRefBehavior


class BenchmarkFixtureManifest(TimestampedModel):
    id: str
    name: str
    profile_refs: list[Ref] = Field(default_factory=list)
    scenario: str
    source_server_ref: Ref | None = None
    seed_urls: list[str] = Field(default_factory=list)
    source_adapter_refs: list[Ref] = Field(default_factory=list)
    auth_fixture_ref: Ref | None = None
    oracles: dict[str, str] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)


class ThresholdSpec(TimestampedModel):
    id: str
    comparison_mode: ComparisonMode = ComparisonMode.EXACT
    numeric_abs: float | None = None
    numeric_pct: float | None = None
    timestamp_seconds: int | None = None
    text_normalization: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tolerance(self) -> ThresholdSpec:
        if self.comparison_mode == ComparisonMode.TOLERANCE:
            if (
                self.numeric_abs is None
                and self.numeric_pct is None
                and self.timestamp_seconds is None
            ):
                raise ValueError("tolerance comparison requires explicit threshold values")
        return self


class ExpectedOutputOracle(TimestampedModel):
    id: str
    fixture_id: str
    expected_output_type: str
    expected_items: list[dict[str, object]] = Field(default_factory=list)
    required_field_coverage: list[dict[str, object]] = Field(default_factory=list)
    required_evidence_level: str
    allowed_optional_misses: list[str] = Field(default_factory=list)
    forbidden_outputs: list[str] = Field(default_factory=list)
    comparison_mode: ComparisonMode = ComparisonMode.EXACT


class ExpectedEvidenceCoverageOracle(TimestampedModel):
    id: str
    fixture_id: str
    required_anchor_refs: list[Ref] = Field(default_factory=list)
    required_artifact_refs: list[Ref] = Field(default_factory=list)
    privacy_classification_expectations: dict[str, str] = Field(default_factory=dict)
    required_verification_refs: list[Ref] = Field(default_factory=list)
    missing_evidence_behavior: CompletenessResult = CompletenessResult.FAIL


class ExpectedEventSequenceOracle(TimestampedModel):
    id: str
    fixture_id: str
    required_event_types: list[str] = Field(default_factory=list)
    forbidden_event_types: list[str] = Field(default_factory=list)
    ordering_constraints: list[dict[str, object]] = Field(default_factory=list)
    required_payloads: list[dict[str, object]] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    replay_required_event_types: list[str] = Field(default_factory=list)


class ExpectedGraphOracle(TimestampedModel):
    id: str
    fixture_id: str
    expected_nodes: list[dict[str, object]] = Field(default_factory=list)
    expected_edges: list[dict[str, object]] = Field(default_factory=list)
    forbidden_edges: list[dict[str, object]] = Field(default_factory=list)
    expected_projection_watermarks: list[Ref] = Field(default_factory=list)
    false_merge_cases: list[dict[str, object]] = Field(default_factory=list)
    false_split_cases: list[dict[str, object]] = Field(default_factory=list)


class FailureInjectionPlan(TimestampedModel):
    id: str
    fixture_id: str
    injected_failures: list[dict[str, object]] = Field(default_factory=list)
    expected_failure_records: list[Ref] = Field(default_factory=list)
    expected_recovery_actions: list[Ref] = Field(default_factory=list)
    expected_dead_letters: list[Ref] = Field(default_factory=list)
    expected_events: list[str] = Field(default_factory=list)
    expected_operator_visible_status: str


class DRRestoreOracle(TimestampedModel):
    id: str
    fixture_id: str
    required_restore_phase_refs: list[Ref] = Field(default_factory=list)
    required_backup_manifest_refs: list[Ref] = Field(default_factory=list)
    required_validation_gate_refs: list[Ref] = Field(default_factory=list)
    expected_report_status: CompletenessResult
    unresolved_ref_behavior: ReplayMissingRefBehavior


class ReplayBundleOracle(TimestampedModel):
    id: str
    fixture_id: str
    required_event_cursor_refs: list[Ref] = Field(default_factory=list)
    required_artifact_hash_refs: list[Ref] = Field(default_factory=list)
    required_source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    required_command_result_refs: list[Ref] = Field(default_factory=list)
    required_agent_action_trace_refs: list[Ref] = Field(default_factory=list)
    required_model_call_trace_refs: list[Ref] = Field(default_factory=list)
    required_tool_call_trace_refs: list[Ref] = Field(default_factory=list)
    required_context_bundle_trace_refs: list[Ref] = Field(default_factory=list)
    required_policy_decision_refs: list[Ref] = Field(default_factory=list)
    expected_missing_ref_behavior: ReplayMissingRefBehavior
    expected_completeness_result: CompletenessResult
