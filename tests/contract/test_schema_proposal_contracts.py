"""Contract tests for s7 ``SchemaProposal`` + ``ProposedField`` (tests 1-9d)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal


def _field(**overrides: object) -> ProposedField:
    payload: dict[str, object] = {
        "name": "title",
        "xpath": "//h1",
        "confidence": 0.8,
        "evidence_anchor_count": 3,
        "proposed_type": "string",
    }
    payload.update(overrides)
    return ProposedField(**payload)  # type: ignore[arg-type]


def _proposal(**overrides: object) -> SchemaProposal:
    payload: dict[str, object] = {
        "id": "schema-proposal:run:1:doc:1",
        "proposal_ref": "proposal:run:1:hash",
        "source_document_ref": "normalized-doc:1",
        "proposed_fields": [_field()],
        "proposal_rationale_refs": ["rationale:anchor:1"],
        "replay_refs": ["run:1", "normalized-doc:1"],
    }
    payload.update(overrides)
    return SchemaProposal(**payload)  # type: ignore[arg-type]


# Test 1
def test_schema_proposal_rejects_blank_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="id"):
        _proposal(id="  ")


# Test 2
def test_schema_proposal_rejects_empty_proposed_fields() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposed_fields"):
        _proposal(proposed_fields=[])


# Test 3
def test_schema_proposal_rejects_blank_proposal_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposal_ref"):
        _proposal(proposal_ref=" ")


# Test 4
def test_proposed_field_rejects_confidence_above_one() -> None:
    with pytest.raises((ValidationError, ValueError), match="confidence"):
        _field(confidence=1.5)


# Test 5
def test_proposed_field_rejects_confidence_below_zero() -> None:
    with pytest.raises((ValidationError, ValueError), match="confidence"):
        _field(confidence=-0.1)


# Test 6
def test_proposed_field_rejects_blank_xpath() -> None:
    with pytest.raises((ValidationError, ValueError), match="xpath"):
        _field(xpath="  ")


# Test 7
def test_proposed_field_rejects_negative_evidence_anchor_count() -> None:
    with pytest.raises((ValidationError, ValueError), match="evidence_anchor_count"):
        _field(evidence_anchor_count=-1)


# Test 8
def test_proposed_field_rejects_invalid_proposed_type() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposed_type"):
        _field(proposed_type="boolean")


# Test 9
def test_schema_proposal_canonical_json_is_deterministic() -> None:
    a = _proposal()
    b = _proposal()
    assert a.canonical_json() == b.canonical_json()


# Test 9a
def test_schema_proposal_rejects_blank_source_document_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="source_document_ref"):
        _proposal(source_document_ref="  ")


# Test 9b
def test_schema_proposal_rejects_empty_proposal_rationale_refs() -> None:
    with pytest.raises((ValidationError, ValueError), match="proposal_rationale_refs"):
        _proposal(proposal_rationale_refs=[])


# Test 9c
def test_schema_proposal_rejects_blank_replay_refs_entry() -> None:
    with pytest.raises((ValidationError, ValueError), match="replay_refs"):
        _proposal(replay_refs=["run:1", "  "])


# Test 9d
def test_proposed_field_rejects_zero_evidence_anchor_count() -> None:
    with pytest.raises((ValidationError, ValueError), match="evidence_anchor_count"):
        _field(evidence_anchor_count=0)


# Bonus — read-model boundary
def test_normalized_document_read_model_rejects_empty_sample_refs() -> None:
    with pytest.raises((ValidationError, ValueError), match="text_sample_refs"):
        NormalizedDocumentReadModel(
            id="doc:1",
            normalized_document_ref="normalized-doc:1",
            text_sample_refs=[],
        )
