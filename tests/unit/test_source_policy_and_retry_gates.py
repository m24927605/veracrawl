from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.adapters.sources.deterministic import DeterministicSourceAdapter
from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    RateLimitDecisionValue,
    SourceFailureType,
)
from veracrawl.contracts.source_runtime import RateLimitDecision, SourceFailureReport
from veracrawl.fetch.acquisition import execute_source_acquisition


def _run(scenario: str) -> str:
    return f"source-{scenario}"


def test_source_blocked_produces_failure_report() -> None:
    outcome = execute_source_acquisition(
        fixture_id=_run("blocked"),
        adapter_type=AdapterType.HTTP,
        scenario="blocked",
        adapter=DeterministicSourceAdapter(adapter_type=AdapterType.HTTP),
    )
    assert outcome.report.completion_result == CompletenessResult.FAIL
    assert outcome.failure_report is not None
    assert outcome.failure_report.failure_type == SourceFailureType.SOURCE_BLOCKED


def test_rate_limit_decision_requires_retry_after() -> None:
    with pytest.raises(ValidationError):
        RateLimitDecision(
            id="rate-limit:bad",
            run_ref="run:bad",
            source_ref="source:bad",
            decision=RateLimitDecisionValue.RATE_LIMIT,
            rate_limit_policy_ref="policy:rate",
        )


def test_rate_limited_and_retry_exhausted_are_typed() -> None:
    rate_limited = execute_source_acquisition(
        fixture_id=_run("rate"),
        adapter_type=AdapterType.HTTP,
        scenario="rate-limited",
        adapter=DeterministicSourceAdapter(adapter_type=AdapterType.HTTP),
    )
    retry_exhausted = execute_source_acquisition(
        fixture_id=_run("retry"),
        adapter_type=AdapterType.HTTP,
        scenario="retry-exhausted",
        adapter=DeterministicSourceAdapter(adapter_type=AdapterType.HTTP),
    )
    assert rate_limited.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert rate_limited.rate_limit_decision is not None
    assert retry_exhausted.report.completion_result == CompletenessResult.FAIL
    assert retry_exhausted.failure_report is not None
    assert retry_exhausted.failure_report.failure_type == SourceFailureType.RETRY_EXHAUSTED


def test_failure_report_requires_diagnostics() -> None:
    with pytest.raises(ValidationError):
        SourceFailureReport(
            id="source-failure:bad",
            run_ref="run:bad",
            source_ref="source:bad",
            failure_type=SourceFailureType.MALFORMED_RESPONSE,
            operator_status="malformed_response",
        )
