from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from veracrawl.cli.fixtures import main, validate_fixture
from veracrawl.contracts.enums import ComparisonMode
from veracrawl.contracts.errors import FixtureValidationError
from veracrawl.contracts.fixture import ThresholdSpec

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.parametrize(
    "fixture_id, expected",
    [
        ("foundation-fetch-like", "pass"),
        ("foundation-non-fetch", "pass"),
        ("foundation-policy-blocked-source", "pass"),
        ("foundation-replay-missing-ref", "fail"),
        ("foundation-missing-evidence", "needs_review"),
        ("foundation-adapter-mismatch", "fail"),
    ],
)
def test_foundation_fixtures_validate(fixture_id: str, expected: str) -> None:
    report = validate_fixture(FIXTURES / fixture_id, profile="target")
    assert report["completeness_result"] == expected


def test_fixture_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "run"
    assert (
        main(
            [
                "run",
                str(FIXTURES / "foundation-fetch-like"),
                "--profile",
                "target",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    assert (out / "run_report.json").exists()


def test_missing_oracle_fails(tmp_path: Path) -> None:
    copied = tmp_path / "fixture"
    shutil.copytree(FIXTURES / "foundation-fetch-like", copied)
    (copied / "oracles" / "expected_events.yaml").unlink()
    with pytest.raises(FixtureValidationError):
        validate_fixture(copied, profile="target")


def test_undeclared_tolerance_fails() -> None:
    with pytest.raises(ValidationError):
        ThresholdSpec(id="threshold:bad", comparison_mode=ComparisonMode.TOLERANCE)
