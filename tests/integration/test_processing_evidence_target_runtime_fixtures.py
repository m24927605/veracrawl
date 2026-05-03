from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.target_runtime_fixture_assertions import assert_target_runtime_fixture


@pytest.mark.parametrize(
    "fixture_name",
    [
        "processing-evidence-target-success",
        "processing-evidence-target-missing-normalization",
        "processing-evidence-target-missing-candidate-anchor",
        "processing-evidence-target-missing-evidence-packet",
        "processing-evidence-target-graph-only-evidence",
        "processing-evidence-target-publication-bypass",
    ],
)
def test_processing_evidence_target_runtime_fixture_contracts(
    fixture_name: str,
    tmp_path: Path,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    assert_target_runtime_fixture(fixture_dir, out_dir=tmp_path / fixture_name)
