"""Unit tests for ``AnchorFrequencyDriftDetector`` (s8.b)."""

from __future__ import annotations

import pytest

from veracrawl.adapters.drift_detection.anchor_frequency_drift_detector import (
    AnchorFrequencyDriftDetector,
)
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal
from veracrawl.ports.drift_detection import DriftDetectionPort


def _proposal() -> SchemaProposal:
    return SchemaProposal(
        id="schema-proposal:1",
        proposal_ref="proposal:run-1:hash",
        source_document_ref="normalized-doc:1",
        proposed_fields=[
            ProposedField(name="title", xpath="//h1", confidence=0.9,
                          evidence_anchor_count=5, proposed_type="string"),
            ProposedField(name="price", xpath="//span[@class='p']",
                          confidence=0.7, evidence_anchor_count=3,
                          proposed_type="number"),
        ],
        proposal_rationale_refs=["rationale:1"],
        replay_refs=["run:1", "normalized-doc:1"],
    )


def _outcome(idx: int, *, hits: dict[str, bool]) -> ExtractionOutcome:
    return ExtractionOutcome(
        id=f"outcome:{idx}",
        run_ref="run:1",
        page_canonical_url=f"https://a.example/{idx}",
        field_outcomes=hits,
        replay_refs=["run:1"],
    )


def test_detect_implements_drift_detection_port() -> None:
    assert isinstance(AnchorFrequencyDriftDetector(), DriftDetectionPort)


def test_detect_flags_field_above_threshold() -> None:
    detector = AnchorFrequencyDriftDetector(drift_threshold=0.30)
    outcomes = [
        _outcome(1, hits={"title": True, "price": False}),
        _outcome(2, hits={"title": True, "price": False}),
        _outcome(3, hits={"title": True, "price": True}),
    ]
    report = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    assert "price" in report.drifted_fields
    assert "title" not in report.drifted_fields


def test_detect_computes_missing_rates_correctly() -> None:
    detector = AnchorFrequencyDriftDetector()
    outcomes = [
        _outcome(1, hits={"title": True, "price": False}),
        _outcome(2, hits={"title": False, "price": False}),
    ]
    report = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    assert report.field_missing_rates["title"] == pytest.approx(0.5)
    assert report.field_missing_rates["price"] == pytest.approx(1.0)


def test_detect_is_pure_function() -> None:
    detector = AnchorFrequencyDriftDetector()
    outcomes = [_outcome(1, hits={"title": True, "price": False})]
    a = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    b = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    assert a.canonical_json() == b.canonical_json()


def test_detect_rejects_empty_outcomes() -> None:
    detector = AnchorFrequencyDriftDetector()
    with pytest.raises(ValueError, match="extraction_outcomes"):
        detector.detect(
            proposal=_proposal(), extraction_outcomes=[], run_ref="run:1",
        )


def test_detector_rejects_threshold_out_of_range() -> None:
    with pytest.raises(ValueError, match="drift_threshold"):
        AnchorFrequencyDriftDetector(drift_threshold=1.0)


def test_detect_pages_evaluated_matches_outcomes_length() -> None:
    detector = AnchorFrequencyDriftDetector()
    outcomes = [_outcome(i, hits={"title": True, "price": True}) for i in range(4)]
    report = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    assert report.pages_evaluated == 4


def test_detect_replay_refs_contain_proposal_ref_and_adapter() -> None:
    detector = AnchorFrequencyDriftDetector()
    outcomes = [_outcome(1, hits={"title": True, "price": True})]
    report = detector.detect(
        proposal=_proposal(), extraction_outcomes=outcomes, run_ref="run:1",
    )
    assert "proposal:run-1:hash" in report.replay_refs
    assert "adapter:anchor-frequency-drift:v1" in report.replay_refs
