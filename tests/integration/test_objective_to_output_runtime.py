from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.runtime_fixture_assertions import assert_successful_runtime_report
from veracrawl.cli.runtime import run_fixture


def test_objective_to_output_runtime_fixture(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "tests" / "fixtures" / "runtime-record-success"
    report = run_fixture(fixture, profile="target", out=tmp_path / "runtime-record-success")
    assert_successful_runtime_report(report)
    written = json.loads((tmp_path / "runtime-record-success" / "run_report.json").read_text())
    assert written["published"] is True
    assert written["missing_replay_ref_fields"] == []
