from __future__ import annotations

import json
from pathlib import Path

import pytest

from veracrawl.adapters.sources.target_runtime import build_adapter_backed_source_records
from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
)
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
    TargetSourceCorpusManifest,
)
from veracrawl.target_runtime.runner import run_target_runtime_fixture


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _adapter_inputs(
    fixture_name: str,
) -> tuple[Path, TargetAdapterBackedSourceManifest, list[TargetAdapterBackedSourceRecord]]:
    fixture_dir = Path("tests/fixtures") / fixture_name
    adapter_manifest = TargetAdapterBackedSourceManifest.model_validate(
        _load_json(fixture_dir / "adapter_backing.json")
    )
    corpus = TargetSourceCorpusManifest.model_validate(_load_json(fixture_dir / "corpus.json"))
    records = build_adapter_backed_source_records(
        fixture_dir=fixture_dir,
        adapter_manifest=adapter_manifest,
        source_corpus=corpus,
    )
    return fixture_dir, adapter_manifest, records


def test_adapter_backed_success_exposes_adapter_lineage_refs() -> None:
    fixture_dir, adapter_manifest, records = _adapter_inputs("adapter-backed-target-success")
    result = run_target_runtime_fixture(
        fixture_id="adapter-backed-target-success",
        scenario="adapter-backed-target-success",
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
        adapter_manifest=adapter_manifest,
        adapter_records=records,
    )
    report = result.report
    assert report.status == TargetRuntimeStatus.COMPLETE
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "adapter_backed_target_runtime_completed"
    assert len(report.adapter_backed_source_refs) == 7
    assert len(report.source_adapter_result_refs) == 7
    assert len(report.adapter_output_refs) == 7
    assert all(record.result == CompletenessResult.PASS for record in result.adapter_backed_records)


@pytest.mark.parametrize(
    ("fixture_name", "status", "failure"),
    [
        (
            "adapter-backed-target-missing-adapter-result",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.ADAPTER_RESULT_MISSING,
        ),
        (
            "adapter-backed-target-output-mismatch",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.ADAPTER_OUTPUT_MISMATCH,
        ),
        (
            "adapter-backed-target-policy-denied",
            TargetRuntimeStatus.BLOCKED,
            TargetRuntimeFailureType.POLICY_DENIED,
        ),
        (
            "adapter-backed-target-replay-mismatch",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.REPLAY_MISMATCH,
        ),
        (
            "adapter-backed-target-direct-source-bypass",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.DIRECT_SOURCE_BYPASS,
        ),
    ],
)
def test_adapter_backed_negative_fixtures_are_typed(
    fixture_name: str,
    status: TargetRuntimeStatus,
    failure: TargetRuntimeFailureType,
) -> None:
    fixture_dir, adapter_manifest, records = _adapter_inputs(fixture_name)
    result = run_target_runtime_fixture(
        fixture_id=fixture_name,
        scenario=fixture_name,
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
        adapter_manifest=adapter_manifest,
        adapter_records=records,
    )
    assert result.report.status == status
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
