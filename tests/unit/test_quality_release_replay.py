from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.quality_release import run_quality_release_gate
from veracrawl.contracts.enums import CompletenessResult, QualityReleaseDecision
from veracrawl.contracts.quality_release import QualityReleaseManifest
from veracrawl.review_replay.quality_release import (
    missing_quality_release_gate_replay_refs,
    missing_quality_release_report_replay_refs,
    missing_quality_release_stability_replay_refs,
    quality_release_gate_replay_passes,
    quality_release_report_replay_passes,
    quality_release_stability_replay_passes,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> QualityReleaseManifest:
    return QualityReleaseManifest(
        id="quality-release-ready",
        scenario="quality-release-ready",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_release_decision=QualityReleaseDecision.RELEASE_READY,
        required_gate_refs=["058", "059", "060", "061", "062", "063"],
    )


def test_quality_release_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_quality_release_gate(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert all(quality_release_gate_replay_passes(item) for item in result.quality_gates)
    assert all(
        quality_release_stability_replay_passes(item) for item in result.stability_runs
    )
    assert quality_release_report_replay_passes(result.report)


def test_quality_release_replay_detects_missing_gate_replay_ref(
    tmp_path: Path,
) -> None:
    result = run_quality_release_gate(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.quality_gates[0].model_copy(update={"replay_bundle_ref": None})

    assert "replay_bundle_ref" in missing_quality_release_gate_replay_refs(broken)
    assert not quality_release_gate_replay_passes(broken)


def test_quality_release_replay_detects_missing_stability_slo_ref(
    tmp_path: Path,
) -> None:
    result = run_quality_release_gate(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.stability_runs[0].model_copy(update={"slo_metric_refs": []})

    assert "slo_metric_refs" in missing_quality_release_stability_replay_refs(broken)
    assert not quality_release_stability_replay_passes(broken)


def test_quality_release_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_quality_release_gate(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_quality_release_report_replay_refs(broken)
    assert not quality_release_report_replay_passes(broken)
