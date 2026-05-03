from __future__ import annotations

from veracrawl.ops.replay_observability_runtime import (
    run_ops_replay_observability_runtime,
)
from veracrawl.review_replay.ops_runtime import (
    missing_ops_replay_observability_refs,
    ops_replay_observability_replay_passes,
)


def test_ops_runtime_replay_passes_for_complete_report() -> None:
    result = run_ops_replay_observability_runtime(
        fixture_id="unit-ops-runtime-replay",
        scenario="ops-runtime-review-replay-success",
    )
    assert ops_replay_observability_replay_passes(result.report)
    assert not missing_ops_replay_observability_refs(result.report)


def test_ops_runtime_replay_reports_missing_bundle() -> None:
    result = run_ops_replay_observability_runtime(
        fixture_id="unit-ops-runtime-replay-gap",
        scenario="ops-runtime-replay-mismatch",
    )
    assert not ops_replay_observability_replay_passes(result.report)
    assert "replay_bundle_ref" in missing_ops_replay_observability_refs(result.report)


def test_ops_runtime_replay_rejects_operator_boundary_violations() -> None:
    for scenario in [
        "ops-runtime-stale-dashboard",
        "ops-runtime-unresolved-recovery",
        "ops-runtime-unsafe-operator-action",
    ]:
        result = run_ops_replay_observability_runtime(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
        )
        assert not ops_replay_observability_replay_passes(result.report)
