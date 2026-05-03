from __future__ import annotations

import json
from pathlib import Path

import pytest

from veracrawl.adapters.sources.target_processing import build_processing_evidence_records
from veracrawl.adapters.sources.target_runtime import build_adapter_backed_source_records
from veracrawl.contracts.enums import (
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
)
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
    TargetProcessingEvidenceEntry,
    TargetProcessingEvidenceManifest,
    TargetProcessingEvidenceRecord,
    TargetSourceCorpusManifest,
)
from veracrawl.target_runtime.runner import run_target_runtime_fixture


def _load(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _inputs(
    fixture_name: str,
) -> tuple[
    Path,
    TargetAdapterBackedSourceManifest,
    list[TargetAdapterBackedSourceRecord],
    TargetProcessingEvidenceManifest,
    list[TargetProcessingEvidenceRecord],
]:
    fixture_dir = Path("tests/fixtures") / fixture_name
    corpus = TargetSourceCorpusManifest.model_validate(_load(fixture_dir / "corpus.json"))
    adapter_manifest = TargetAdapterBackedSourceManifest.model_validate(
        _load(fixture_dir / "adapter_backing.json")
    )
    adapter_records = build_adapter_backed_source_records(
        fixture_dir=fixture_dir,
        adapter_manifest=adapter_manifest,
        source_corpus=corpus,
    )
    processing_manifest = TargetProcessingEvidenceManifest.model_validate(
        _load(fixture_dir / "processing_evidence.json")
    )
    processing_records = build_processing_evidence_records(
        processing_manifest=processing_manifest,
        adapter_records=adapter_records,
    )
    return fixture_dir, adapter_manifest, adapter_records, processing_manifest, processing_records


def test_processing_evidence_success_exposes_lineage_refs() -> None:
    fixture_dir, adapter_manifest, adapter_records, processing_manifest, processing_records = (
        _inputs("processing-evidence-target-success")
    )
    result = run_target_runtime_fixture(
        fixture_id="processing-evidence-target-success",
        scenario="processing-evidence-target-success",
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
        adapter_manifest=adapter_manifest,
        adapter_records=adapter_records,
        processing_manifest=processing_manifest,
        processing_records=processing_records,
    )
    assert result.report.status == TargetRuntimeStatus.COMPLETE
    assert result.report.operator_status == "processing_evidence_target_runtime_completed"
    assert len(result.report.processing_evidence_refs) == 7
    assert len(result.report.normalized_document_refs) == 7
    assert len(result.report.extraction_candidate_refs) == 7
    assert len(result.report.evidence_packet_refs) == 7
    assert len(result.report.evidence_anchor_refs) >= 7
    assert len(result.report.publication_report_refs) == 7


def test_processing_evidence_manifest_extra_entry_fails_without_adapter_crash() -> None:
    fixture_dir, adapter_manifest, adapter_records, processing_manifest, _ = _inputs(
        "processing-evidence-target-success"
    )
    expanded_manifest = TargetProcessingEvidenceManifest(
        id="processing-evidence-target-success:processing-expanded",
        fixture_id=processing_manifest.fixture_id,
        entries=[
            *processing_manifest.entries,
            TargetProcessingEvidenceEntry(
                id="processing-evidence-target-success:missing-adapter-entry",
                corpus_entry_ref="missing-adapter-entry",
                adapter_backed_source_ref=(
                    "adapter-backed-source:processing-evidence-target-success:"
                    "missing-adapter-entry"
                ),
                required_field_refs=["title"],
                policy_decision_ref="policy:processing-evidence-target-success:missing",
            ),
        ],
        expected_processing_evidence_count=8,
        policy_decision_refs=[
            *processing_manifest.policy_decision_refs,
            "policy:processing-evidence-target-success:missing",
        ],
        replay_oracle_ref=processing_manifest.replay_oracle_ref,
    )
    processing_records = build_processing_evidence_records(
        processing_manifest=expanded_manifest,
        adapter_records=adapter_records,
    )
    result = run_target_runtime_fixture(
        fixture_id="processing-evidence-target-success",
        scenario="processing-evidence-target-success",
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
        adapter_manifest=adapter_manifest,
        adapter_records=adapter_records,
        processing_manifest=expanded_manifest,
        processing_records=processing_records,
    )
    assert len(processing_records) == 7
    assert result.report.status == TargetRuntimeStatus.FAILED
    assert result.report.failure_type == TargetRuntimeFailureType.PROCESSING_MISSING


@pytest.mark.parametrize(
    ("fixture_name", "failure"),
    [
        (
            "processing-evidence-target-missing-normalization",
            TargetRuntimeFailureType.PROCESSING_MISSING,
        ),
        (
            "processing-evidence-target-missing-candidate-anchor",
            TargetRuntimeFailureType.EVIDENCE_MISSING,
        ),
        (
            "processing-evidence-target-missing-evidence-packet",
            TargetRuntimeFailureType.EVIDENCE_MISSING,
        ),
        (
            "processing-evidence-target-graph-only-evidence",
            TargetRuntimeFailureType.DERIVED_CONTEXT_AS_EVIDENCE,
        ),
        (
            "processing-evidence-target-publication-bypass",
            TargetRuntimeFailureType.PUBLICATION_BYPASS,
        ),
    ],
)
def test_processing_evidence_negative_fixtures_are_typed(
    fixture_name: str,
    failure: TargetRuntimeFailureType,
) -> None:
    fixture_dir, adapter_manifest, adapter_records, processing_manifest, processing_records = (
        _inputs(fixture_name)
    )
    result = run_target_runtime_fixture(
        fixture_id=fixture_name,
        scenario=fixture_name,
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
        adapter_manifest=adapter_manifest,
        adapter_records=adapter_records,
        processing_manifest=processing_manifest,
        processing_records=processing_records,
    )
    assert result.report.status == TargetRuntimeStatus.FAILED
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
