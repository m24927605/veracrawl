from __future__ import annotations

from pathlib import Path

from tests.helpers.multi_agent_fixture_assertions import (
    assert_multi_agent_negative,
    assert_multi_agent_success,
)
from veracrawl.cli.agents import run_fixture


def test_multi_agent_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "multi-agent-repair-success",
        "coordination-arbitration-success",
        "repair-loop-evidence-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_multi_agent_success(report)


def test_multi_agent_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "owner-service-bypass": "owner_service_bypass",
        "unresolved-coordination-conflict": "unresolved_coordination_conflict",
        "agent-reasoning-as-evidence": "agent_reasoning_as_evidence",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_multi_agent_negative(report, operator_status=operator_status)
