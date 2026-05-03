from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import field_oracle
from veracrawl.contracts.enums import CompletenessResult, FieldOracleFailureType


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("field-oracle-quality-corpus", CompletenessResult.PASS, None),
        ("field-oracle-wrong-value", CompletenessResult.FAIL, FieldOracleFailureType.WRONG_VALUE),
        (
            "field-oracle-missing-anchor",
            CompletenessResult.FAIL,
            FieldOracleFailureType.MISSING_ANCHOR,
        ),
        (
            "field-oracle-schema-violation",
            CompletenessResult.FAIL,
            FieldOracleFailureType.SCHEMA_VIOLATION,
        ),
        (
            "field-oracle-stale-evidence",
            CompletenessResult.FAIL,
            FieldOracleFailureType.STALE_EVIDENCE,
        ),
        (
            "field-oracle-publication-bypass",
            CompletenessResult.FAIL,
            FieldOracleFailureType.PUBLICATION_BYPASS,
        ),
        (
            "field-oracle-llm-as-evidence",
            CompletenessResult.FAIL,
            FieldOracleFailureType.LLM_AS_EVIDENCE,
        ),
    ],
)
def test_field_oracle_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: FieldOracleFailureType | None,
) -> None:
    result = field_oracle.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "field_oracle_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.schema_count == 8
        assert result.report.expected_field_count == 200
