from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.durable_fixture_assertions import assert_durable_success
from veracrawl.cli.durable import run_fixture


def test_durable_runtime_success_fixture_reloads_state(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "tests" / "fixtures" / "durable-runtime-success"
    report = run_fixture(fixture, profile="target", out=tmp_path / "durable-runtime-success")
    assert_durable_success(report)
    written = json.loads((tmp_path / "durable-runtime-success" / "run_report.json").read_text())
    assert written["reloaded"] is True
    assert written["completion_result"] == "pass"


def test_durable_duplicate_command_fixture_dedupes(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "tests" / "fixtures" / "durable-duplicate-command"
    report = run_fixture(fixture, profile="target", out=tmp_path / "durable-duplicate-command")
    assert_durable_success(report)
    assert report.duplicate_command_deduped is True
    assert report.event_count == 1
    assert report.outbox_count == 1
