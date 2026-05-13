"""Model + tool call traces for the external crawl runtime.

Phase 5 records every LLM call and every tool invocation as a
structured trace so the run report can reconstruct what the
AI-assisted layer did. These records live alongside the frontier
events under ``events/`` in the run directory.

The trace shape is intentionally narrow: the goal doc forbids
LLM output from becoming source evidence on its own, so traces
capture the request/response, not the candidate fields. The
extractor adapter is what binds an LLM-asserted quote to a
normalised-text anchor; failure to match is a policy denial,
not a stored candidate.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator

from veracrawl.contracts.common import VeraModel


class ModelCallTrace(VeraModel):
    trace_id: str = Field(min_length=1)
    canonical_url: str = Field(min_length=1)
    provider_ref: str = Field(min_length=1)
    schema_ref: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=64, max_length=64)
    response_hash: str = Field(min_length=64, max_length=64)
    status: str  # "ok" | "refused" | "error"
    started_at: datetime
    completed_at: datetime
    elapsed_ms: float = Field(ge=0.0)

    @field_validator("started_at", "completed_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("trace timestamps must be UTC")
        return value.astimezone(UTC)


class ToolCallTrace(VeraModel):
    trace_id: str = Field(min_length=1)
    canonical_url: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments_hash: str = Field(min_length=64, max_length=64)
    result_hash: str = Field(min_length=64, max_length=64)
    status: str  # "ok" | "denied" | "error"
    started_at: datetime
    completed_at: datetime


__all__ = ["ModelCallTrace", "ToolCallTrace"]
