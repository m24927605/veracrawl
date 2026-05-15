"""``SchemaProposal`` + ``ProposedField`` — s7 extraction-strategy output.

A schema proposal is the open-schema discovery output: given a
normalized document (via ``NormalizedDocumentReadModel``), the
strategy emits a list of candidate fields with xpaths, confidence,
and evidence counts. The proposal carries ref-only provenance
(``source_document_ref``, ``proposal_rationale_refs``,
``replay_refs``) so downstream consumers (s8 drift detection, s10
runtime) can re-derive everything from the bundle.

See ``docs/plans/general-purpose-crawler-agentification/
s7-extraction-strategy-port.md``.
"""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel

PROPOSED_TYPES: frozenset[str] = frozenset({"string", "number", "date", "url"})


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class ProposedField(VeraModel):
    name: str
    xpath: str
    confidence: float
    evidence_anchor_count: int
    proposed_type: str

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.name.strip()), "name must be non-blank")
        _require(bool(self.xpath.strip()), "xpath must be non-blank")
        _require(
            0.0 <= self.confidence <= 1.0,
            "confidence must be in [0.0, 1.0]",
        )
        _require(
            self.evidence_anchor_count >= 1,
            "evidence_anchor_count must be ≥ 1",
        )
        _require(
            self.proposed_type in PROPOSED_TYPES,
            f"proposed_type must be one of {sorted(PROPOSED_TYPES)}",
        )


class SchemaProposal(VeraModel):
    id: str
    proposal_ref: Ref
    source_document_ref: Ref
    proposed_fields: list[ProposedField] = Field(default_factory=list)
    proposal_rationale_refs: list[Ref] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(
            bool(self.proposal_ref.strip()),
            "proposal_ref must be non-blank",
        )
        _require(
            bool(self.source_document_ref.strip()),
            "source_document_ref must be non-blank",
        )
        _require(
            len(self.proposed_fields) >= 1,
            "proposed_fields must contain ≥ 1 entry",
        )
        _require(
            len(self.proposal_rationale_refs) >= 1,
            "proposal_rationale_refs must contain ≥ 1 ref",
        )
        for ref in self.proposal_rationale_refs:
            _require(
                bool(ref.strip()),
                "proposal_rationale_refs entries must be non-blank",
            )
        _require(
            len(self.replay_refs) >= 1,
            "replay_refs must contain ≥ 1 ref",
        )
        for ref in self.replay_refs:
            _require(
                bool(ref.strip()),
                "replay_refs entries must be non-blank",
            )


__all__ = ["PROPOSED_TYPES", "ProposedField", "SchemaProposal"]
