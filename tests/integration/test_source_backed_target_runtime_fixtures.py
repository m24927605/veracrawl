from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.target_runtime_fixture_assertions import assert_target_runtime_fixture


@pytest.mark.parametrize(
    "fixture_name",
    [
        "source-backed-target-success",
        "source-backed-target-policy-denied",
        "source-backed-target-prompt-injection",
        "source-backed-target-missing-evidence",
        "source-backed-target-replay-mismatch",
        "source-backed-target-partial-export",
    ],
)
def test_source_backed_target_runtime_fixture_contracts(
    fixture_name: str,
    tmp_path: Path,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    assert_target_runtime_fixture(fixture_dir, out_dir=tmp_path / fixture_name)
