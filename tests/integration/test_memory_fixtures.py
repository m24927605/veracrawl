from __future__ import annotations

from pathlib import Path

from tests.helpers.memory_fixture_assertions import assert_memory_negative, assert_memory_success
from veracrawl.cli.memory import run_fixture


def test_memory_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "memory-write-retrieve-success",
        "memory-invalidation-exclusion",
        "cross-scope-sanitized-memory",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_memory_success(report)


def test_memory_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "poisoned-memory-blocked": "tainted_memory_for_prompt",
        "unauthorized-cross-scope-memory": "unauthorized_cross_scope_tunnel",
        "memory-as-evidence": "memory_as_evidence",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_memory_negative(report, operator_status=operator_status)
