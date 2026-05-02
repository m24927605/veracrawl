from __future__ import annotations

from pathlib import Path

from tests.helpers.graph_fixture_assertions import assert_graph_negative, assert_graph_success
from veracrawl.cli.graph import run_fixture


def test_graph_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "graph-url-hyperlink",
        "graph-canonical-redirect",
        "graph-page-structure",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_graph_success(report)


def test_graph_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "graph-missing-input": "missing_graph_input",
        "graph-rebuild-mismatch": "rebuild_mismatch",
        "graph-as-evidence": "graph_as_evidence",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_graph_negative(report, operator_status=operator_status)
