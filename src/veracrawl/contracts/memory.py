"""Memory kernel contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrossScopeTunnelStatus,
    MemoryEventStatus,
    MemoryPromptUse,
    MemoryTrustLevel,
    MemoryType,
)


class MemoryEvent(TimestampedModel):
    id: str
    run_ref: Ref
    scope_ref: Ref
    memory_type: MemoryType
    content_ref: Ref
    evidence_refs: list[Ref] = Field(default_factory=list)
    provenance_refs: list[Ref] = Field(default_factory=list)
    trust_level: MemoryTrustLevel
    taint_labels: list[str] = Field(default_factory=list)
    promotion_policy_ref: Ref
    poisoning_check_ref: Ref
    sanitized_context_ref: Ref | None = None
    allowed_prompt_use: MemoryPromptUse
    freshness_ref: Ref
    status: MemoryEventStatus
    invalidated_by_ref: Ref | None = None
    supersedes_memory_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_memory_event(self) -> MemoryEvent:
        if not self.scope_ref or not self.content_ref:
            raise ValueError("memory event requires scope and content refs")
        if not self.provenance_refs:
            raise ValueError("memory event requires provenance refs")
        if not self.promotion_policy_ref or not self.poisoning_check_ref or not self.freshness_ref:
            raise ValueError("memory event requires promotion, poisoning, and freshness refs")
        if not self.policy_decision_refs:
            raise ValueError("memory event requires policy refs")
        if self.allowed_prompt_use != MemoryPromptUse.FORBIDDEN and not self.sanitized_context_ref:
            raise ValueError("prompt-eligible memory requires sanitized context ref")
        if self.status == MemoryEventStatus.INVALIDATED and not self.invalidated_by_ref:
            raise ValueError("invalidated memory requires invalidation ref")
        if self.status == MemoryEventStatus.SUPERSEDED and not self.supersedes_memory_ref:
            raise ValueError("superseded memory requires replacement ref")
        return self


class MemoryRetrievalTrace(TimestampedModel):
    id: str
    run_ref: Ref
    query_ref: Ref
    scope_ref: Ref
    retrieved_memory_refs: list[Ref] = Field(default_factory=list)
    excluded_memory_refs: list[Ref] = Field(default_factory=list)
    exclusion_reasons: list[str] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    cross_scope_tunnel_ref: Ref | None = None
    taint_labels: list[str] = Field(default_factory=list)
    freshness_cutoff_ref: Ref
    retrieval_index_ref: Ref
    sanitized_context_ref: Ref | None = None
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_retrieval(self) -> MemoryRetrievalTrace:
        if not self.query_ref or not self.scope_ref:
            raise ValueError("memory retrieval requires query and scope refs")
        if not self.retrieved_memory_refs and not self.excluded_memory_refs:
            raise ValueError("memory retrieval requires retrieved or excluded refs")
        if self.excluded_memory_refs and not self.exclusion_reasons:
            raise ValueError("excluded memory refs require reasons")
        if not self.policy_decision_refs:
            raise ValueError("memory retrieval requires policy refs")
        if not self.freshness_cutoff_ref or not self.retrieval_index_ref:
            raise ValueError("memory retrieval requires freshness and index refs")
        if self.retrieved_memory_refs and not self.sanitized_context_ref:
            raise ValueError("retrieved memory requires sanitized context ref")
        return self


class CrossScopeMemoryTunnel(TimestampedModel):
    id: str
    source_scope_ref: Ref
    target_scope_ref: Ref
    allowed_memory_types: list[MemoryType] = Field(default_factory=list)
    authorization_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    sanitized_only: bool = True
    evidence_ref_required: bool = True
    taint_exclusion_rules: list[str] = Field(default_factory=list)
    status: CrossScopeTunnelStatus

    @model_validator(mode="after")
    def validate_tunnel(self) -> CrossScopeMemoryTunnel:
        if not self.source_scope_ref or not self.target_scope_ref:
            raise ValueError("cross-scope memory tunnel requires source and target scopes")
        if self.source_scope_ref == self.target_scope_ref:
            raise ValueError("cross-scope memory tunnel requires different scopes")
        if not self.allowed_memory_types:
            raise ValueError("cross-scope memory tunnel requires allowed memory types")
        if not self.policy_decision_refs:
            raise ValueError("cross-scope memory tunnel requires policy refs")
        if self.status == CrossScopeTunnelStatus.APPROVED:
            if not self.authorization_ref:
                raise ValueError("approved cross-scope memory tunnel requires authorization")
            if not self.sanitized_only or not self.evidence_ref_required:
                raise ValueError(
                    "approved cross-scope memory tunnel must be sanitized and anchored"
                )
        return self


class OperationalTemporalMemoryRecord(TimestampedModel):
    id: str
    run_ref: Ref
    scope_ref: Ref
    memory_type: MemoryType
    memory_event_refs: list[Ref] = Field(default_factory=list)
    valid_from_ref: Ref
    valid_to_ref: Ref | None = None
    evidence_refs: list[Ref] = Field(default_factory=list)
    status: MemoryEventStatus

    @model_validator(mode="after")
    def validate_operational_temporal_memory(self) -> OperationalTemporalMemoryRecord:
        if not self.scope_ref or not self.valid_from_ref:
            raise ValueError("operational temporal memory requires scope and valid-from refs")
        if not self.memory_event_refs:
            raise ValueError("operational temporal memory requires memory event refs")
        if not self.evidence_refs:
            raise ValueError("operational temporal memory requires evidence refs")
        return self


class MemoryKernelReport(TimestampedModel):
    id: str
    run_ref: Ref
    memory_event_refs: list[Ref] = Field(default_factory=list)
    retrieval_trace_ref: Ref | None = None
    tunnel_ref: Ref | None = None
    operational_record_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_memory_kernel_report(self) -> MemoryKernelReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "memory_event_refs": self.memory_event_refs,
                "retrieval_trace_ref": self.retrieval_trace_ref,
                "operational_record_refs": self.operational_record_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing memory kernel report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError("non-pass memory kernel report requires failures or missing refs")
        return self


class MemoryFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> MemoryFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("memory fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative memory fixture must not expect pass")
        return self
