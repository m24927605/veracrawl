from __future__ import annotations

from pathlib import Path

from tests.helpers.ops_replay_observability_fixture_assertions import (
    assert_ops_runtime_negative,
    assert_ops_runtime_success,
)
from veracrawl.cli.ops_runtime import run_fixture
from veracrawl.contracts.enums import OpsReplayObservabilityFailureType


def test_ops_runtime_success_fixtures(tmp_path: Path) -> None:
    expectations = {
        "ops-runtime-review-replay-success": "ops_replay_observability_completed",
        "ops-runtime-incident-recovery-success": (
            "ops_replay_observability_incident_recovered"
        ),
        "ops-runtime-cost-alert-success": "ops_replay_observability_cost_alert_completed",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            telemetry_backend_ref="telemetry-backend:test",
            collector_handoff_ref="collector-handoff:test",
            out=tmp_path / fixture_id,
        )
        assert_ops_runtime_success(report, operator_status=operator_status)


def test_ops_runtime_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "ops-runtime-missing-publication": (
            OpsReplayObservabilityFailureType.MISSING_PUBLICATION
        ),
        "ops-runtime-missing-worker-orchestration": (
            OpsReplayObservabilityFailureType.MISSING_WORKER_ORCHESTRATION
        ),
        "ops-runtime-missing-ops-console": (
            OpsReplayObservabilityFailureType.MISSING_OPS_CONSOLE
        ),
        "ops-runtime-missing-observability": (
            OpsReplayObservabilityFailureType.MISSING_OBSERVABILITY
        ),
        "ops-runtime-stale-dashboard": OpsReplayObservabilityFailureType.STALE_DASHBOARD,
        "ops-runtime-unresolved-recovery": (
            OpsReplayObservabilityFailureType.UNRESOLVED_RECOVERY
        ),
        "ops-runtime-unsafe-operator-action": (
            OpsReplayObservabilityFailureType.UNSAFE_OPERATOR_ACTION
        ),
        "ops-runtime-replay-mismatch": OpsReplayObservabilityFailureType.REPLAY_MISMATCH,
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, failure in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            telemetry_backend_ref="telemetry-backend:test",
            collector_handoff_ref="collector-handoff:test",
            out=tmp_path / fixture_id,
        )
        assert_ops_runtime_negative(
            report,
            operator_status=failure.value,
            failure_type=failure.value,
        )
