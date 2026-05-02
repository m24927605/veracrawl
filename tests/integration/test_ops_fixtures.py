from __future__ import annotations

from pathlib import Path

from tests.helpers.ops_fixture_assertions import assert_ops_negative, assert_ops_success
from veracrawl.cli.ops import run_fixture


def test_ops_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "review-console-success",
        "replay-audit-success",
        "quality-dashboard-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_ops_success(report)


def test_ops_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "missing-review-evidence": "missing_review_evidence",
        "unresolved-failure-without-recovery": "unresolved_failure_without_recovery",
        "stale-dashboard-projection": "stale_dashboard_projection",
        "unsafe-recovery-without-review": "unsafe_recovery_without_review",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_ops_negative(report, operator_status=operator_status)
