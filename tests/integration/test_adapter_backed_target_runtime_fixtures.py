from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.target_runtime_fixture_assertions import assert_target_runtime_fixture


@pytest.mark.parametrize(
    "fixture_name",
    [
        "adapter-backed-target-success",
        "adapter-backed-target-missing-adapter-result",
        "adapter-backed-target-output-mismatch",
        "adapter-backed-target-policy-denied",
        "adapter-backed-target-replay-mismatch",
        "adapter-backed-target-direct-source-bypass",
    ],
)
def test_adapter_backed_target_runtime_fixture_contracts(
    fixture_name: str,
    tmp_path: Path,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    assert_target_runtime_fixture(fixture_dir, out_dir=tmp_path / fixture_name)
