from __future__ import annotations

from pathlib import Path

from tests.helpers.persistence_adapter_fixture_assertions import (
    assert_postgres_runtime_unavailable,
)
from veracrawl.cli.persistence_adapter import run_fixture


def test_postgres_runtime_unavailable_fixture_is_needs_review(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "postgres-runtime-unavailable",
        profile="target",
        out=tmp_path / "postgres-runtime-unavailable",
    )
    assert_postgres_runtime_unavailable(report)
