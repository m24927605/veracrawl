from __future__ import annotations

from veracrawl.cli.evidence import _build_evidence, _candidate, _run_publication
from veracrawl.contracts.evidence import EvidencePublicationFixtureManifest
from veracrawl.review_replay.publication import (
    missing_publication_replay_refs,
    publication_replay_passes,
)


def _manifest(fixture_id: str, scenario: str) -> EvidencePublicationFixtureManifest:
    return EvidencePublicationFixtureManifest(
        id=fixture_id,
        scenario=scenario,
        profile_refs=["target"],
        expected_completion_result="pass",
        expected_operator_status="publication_completed",
    )


def test_publication_replay_passes_for_complete_report() -> None:
    manifest = _manifest("unit-replay-pass", "publication-success")
    candidate = _candidate(manifest.id)
    built, _, privacy_refs = _build_evidence(manifest, candidate)
    outcome, _ = _run_publication(manifest, candidate, built, privacy_refs)
    assert publication_replay_passes(outcome.report)


def test_publication_replay_detects_missing_refs() -> None:
    manifest = _manifest("unit-replay-gap", "replay-gap")
    candidate = _candidate(manifest.id)
    built, _, privacy_refs = _build_evidence(manifest, candidate)
    outcome, _ = _run_publication(manifest, candidate, built, privacy_refs)
    missing = missing_publication_replay_refs(outcome.report)
    assert "replay_gap" in missing
