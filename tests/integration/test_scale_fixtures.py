from __future__ import annotations

from pathlib import Path

from tests.helpers.scale_fixture_assertions import assert_scale_negative, assert_scale_success
from veracrawl.cli.scale import run_fixture


def test_scale_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "scale-sharding-success",
        "backpressure-autoscale-success",
        "dead-letter-recovery-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_scale_success(report)


def test_scale_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "stale-lease-without-recovery": "stale_lease_without_recovery",
        "unfair-site-starvation": "unfair_site_starvation",
        "autoscale-without-policy": "autoscale_without_policy",
        "dead-letter-missing-failure-record": "dead_letter_missing_failure_record",
        "replay-missing-scale-refs": "replay_missing_scale_refs",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_scale_negative(report, operator_status=operator_status)
