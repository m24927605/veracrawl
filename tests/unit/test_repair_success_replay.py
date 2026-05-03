from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.repair_success import run_repair_success_benchmark
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.repair_success import RepairQualityManifest
from veracrawl.review_replay.repair_success import (
    missing_repair_attempt_replay_refs,
    missing_repair_quality_report_replay_refs,
    missing_seeded_repair_case_replay_refs,
    repair_attempt_replay_passes,
    repair_quality_report_replay_passes,
    seeded_repair_case_replay_passes,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> RepairQualityManifest:
    return RepairQualityManifest(
        id="repair-success-quality",
        scenario="repair-success-quality",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="repair_quality_completed",
        required_ref_types=["repair_case", "repair_attempt", "replay"],
    )


def test_repair_success_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert all(seeded_repair_case_replay_passes(item) for item in result.seeded_cases)
    assert all(repair_attempt_replay_passes(item) for item in result.repair_attempts)
    assert repair_quality_report_replay_passes(result.report)


def test_repair_success_replay_detects_missing_case_replay_ref(
    tmp_path: Path,
) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.seeded_cases[0].model_copy(update={"replay_bundle_ref": None})

    assert "replay_bundle_ref" in missing_seeded_repair_case_replay_refs(broken)
    assert not seeded_repair_case_replay_passes(broken)


def test_repair_success_replay_detects_missing_attempt_trace_refs(
    tmp_path: Path,
) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.repair_attempts[0].model_copy(update={"model_call_trace_refs": []})

    assert "model_call_trace_refs" in missing_repair_attempt_replay_refs(broken)
    assert not repair_attempt_replay_passes(broken)


def test_repair_success_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_repair_success_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_repair_quality_report_replay_refs(broken)
    assert not repair_quality_report_replay_passes(broken)
