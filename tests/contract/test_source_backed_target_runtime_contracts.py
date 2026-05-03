from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, TargetWebsitePattern
from veracrawl.contracts.target_runtime import (
    TargetSourceCorpusEntry,
    TargetSourceCorpusManifest,
    TargetSourceObservationRecord,
)


def _entry(**overrides: object) -> TargetSourceCorpusEntry:
    data: dict[str, object] = {
        "id": "static-home",
        "website_pattern": TargetWebsitePattern.STATIC,
        "source_path": "sources/static.html",
        "content_type": "html",
        "expected_fields": {"title": "Acme Overview"},
        "evidence_markers": {"title": "Acme Overview"},
        "policy_decision_ref": "policy:source:static",
    }
    data.update(overrides)
    return TargetSourceCorpusEntry.model_validate(data)


def test_source_corpus_entry_requires_generic_evidence_descriptor() -> None:
    assert _entry().allowed is True
    with pytest.raises(ValidationError):
        _entry(expected_fields={})


def test_source_corpus_manifest_requires_unique_entries() -> None:
    entry = _entry()
    with pytest.raises(ValidationError):
        TargetSourceCorpusManifest(
            id="corpus:duplicate",
            fixture_id="source-backed-target-success",
            entries=[entry, entry],
            expected_pattern_count=2,
            policy_decision_refs=["policy:source"],
            replay_oracle_ref="replay-oracle:source",
        )


def test_passing_source_observation_requires_content_hash_and_evidence() -> None:
    data: dict[str, object] = {
        "id": "observation:static",
        "run_ref": "run:source-backed",
        "corpus_entry_ref": "static-home",
        "website_pattern": TargetWebsitePattern.STATIC,
        "source_path_ref": "source-path:static",
        "content_hash_ref": "sha256:abc",
        "source_observation_ref": "source-observation:static",
        "artifact_ref": "artifact:static",
        "extracted_field_refs": ["field:static:title"],
        "evidence_refs": ["evidence:static:title"],
        "graph_refs": ["graph:static"],
        "policy_decision_refs": ["policy:static"],
        "replay_refs": ["replay:static"],
        "result": CompletenessResult.PASS,
    }
    observation = TargetSourceObservationRecord.model_validate(data)
    assert observation.content_hash_ref == "sha256:abc"
    data["evidence_refs"] = []
    with pytest.raises(ValidationError):
        TargetSourceObservationRecord.model_validate(data)
