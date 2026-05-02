from __future__ import annotations

from pathlib import Path

from tests.helpers.infrastructure_fixture_assertions import (
    assert_infrastructure_negative,
    assert_infrastructure_runtime_unavailable,
)
from veracrawl.cli.infrastructure import run_fixture


def test_operational_infrastructure_runtime_unavailable_fixture(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "operational-infrastructure-runtime-unavailable",
        profile="target",
        out=tmp_path / "operational-infrastructure-runtime-unavailable",
    )
    assert_infrastructure_runtime_unavailable(report)


def test_operational_infrastructure_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "infrastructure-missing-persistence-refs": "infrastructure_missing_persistence_refs",
        "infrastructure-missing-queue-refs": "infrastructure_missing_queue_refs",
        "infrastructure-missing-object-refs": "infrastructure_missing_object_refs",
        "infrastructure-missing-replay-refs": "infrastructure_missing_replay_refs",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_infrastructure_negative(report, operator_status=operator_status)
