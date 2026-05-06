from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.optimization.objective_evidence import (
    objective_evidence_summary,
    run_deterministic_objective_evidence,
)
from veracrawl.review_replay.crawler_optimization_objective_gate import (
    agent_decision_loop_replay_passes,
    objective_release_gate_replay_passes,
    objective_score_replay_passes,
)
from veracrawl.review_replay.crawler_optimization_owner_integration import (
    regression_release_gate_replay_passes,
)


def test_deterministic_objective_evidence_materializes_096_and_097_gates() -> None:
    run = run_deterministic_objective_evidence()

    assert len(run.lower_integrations) == 7
    assert run.regression_gate.completion_result == CompletenessResult.PASS
    assert run.objective_score.completion_result == CompletenessResult.PASS
    assert run.agent_decision_loop.completion_result == CompletenessResult.PASS
    assert run.objective_release_gate.completion_result == CompletenessResult.PASS
    assert regression_release_gate_replay_passes(run.regression_gate)
    assert objective_score_replay_passes(run.objective_score)
    assert agent_decision_loop_replay_passes(run.agent_decision_loop)
    assert objective_release_gate_replay_passes(run.objective_release_gate)


def test_deterministic_objective_evidence_summary_names_all_audit_refs() -> None:
    run = run_deterministic_objective_evidence()
    summary = objective_evidence_summary(run)

    assert summary["ok"] is True
    assert summary["lower_integration_count"] == 7
    assert summary["lower_regression_gate_ref"] == run.regression_gate.id
    assert summary["objective_score_ref"] == run.objective_score.id
    assert summary["agent_decision_loop_ref"] == run.agent_decision_loop.id
    assert summary["objective_release_gate_ref"] == run.objective_release_gate.id
    assert float(summary["optimization_score"]) >= float(summary["score_threshold"])
