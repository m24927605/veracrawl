"""Contract tests for s8.a — DriftReport + RepairProposal + ExtractionOutcome."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.repair_proposal import FieldRepair, RepairProposal


def _drift(**overrides: object) -> DriftReport:
    payload: dict[str, object] = {
        "id": "drift:run-1:1",
        "run_ref": "run:1",
        "proposal_ref": "proposal:run-1:hash",
        "pages_evaluated": 5,
        "field_missing_rates": {"title": 0.1, "price": 0.4},
        "drifted_fields": ["price"],
        "drift_threshold": 0.30,
        "replay_refs": ["run:1", "proposal:run-1:hash"],
    }
    payload.update(overrides)
    return DriftReport(**payload)  # type: ignore[arg-type]


def _outcome(**overrides: object) -> ExtractionOutcome:
    payload: dict[str, object] = {
        "id": "outcome:1",
        "run_ref": "run:1",
        "page_canonical_url": "https://a.example/1",
        "field_outcomes": {"title": True, "price": False},
        "replay_refs": ["run:1"],
    }
    payload.update(overrides)
    return ExtractionOutcome(**payload)  # type: ignore[arg-type]


def _repair_field(**overrides: object) -> FieldRepair:
    payload: dict[str, object] = {
        "field_name": "price",
        "original_xpath": "//span[@class='price']",
        "proposed_xpath": "//div[@class='price']//span",
        "confidence": 0.7,
        "repair_kind": "anchor_reselect",
    }
    payload.update(overrides)
    return FieldRepair(**payload)  # type: ignore[arg-type]


def _repair(**overrides: object) -> RepairProposal:
    payload: dict[str, object] = {
        "id": "repair:run-1:1",
        "run_ref": "run:1",
        "drift_report_ref": "drift:run-1:1",
        "field_repairs": [_repair_field()],
        "replay_refs": ["run:1", "drift:run-1:1"],
    }
    payload.update(overrides)
    return RepairProposal(**payload)  # type: ignore[arg-type]


# DriftReport tests (1-9)
def test_drift_report_rejects_blank_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="id"):
        _drift(id=" ")


def test_drift_report_rejects_blank_run_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="run_ref"):
        _drift(run_ref=" ")


def test_drift_report_rejects_blank_proposal_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposal_ref"):
        _drift(proposal_ref=" ")


def test_drift_report_rejects_zero_pages_evaluated() -> None:
    with pytest.raises((ValidationError, ValueError), match="pages_evaluated"):
        _drift(pages_evaluated=0)


def test_drift_report_rejects_rate_above_one() -> None:
    with pytest.raises((ValidationError, ValueError), match="field_missing_rates"):
        _drift(field_missing_rates={"title": 1.5})


def test_drift_report_rejects_threshold_at_one() -> None:
    with pytest.raises((ValidationError, ValueError), match="drift_threshold"):
        _drift(drift_threshold=1.0)


def test_drift_report_rejects_drifted_field_not_in_rates() -> None:
    with pytest.raises((ValidationError, ValueError), match="drifted_fields"):
        _drift(drifted_fields=["unknown"])


def test_drift_report_rejects_empty_replay_refs() -> None:
    with pytest.raises((ValidationError, ValueError), match="replay_refs"):
        _drift(replay_refs=[])


def test_drift_report_canonical_json_is_deterministic() -> None:
    assert _drift().canonical_json() == _drift().canonical_json()


# RepairProposal tests (10-15)
def test_repair_field_rejects_blank_field_name() -> None:
    with pytest.raises((ValidationError, ValueError), match="field_name"):
        _repair_field(field_name=" ")


def test_repair_field_rejects_blank_proposed_xpath() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposed_xpath"):
        _repair_field(proposed_xpath=" ")


def test_repair_field_rejects_invalid_kind() -> None:
    with pytest.raises((ValidationError, ValueError), match="repair_kind"):
        _repair_field(repair_kind="rewrite_everything")


def test_repair_field_rejects_confidence_above_one() -> None:
    with pytest.raises((ValidationError, ValueError), match="confidence"):
        _repair_field(confidence=1.1)


def test_repair_proposal_rejects_empty_field_repairs() -> None:
    with pytest.raises((ValidationError, ValueError), match="field_repairs"):
        _repair(field_repairs=[])


def test_repair_proposal_canonical_json_is_deterministic() -> None:
    assert _repair().canonical_json() == _repair().canonical_json()


# ExtractionOutcome tests
def test_extraction_outcome_rejects_blank_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="id"):
        _outcome(id=" ")


def test_extraction_outcome_rejects_empty_field_outcomes() -> None:
    with pytest.raises((ValidationError, ValueError), match="field_outcomes"):
        _outcome(field_outcomes={})


def test_extraction_outcome_rejects_blank_replay_refs_entry() -> None:
    with pytest.raises((ValidationError, ValueError), match="replay_refs"):
        _outcome(replay_refs=["run:1", " "])


# R7 extra-field rejection coverage
def test_drift_report_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        DriftReport(  # type: ignore[call-arg]
            id="drift:1", run_ref="run:1", proposal_ref="proposal:1",
            pages_evaluated=1, field_missing_rates={"x": 0.1},
            replay_refs=["run:1"],
            unexpected_extra="boom",
        )


def test_repair_proposal_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RepairProposal(  # type: ignore[call-arg]
            id="repair:1", run_ref="run:1", drift_report_ref="drift:1",
            field_repairs=[_repair_field()], replay_refs=["run:1"],
            unexpected_extra="boom",
        )


def test_extraction_outcome_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExtractionOutcome(  # type: ignore[call-arg]
            id="outcome:1", run_ref="run:1",
            page_canonical_url="https://a.example/1",
            field_outcomes={"t": True}, replay_refs=["run:1"],
            unexpected_extra="boom",
        )
