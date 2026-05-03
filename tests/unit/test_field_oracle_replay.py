from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.field_oracle import run_field_oracle_benchmark
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.field_oracle import FieldOracleBenchmarkManifest
from veracrawl.review_replay.field_oracle import (
    field_evaluation_replay_passes,
    field_oracle_report_replay_passes,
    missing_field_evaluation_replay_refs,
    missing_field_oracle_report_replay_refs,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> FieldOracleBenchmarkManifest:
    return FieldOracleBenchmarkManifest(
        id="field-oracle-quality-corpus",
        scenario="field-oracle-quality-corpus",
        profile_refs=["quality"],
        generated_schema_count=8,
        generated_fields_per_schema=25,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="field_oracle_completed",
        required_ref_types=["schema", "field", "replay"],
    )


def test_field_oracle_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_field_oracle_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert all(field_evaluation_replay_passes(item) for item in result.evaluations)
    assert field_oracle_report_replay_passes(result.report)


def test_field_oracle_replay_detects_missing_evaluation_replay_ref(tmp_path: Path) -> None:
    result = run_field_oracle_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.evaluations[0].model_copy(update={"replay_bundle_ref": None})

    assert "replay_bundle_ref" in missing_field_evaluation_replay_refs(broken)
    assert not field_evaluation_replay_passes(broken)


def test_field_oracle_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_field_oracle_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_field_oracle_report_replay_refs(broken)
    assert not field_oracle_report_replay_passes(broken)
