from __future__ import annotations

from pathlib import Path

from tests.helpers.projection_fixture_assertions import (
    assert_advanced_graph_negative,
    assert_advanced_graph_success,
)
from veracrawl.cli.projection import run_fixture


def test_advanced_graph_projection_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "projection-rebuild-success",
        "graph-signal-frontier-review",
        "temporal-graph-foundation",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_advanced_graph_success(report)


def test_advanced_graph_projection_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "projection-missing-watermark": "missing_projection_watermark",
        "projection-mismatch": "projection_mismatch",
        "graph-signal-as-evidence": "graph_signal_as_evidence",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_advanced_graph_negative(report, operator_status=operator_status)
