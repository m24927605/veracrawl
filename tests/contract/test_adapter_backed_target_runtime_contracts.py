from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import AdapterType, CompletenessResult
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceEntry,
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
)


def _entry(**overrides: object) -> TargetAdapterBackedSourceEntry:
    data: dict[str, object] = {
        "id": "adapter-backed-target-success:static-home",
        "corpus_entry_ref": "static-home",
        "adapter_type": AdapterType.HTTP,
        "adapter_spec_ref": "adapter-spec:target:http",
        "adapter_source_ref": "adapter-source:static-home",
        "policy_decision_ref": "policy:adapter:static",
    }
    data.update(overrides)
    return TargetAdapterBackedSourceEntry.model_validate(data)


def test_adapter_backed_entry_requires_adapter_and_policy_refs() -> None:
    assert _entry().require_source_adapter_result is True
    with pytest.raises(ValidationError):
        _entry(adapter_spec_ref="")


def test_adapter_backed_manifest_rejects_duplicate_corpus_refs() -> None:
    entry = _entry()
    with pytest.raises(ValidationError):
        TargetAdapterBackedSourceManifest(
            id="adapter-backed:duplicate",
            fixture_id="adapter-backed-target-success",
            entries=[entry, entry],
            required_adapter_types=[AdapterType.HTTP],
            expected_adapter_result_count=1,
            policy_decision_refs=["policy:adapter"],
            replay_oracle_ref="replay-oracle:adapter",
        )


def test_passing_adapter_backed_record_requires_adapter_output_and_replay() -> None:
    data: dict[str, object] = {
        "id": "adapter-backed-source:static",
        "run_ref": "run:adapter-backed-target-success",
        "corpus_entry_ref": "static-home",
        "adapter_type": AdapterType.HTTP,
        "source_adapter_result_ref": "source-result:static",
        "adapter_output_refs": ["adapter-output:static"],
        "adapter_policy_decision_refs": ["policy:adapter:static"],
        "adapter_replay_refs": ["event:adapter:static"],
        "source_observation_ref": "source-observation:static",
        "content_hash_ref": "sha256:abc",
        "result": CompletenessResult.PASS,
    }
    record = TargetAdapterBackedSourceRecord.model_validate(data)
    assert record.source_adapter_result_ref == "source-result:static"
    data["adapter_output_refs"] = []
    with pytest.raises(ValidationError):
        TargetAdapterBackedSourceRecord.model_validate(data)


def test_failed_adapter_backed_record_requires_typed_diagnostics() -> None:
    with pytest.raises(ValidationError):
        TargetAdapterBackedSourceRecord(
            id="adapter-backed-source:bad",
            run_ref="run:adapter-backed",
            corpus_entry_ref="static-home",
            adapter_type=AdapterType.HTTP,
            result=CompletenessResult.FAIL,
        )
