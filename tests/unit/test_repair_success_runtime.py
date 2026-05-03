from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.repair_success import run_repair_success_benchmark
from veracrawl.contracts.enums import CompletenessResult, RepairBenchmarkFailureType
from veracrawl.contracts.repair_success import RepairQualityManifest
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest(
    *,
    scenario: str = "repair-success-quality",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: RepairBenchmarkFailureType | None = None,
) -> RepairQualityManifest:
    return RepairQualityManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["quality"],
        expected_completion_result=expected_result,
        expected_operator_status=(
            expected_failure.value if expected_failure else "repair_quality_completed"
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_ref_types=["repair_case", "repair_attempt", "replay"],
    )


def test_repair_success_runtime_computes_success_and_safety_metrics(
    tmp_path: Path,
) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.repairable_case_count >= 30
    assert result.report.repair_success_rate >= 0.80
    assert result.report.unsafe_bypass_rate == 0
    assert result.report.unresolved_critical_rate == 0
    assert len(result.seeded_cases) >= 30
    assert len(result.repair_attempts) == len(result.seeded_cases)
    assert all(item.model_call_trace_refs for item in result.repair_attempts)
    assert all(item.replay_bundle_ref for item in result.repair_attempts)


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("repair-success-low-rate", RepairBenchmarkFailureType.SUCCESS_RATE_BELOW_THRESHOLD),
        ("repair-success-unsafe-bypass", RepairBenchmarkFailureType.UNSAFE_BYPASS_DETECTED),
        ("repair-success-owner-service-bypass", RepairBenchmarkFailureType.OWNER_SERVICE_BYPASS),
        ("repair-success-model-only-evidence", RepairBenchmarkFailureType.MODEL_ONLY_EVIDENCE),
        ("repair-success-missing-trace", RepairBenchmarkFailureType.MISSING_TRACE_REFS),
        ("repair-success-rollback-missing", RepairBenchmarkFailureType.MISSING_ROLLBACK_REFS),
        (
            "repair-success-unresolved-hidden",
            RepairBenchmarkFailureType.UNRESOLVED_CRITICAL_REPAIR,
        ),
        ("repair-success-replay-missing", RepairBenchmarkFailureType.MISSING_REPLAY_REFS),
    ],
)
def test_repair_success_runtime_maps_negative_fixtures(
    tmp_path: Path,
    scenario: str,
    failure: RepairBenchmarkFailureType,
) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(
            scenario=scenario,
            expected_result=CompletenessResult.FAIL,
            expected_failure=failure,
        ),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
