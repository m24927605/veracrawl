from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_evidence_publication_contracts_registered() -> None:
    for contract in [
        "EvidenceAnchor",
        "EvidencePacketManifest",
        "EvidencePublicationFixtureManifest",
        "ReviewDecision",
        "PublicationReport",
    ]:
        assert contract in FOUNDATION_CONTRACTS


def test_evidence_publication_commands_events_fixtures_registered() -> None:
    assert {
        "record_evidence_anchor",
        "record_evidence_manifest",
        "record_review_decision",
        "record_publication_report",
    }.issubset(COMMAND_TYPES)
    assert {
        "evidence_anchor_recorded",
        "evidence_manifest_recorded",
        "review_decision_recorded",
        "publication_report_recorded",
    }.issubset(EVENT_TYPES)
    assert "evidence_publication" in TARGET_CONTRACT_AREAS
    assert {
        "evidence-field-coverage",
        "evidence-verification-review",
        "evidence-publication-success",
        "evidence-missing-anchor",
        "evidence-verification-conflict",
        "evidence-policy-denied",
        "evidence-replay-gap",
        "evidence-candidate-direct-publication",
    }.issubset(FIXTURE_ORACLES)


def test_evidence_publication_registry_validation_passes() -> None:
    assert validate_registry().ok
