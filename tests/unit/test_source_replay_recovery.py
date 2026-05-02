from __future__ import annotations

from veracrawl.adapters.sources.deterministic import DeterministicSourceAdapter
from veracrawl.contracts.enums import AdapterType
from veracrawl.fetch.acquisition import execute_source_acquisition
from veracrawl.review_replay.source import missing_source_replay_refs, source_replay_passes


def test_source_replay_passes_with_complete_success_refs() -> None:
    outcome = execute_source_acquisition(
        fixture_id="source-replay-pass",
        adapter_type=AdapterType.HTTP,
        scenario="success",
        adapter=DeterministicSourceAdapter(adapter_type=AdapterType.HTTP),
    )
    assert source_replay_passes(outcome.report)
    assert missing_source_replay_refs(outcome.report) == []


def test_source_replay_fails_missing_artifact() -> None:
    outcome = execute_source_acquisition(
        fixture_id="source-replay-missing",
        adapter_type=AdapterType.HTTP,
        scenario="missing-artifact",
        adapter=DeterministicSourceAdapter(adapter_type=AdapterType.HTTP),
    )
    assert not source_replay_passes(outcome.report)
    assert "artifact_refs" in missing_source_replay_refs(outcome.report)
