"""Contract tests for ``ModelCallTrace`` + ``ToolCallTrace``."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from veracrawl.external_crawl.traces import ModelCallTrace, ToolCallTrace


def _ts(seconds: int = 0) -> datetime:
    return datetime(2026, 5, 13, 9, 0, seconds, tzinfo=UTC)


def test_model_call_trace_valid_minimal() -> None:
    trace = ModelCallTrace(
        trace_id="trace:1",
        canonical_url="https://example.com/",
        provider_ref="stub",
        schema_ref="schema:demo",
        prompt_hash="a" * 64,
        response_hash="b" * 64,
        status="ok",
        started_at=_ts(0),
        completed_at=_ts(1),
        elapsed_ms=1000.0,
    )
    assert trace.status == "ok"


def test_model_call_trace_requires_64_char_hashes() -> None:
    with pytest.raises(ValidationError):
        ModelCallTrace(
            trace_id="trace:1",
            canonical_url="https://example.com/",
            provider_ref="stub",
            schema_ref="schema:demo",
            prompt_hash="short",
            response_hash="b" * 64,
            status="ok",
            started_at=_ts(0),
            completed_at=_ts(1),
            elapsed_ms=1.0,
        )


def test_model_call_trace_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="UTC"):
        ModelCallTrace(
            trace_id="trace:1",
            canonical_url="https://example.com/",
            provider_ref="stub",
            schema_ref="schema:demo",
            prompt_hash="a" * 64,
            response_hash="b" * 64,
            status="ok",
            started_at=datetime(2026, 5, 13, 9, 0, 0),  # naive
            completed_at=_ts(1),
            elapsed_ms=1.0,
        )


def test_tool_call_trace_valid_minimal() -> None:
    trace = ToolCallTrace(
        trace_id="trace:t1",
        canonical_url="https://example.com/",
        tool_name="search.knowledge",
        arguments_hash="c" * 64,
        result_hash="d" * 64,
        status="ok",
        started_at=_ts(0),
        completed_at=_ts(1),
    )
    assert trace.tool_name == "search.knowledge"
