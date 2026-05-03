from __future__ import annotations

from pathlib import Path

from tests.helpers.production_benchmark_release_fixture_assertions import (
    assert_release_negative,
    assert_release_success,
)
from veracrawl.cli.release_gate import run_fixture
from veracrawl.contracts.enums import ProductionBenchmarkReleaseFailureType


def test_production_release_success_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "production-release-benchmark-success",
        profile="target",
        telemetry_backend_ref="telemetry-backend:test",
        collector_handoff_ref="collector-handoff:test",
        out=tmp_path / "production-release-benchmark-success",
    )
    assert_release_success(report)


def test_production_release_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "production-release-missing-target-runtime": (
            ProductionBenchmarkReleaseFailureType.MISSING_TARGET_RUNTIME
        ),
        "production-release-missing-source-coverage": (
            ProductionBenchmarkReleaseFailureType.MISSING_SOURCE_COVERAGE
        ),
        "production-release-missing-product-acceptance": (
            ProductionBenchmarkReleaseFailureType.MISSING_PRODUCT_ACCEPTANCE
        ),
        "production-release-missing-security-privacy": (
            ProductionBenchmarkReleaseFailureType.MISSING_SECURITY_PRIVACY
        ),
        "production-release-missing-publication": (
            ProductionBenchmarkReleaseFailureType.MISSING_PUBLICATION
        ),
        "production-release-missing-worker-orchestration": (
            ProductionBenchmarkReleaseFailureType.MISSING_WORKER_ORCHESTRATION
        ),
        "production-release-missing-ops-runtime": (
            ProductionBenchmarkReleaseFailureType.MISSING_OPS_RUNTIME
        ),
        "production-release-slo-violation": (
            ProductionBenchmarkReleaseFailureType.SLO_VIOLATION
        ),
        "production-release-blocker-present": (
            ProductionBenchmarkReleaseFailureType.RELEASE_BLOCKER_PRESENT
        ),
        "production-release-false-ready": (
            ProductionBenchmarkReleaseFailureType.FALSE_READY
        ),
        "production-release-replay-mismatch": (
            ProductionBenchmarkReleaseFailureType.REPLAY_MISMATCH
        ),
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
        assert_release_negative(
            report,
            release_status=failure.value,
            failure_type=failure.value,
        )
