from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.run_control import run_fixture


@pytest.mark.parametrize(
    "fixture_name",
    [
        "production-run-control-success",
        "production-run-control-paused-resumed",
        "production-run-control-cancelled",
        "production-run-control-policy-denied",
        "production-run-control-missing-approval",
        "production-run-control-missing-budget",
        "production-run-control-invalid-transition",
        "production-run-control-missing-replay",
    ],
)
def test_production_run_control_fixture(fixture_name: str, tmp_path: Path) -> None:
    report = run_fixture(
        Path("tests/fixtures") / fixture_name,
        profile="target",
        out=tmp_path / fixture_name,
    )
    assert report.fixture_id == fixture_name
