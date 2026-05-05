from __future__ import annotations

import pytest

from veracrawl.contracts.crawler_optimization import (
    RuntimeFrontierOptimizationDecision,
    RuntimeOptimizationAggregate,
    RuntimeOptimizationSignalSet,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


def test_runtime_signal_set_requires_block_reason_for_denied_candidate() -> None:
    signal = RuntimeOptimizationSignalSet(
        id="runtime-signal:1",
        fixture_id="runtime-optimization-policy-blocked-url",
        run_ref="run:1",
        objective_ref="objective:1",
        candidate_url="https://example.com/private",
        policy_decision_refs=["policy:deny"],
        allowed=False,
        blocked_reason_refs=["robots:denied"],
    )

    assert not signal.allowed

    with pytest.raises(ValueError, match="blocked_reason_refs"):
        RuntimeOptimizationSignalSet(
            id="runtime-signal:bad",
            fixture_id="runtime-optimization-policy-blocked-url",
            run_ref="run:1",
            objective_ref="objective:1",
            candidate_url="https://example.com/private",
            policy_decision_refs=["policy:deny"],
            allowed=False,
        )


def test_runtime_frontier_enqueue_requires_score_and_priority() -> None:
    with pytest.raises(ValueError, match="requires score ref"):
        RuntimeFrontierOptimizationDecision(
            id="runtime-frontier:bad",
            fixture_id="runtime-optimization-wiring-success",
            signal_set_ref="runtime-signal:1",
            candidate_url="https://example.com/list",
            scheduler_action="enqueue",
            scheduler_priority=0,
            policy_decision_refs=["policy:allow"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_ref="replay:1",
        )


def test_runtime_aggregate_requires_typed_failure_when_non_pass() -> None:
    aggregate = RuntimeOptimizationAggregate(
        id="runtime-aggregate:fail",
        fixture_id="runtime-optimization-missing-replay",
        failure_report_refs=["failure:missing-replay"],
        missing_ref_fields=["replay_bundle_refs"],
        failure_type=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
        diagnostics=["missing replay refs"],
        completion_result=CompletenessResult.FAIL,
    )

    assert aggregate.failure_type == CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
