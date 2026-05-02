"""Event contract models."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import OwnerService


class EventCursor(TimestampedModel):
    id: str
    run_id: str
    from_sequence: int
    to_sequence: int

    @model_validator(mode="after")
    def validate_range(self) -> EventCursor:
        if self.to_sequence < self.from_sequence:
            raise ValueError("event cursor to_sequence must be >= from_sequence")
        return self


class EventTypeSpec(TimestampedModel):
    id: str
    event_type: str
    event_version: str = "1.0"
    payload_schema_ref: Ref
    owner_service: OwnerService
    state_before_required: bool = False
    state_after_required: bool = False
    replay_critical_refs: list[str] = Field(default_factory=list)
    redaction_policy: str = "stable_ref"


class CrawlRunEvent(TimestampedModel):
    id: str
    run_id: str
    objective_id: str
    crawl_plan_id: str
    event_version: str = "1.0"
    sequence: int
    event_type: str
    event_type_spec_id: str
    payload_ref: Ref
    actor: str = "system"
    agent_id: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    prompt_ref: Ref | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    tool_input_schema_ref: Ref | None = None
    tool_output_schema_ref: Ref | None = None
    input_refs: list[Ref] = Field(default_factory=list)
    output_refs: list[Ref] = Field(default_factory=list)
    decision: str | None = None
    reason: str | None = None
    confidence: float | None = None
    state_before: dict[str, object] | None = None
    state_after: dict[str, object] | None = None
    causation_id: str
    correlation_id: str
    trace_id: str
    run_plan_snapshot_id: Ref | None = None
    policy_snapshot_id: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    memory_snapshot_refs: list[Ref] = Field(default_factory=list)
    graph_snapshot_refs: list[Ref] = Field(default_factory=list)
    idempotency_key: str
    error: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_sequence(self) -> CrawlRunEvent:
        if self.sequence < 1:
            raise ValueError("event sequence must be >= 1")
        return self
