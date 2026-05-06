from __future__ import annotations

from tests.unit.test_crawler_optimization_objective_gate import _lower_gate, _metric
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.optimization.objective_gate import (
    build_agent_decision_loop_evidence,
    build_optimization_objective_score,
    build_optimization_objective_score_from_metric,
    optimization_objective_release_gate,
)
from veracrawl.review_replay.crawler_optimization_objective_gate import (
    agent_decision_loop_replay_passes,
    missing_agent_decision_loop_replay_refs,
    missing_objective_release_gate_replay_refs,
    missing_objective_score_replay_refs,
    objective_release_gate_replay_passes,
    objective_score_replay_passes,
)


def test_objective_score_replay_requires_policy_command_event_outbox_and_replay() -> None:
    passing = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    missing = build_optimization_objective_score(
        fixture_id="optimization-objective-missing-replay",
        run_ref="run:objective",
        profile_ref="profile:optimization",
        extraction_accuracy=0.98,
        intent_match_precision=0.96,
        crawl_success_rate=0.97,
        dedupe_quality=0.98,
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        command_record_refs=[],
        event_cursor_refs=[],
        outbox_refs=[],
        replay_bundle_ref="",
    )

    assert objective_score_replay_passes(passing)
    assert not objective_score_replay_passes(missing)
    assert missing_objective_score_replay_refs(missing) == [
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "replay_bundle_ref",
    ]


def test_agent_decision_loop_replay_requires_all_phases_and_stop_condition() -> None:
    passing = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        confidence=0.91,
    )
    missing = build_agent_decision_loop_evidence(
        fixture_id="agent-decision-missing-stop",
        run_ref="run:objective",
        objective_score_ref="optimization-objective-score:success",
        confidence=0.91,
        stop_condition_ref="",
    )

    assert agent_decision_loop_replay_passes(passing)
    assert not agent_decision_loop_replay_passes(missing)
    assert "stop_condition_ref" in missing_agent_decision_loop_replay_refs(missing)


def test_objective_release_gate_replay_requires_lower_scores_agent_and_refs() -> None:
    score = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    loop = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref=score.id,
        confidence=0.91,
    )
    passing = optimization_objective_release_gate(
        fixture_id="optimization-objective-gate-success",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[_lower_gate()],
        objective_scores=[score],
        agent_decision_loops=[loop],
    )
    missing = optimization_objective_release_gate(
        fixture_id="objective-release-missing-lower-gate",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[],
        objective_scores=[score],
        agent_decision_loops=[loop],
        command_record_refs=[],
    )

    assert objective_release_gate_replay_passes(passing)
    assert not objective_release_gate_replay_passes(missing)
    missing_refs = missing_objective_release_gate_replay_refs(missing)
    assert "optimization-regression-release-gate:objective-release-missing-lower-gate" in (
        missing_refs
    )
    assert "command_record_refs" in missing_refs


def test_failed_lower_gate_blocks_release_replay_pass() -> None:
    score = build_optimization_objective_score_from_metric(
        metric=_metric(),
        run_ref="run:objective",
        profile_ref="profile:optimization",
        freshness=0.91,
        normalized_latency=0.25,
        normalized_cost=0.20,
        algorithm_recommendation_refs=["algorithm:objective"],
    )
    loop = build_agent_decision_loop_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref="run:objective",
        objective_score_ref=score.id,
        confidence=0.91,
    )
    gate = optimization_objective_release_gate(
        fixture_id="objective-release-failed-lower-gate",
        claim_scope_ref="claim:objective-fixture",
        lower_regression_gates=[_lower_gate(completion_result=CompletenessResult.FAIL)],
        objective_scores=[score],
        agent_decision_loops=[loop],
    )

    assert gate.failed_lower_gate_refs
    assert not objective_release_gate_replay_passes(gate)
