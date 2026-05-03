from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.target_runtime_fixture_assertions import assert_target_runtime_fixture


@pytest.mark.parametrize(
    "fixture_name",
    [
        "target-runtime-success",
        "target-runtime-drift-repair",
        "target-runtime-needs-review",
        "target-runtime-policy-denied",
        "target-runtime-prompt-injection",
        "target-runtime-missing-evidence",
        "target-runtime-replay-mismatch",
        "target-runtime-partial-export",
        "target-runtime-false-complete",
    ],
)
def test_target_runtime_fixture_contracts(
    fixture_name: str,
    tmp_path: Path,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    assert_target_runtime_fixture(fixture_dir, out_dir=tmp_path / fixture_name)
