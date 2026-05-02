from __future__ import annotations

from pathlib import Path

from tests.helpers.queue_broker_fixture_assertions import (
    assert_queue_broker_negative,
    assert_queue_broker_runtime_unavailable,
)
from veracrawl.cli.queue_broker import run_fixture


def test_queue_broker_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "redis-broker-runtime-unavailable",
        profile="target",
        out=tmp_path / "redis-broker-runtime-unavailable",
    )
    assert_queue_broker_runtime_unavailable(report)


def test_queue_broker_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "broker-missing-fencing-token": "broker_missing_fencing_token",
        "broker-missing-heartbeat": "broker_missing_heartbeat",
        "broker-missing-dead-letter": "broker_missing_dead_letter",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_queue_broker_negative(report, operator_status=operator_status)
