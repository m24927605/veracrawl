from __future__ import annotations

from pathlib import Path

from tests.helpers.worker_orchestration_fixture_assertions import (
    assert_worker_orchestration_negative,
    assert_worker_orchestration_success,
)
from veracrawl.cli.worker_orchestration import run_fixture
from veracrawl.contracts.enums import WorkerOrchestrationFailureType


def test_worker_orchestration_success_fixtures(tmp_path: Path) -> None:
    expectations = {
        "worker-orchestration-production-success": "worker_orchestration_completed",
        "worker-orchestration-worker-crash-recovered": (
            "worker_orchestration_worker_crash_recovered"
        ),
        "worker-orchestration-backpressure-autoscale-success": (
            "worker_orchestration_backpressure_autoscale_completed"
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_worker_orchestration_success(report, operator_status=operator_status)


def test_worker_orchestration_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "worker-orchestration-missing-persistence": (
            WorkerOrchestrationFailureType.MISSING_PERSISTENCE
        ),
        "worker-orchestration-missing-queue-broker": (
            WorkerOrchestrationFailureType.MISSING_QUEUE_BROKER
        ),
        "worker-orchestration-stale-lease-unrecovered": (
            WorkerOrchestrationFailureType.STALE_LEASE_UNRECOVERED
        ),
        "worker-orchestration-missing-heartbeat": (
            WorkerOrchestrationFailureType.MISSING_HEARTBEAT
        ),
        "worker-orchestration-dead-letter-hidden": (
            WorkerOrchestrationFailureType.DEAD_LETTER_HIDDEN
        ),
        "worker-orchestration-duplicate-pollution": (
            WorkerOrchestrationFailureType.DUPLICATE_POLLUTION
        ),
        "worker-orchestration-backpressure-without-policy": (
            WorkerOrchestrationFailureType.BACKPRESSURE_WITHOUT_POLICY
        ),
        "worker-orchestration-replay-mismatch": (
            WorkerOrchestrationFailureType.REPLAY_MISMATCH
        ),
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, failure in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_worker_orchestration_negative(
            report,
            operator_status=failure.value,
            failure_type=failure.value,
        )
