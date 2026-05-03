from __future__ import annotations

from veracrawl.review_replay.worker_orchestration import (
    missing_worker_orchestration_replay_refs,
    worker_orchestration_replay_passes,
)
from veracrawl.scale.worker_orchestration import run_worker_orchestration_runtime


def test_worker_orchestration_replay_passes_for_complete_report() -> None:
    result = run_worker_orchestration_runtime(
        fixture_id="unit-worker-orchestration-replay",
        scenario="worker-orchestration-production-success",
    )
    assert worker_orchestration_replay_passes(result.report)
    assert not missing_worker_orchestration_replay_refs(result.report)


def test_worker_orchestration_replay_reports_missing_bundle() -> None:
    result = run_worker_orchestration_runtime(
        fixture_id="unit-worker-orchestration-missing-replay",
        scenario="worker-orchestration-replay-mismatch",
    )
    assert not worker_orchestration_replay_passes(result.report)
    assert "replay_bundle_ref" in missing_worker_orchestration_replay_refs(result.report)


def test_worker_orchestration_replay_rejects_hidden_failure_boundaries() -> None:
    for scenario in [
        "worker-orchestration-stale-lease-unrecovered",
        "worker-orchestration-dead-letter-hidden",
        "worker-orchestration-duplicate-pollution",
    ]:
        result = run_worker_orchestration_runtime(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
        )
        assert not worker_orchestration_replay_passes(result.report)
