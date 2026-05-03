from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.target_runtime import (
    TargetProcessingEvidenceEntry,
    TargetProcessingEvidenceManifest,
    TargetProcessingEvidenceRecord,
)


def _entry(**overrides: object) -> TargetProcessingEvidenceEntry:
    data: dict[str, object] = {
        "id": "processing-evidence-target-success:static-home",
        "corpus_entry_ref": "static-home",
        "adapter_backed_source_ref": "adapter-backed-source:static-home",
        "required_field_refs": ["title"],
        "policy_decision_ref": "policy:processing:static",
    }
    data.update(overrides)
    return TargetProcessingEvidenceEntry.model_validate(data)


def test_processing_evidence_entry_requires_adapter_backed_source_and_fields() -> None:
    assert _entry().required_field_refs == ["title"]
    with pytest.raises(ValidationError):
        _entry(required_field_refs=[])


def test_processing_evidence_manifest_rejects_duplicate_corpus_refs() -> None:
    entry = _entry()
    with pytest.raises(ValidationError):
        TargetProcessingEvidenceManifest(
            id="processing:duplicate",
            fixture_id="processing-evidence-target-success",
            entries=[entry, entry],
            expected_processing_evidence_count=1,
            policy_decision_refs=["policy:processing"],
            replay_oracle_ref="replay:processing",
        )


def test_processing_evidence_manifest_rejects_impossible_expected_count() -> None:
    with pytest.raises(ValidationError):
        TargetProcessingEvidenceManifest(
            id="processing:too-many",
            fixture_id="processing-evidence-target-success",
            entries=[_entry()],
            expected_processing_evidence_count=2,
            policy_decision_refs=["policy:processing"],
            replay_oracle_ref="replay:processing",
        )


def test_passing_processing_record_requires_lineage_refs() -> None:
    data: dict[str, object] = {
        "id": "processing-evidence:static",
        "run_ref": "run:processing",
        "corpus_entry_ref": "static-home",
        "adapter_backed_source_ref": "adapter-backed-source:static",
        "source_observation_ref": "source-observation:static",
        "adapter_output_refs": ["adapter-output:static"],
        "normalized_document_ref": "normalized:static",
        "extraction_candidate_ref": "candidate:static",
        "candidate_anchor_refs": ["candidate-anchor:static:title"],
        "evidence_packet_ref": "evidence-packet:static",
        "evidence_anchor_refs": ["evidence-anchor:static:title"],
        "publication_report_ref": "publication-report:static",
        "policy_decision_refs": ["policy:processing:static"],
        "replay_refs": ["replay:processing:static"],
        "result": CompletenessResult.PASS,
    }
    assert TargetProcessingEvidenceRecord.model_validate(data).evidence_packet_ref
    data["evidence_packet_ref"] = None
    with pytest.raises(ValidationError):
        TargetProcessingEvidenceRecord.model_validate(data)


def test_failed_processing_record_requires_typed_diagnostics() -> None:
    with pytest.raises(ValidationError):
        TargetProcessingEvidenceRecord(
            id="processing-evidence:bad",
            run_ref="run:processing",
            corpus_entry_ref="static-home",
            adapter_backed_source_ref="adapter-backed-source:static",
            result=CompletenessResult.FAIL,
        )
