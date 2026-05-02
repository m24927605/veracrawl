from __future__ import annotations

from tests.factories import full_replay_manifest
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.runtime_events.replay import (
    missing_runtime_replay_refs,
    validate_runtime_replay_manifest,
)

RUNTIME_REFS = {
    "normalized_document_refs": ["normalized:1"],
    "extraction_candidate_refs": ["candidate:1"],
    "evidence_packet_refs": ["evidence:1"],
    "verification_decision_refs": ["verification:1"],
    "output_manifest_refs": ["output-manifest:1"],
}


def test_runtime_replay_refs_pass_when_complete() -> None:
    report = validate_runtime_replay_manifest(full_replay_manifest(), runtime_refs=RUNTIME_REFS)
    assert report.completeness_result == CompletenessResult.PASS


def test_runtime_replay_missing_publication_refs_fail() -> None:
    runtime_refs = {**RUNTIME_REFS, "output_manifest_refs": []}
    report = validate_runtime_replay_manifest(full_replay_manifest(), runtime_refs=runtime_refs)
    assert report.completeness_result == CompletenessResult.FAIL
    assert "output_manifest_refs" in report.missing_ref_fields


def test_runtime_replay_combines_base_and_runtime_gaps() -> None:
    manifest = full_replay_manifest().model_copy(update={"redaction_map_ref": None})
    missing = missing_runtime_replay_refs(
        manifest,
        runtime_refs={**RUNTIME_REFS, "verification_decision_refs": []},
    )
    assert "redaction_map_ref" in missing
    assert "verification_decision_refs" in missing
