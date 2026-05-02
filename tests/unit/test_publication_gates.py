from __future__ import annotations

from veracrawl.cli.evidence import _build_evidence, _candidate, _run_publication
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.evidence import EvidencePublicationFixtureManifest
from veracrawl.publish.gates import reject_direct_candidate_publication


def _manifest(fixture_id: str, scenario: str) -> EvidencePublicationFixtureManifest:
    return EvidencePublicationFixtureManifest(
        id=fixture_id,
        scenario=scenario,
        profile_refs=["target"],
        expected_completion_result="pass",
        expected_operator_status="publication_completed",
    )


def test_publication_requires_all_gates() -> None:
    manifest = _manifest("unit-publish", "publication-success")
    candidate = _candidate(manifest.id)
    built, _, privacy_refs = _build_evidence(manifest, candidate)
    outcome, _ = _run_publication(manifest, candidate, built, privacy_refs)
    assert outcome.report.completion_result == CompletenessResult.PASS
    assert outcome.published_output
    assert outcome.output_manifest


def test_publication_blocks_policy_denial() -> None:
    manifest = _manifest("unit-policy-denied", "policy-denied")
    candidate = _candidate(manifest.id)
    built, _, privacy_refs = _build_evidence(manifest, candidate)
    outcome, _ = _run_publication(manifest, candidate, built, privacy_refs)
    assert outcome.report.completion_result == CompletenessResult.FAIL
    assert outcome.published_output is None
    assert "publication_policy_denied" in outcome.report.missing_ref_fields


def test_direct_candidate_publication_is_rejected() -> None:
    candidate = _candidate("unit-direct")
    outcome = reject_direct_candidate_publication(
        fixture_id="unit-direct",
        run_ref="run:unit-direct",
        candidate=candidate,
    )
    assert outcome.report.completion_result == CompletenessResult.FAIL
    assert "candidate_direct_publication" in outcome.report.missing_ref_fields
