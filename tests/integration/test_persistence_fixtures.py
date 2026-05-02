from __future__ import annotations

from pathlib import Path

from tests.helpers.persistence_fixture_assertions import (
    assert_persistence_negative,
    assert_persistence_success,
)
from veracrawl.cli.persistence import run_fixture


def test_persistence_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "persistence-transaction-success",
        "idempotent-replay-success",
        "queue-lease-recovery-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_persistence_success(report)
        if fixture_id == "idempotent-replay-success":
            assert report.reloaded is True
            assert report.duplicate_deduped is True
            assert report.event_count == 1
            assert report.outbox_count == 1


def test_persistence_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "non-atomic-commit": "non_atomic_commit",
        "idempotency-not-persisted": "idempotency_not_persisted",
        "event-log-gap": "event_log_gap",
        "outbox-dispatch-missing": "outbox_dispatch_missing",
        "artifact-index-missing": "artifact_index_missing",
        "lease-heartbeat-missing": "lease_heartbeat_missing",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_persistence_negative(report, operator_status=operator_status)
