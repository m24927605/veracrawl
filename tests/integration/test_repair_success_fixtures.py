from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import repair_success
from veracrawl.contracts.enums import CompletenessResult, RepairBenchmarkFailureType


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("repair-success-quality", CompletenessResult.PASS, None),
        (
            "repair-success-low-rate",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.SUCCESS_RATE_BELOW_THRESHOLD,
        ),
        (
            "repair-success-unsafe-bypass",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.UNSAFE_BYPASS_DETECTED,
        ),
        (
            "repair-success-owner-service-bypass",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.OWNER_SERVICE_BYPASS,
        ),
        (
            "repair-success-model-only-evidence",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.MODEL_ONLY_EVIDENCE,
        ),
        (
            "repair-success-missing-trace",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.MISSING_TRACE_REFS,
        ),
        (
            "repair-success-rollback-missing",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.MISSING_ROLLBACK_REFS,
        ),
        (
            "repair-success-unresolved-hidden",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.UNRESOLVED_CRITICAL_REPAIR,
        ),
        (
            "repair-success-replay-missing",
            CompletenessResult.FAIL,
            RepairBenchmarkFailureType.MISSING_REPLAY_REFS,
        ),
    ],
)
def test_repair_success_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: RepairBenchmarkFailureType | None,
) -> None:
    result = repair_success.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "repair_quality_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.repairable_case_count >= 30
        assert result.report.repair_success_rate >= 0.80
        assert result.report.unsafe_bypass_rate == 0
