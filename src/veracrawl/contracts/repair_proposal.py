"""``RepairProposal`` — per-field xpath repair suggestions for s8.

Produced by the ``RepairPort`` over a ``DriftReport`` plus a list of
``NormalizedDocumentReadModel`` samples (text via ``resolve_text``).
Carries one ``FieldRepair`` per drifted field with an alternative
xpath proposal.

Per R4 (s8 plan iter-5 reservation), ``repair_kind`` is a validated
string (rather than a StrEnum) so this slice stays inside the
≤ 300 LOC behavior cap. Allowed values: ``"anchor_reselect"``,
``"confidence_adjust"``, ``"type_relax"``.

See ``docs/plans/general-purpose-crawler-agentification/
s8-drift-repair-ports.md``.
"""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel

REPAIR_KINDS: frozenset[str] = frozenset({
    "anchor_reselect", "confidence_adjust", "type_relax",
})


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class FieldRepair(VeraModel):
    field_name: str
    original_xpath: str
    proposed_xpath: str
    confidence: float
    repair_kind: str

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.field_name.strip()), "field_name must be non-blank")
        _require(
            bool(self.original_xpath.strip()),
            "original_xpath must be non-blank",
        )
        _require(
            bool(self.proposed_xpath.strip()),
            "proposed_xpath must be non-blank",
        )
        _require(
            0.0 <= self.confidence <= 1.0,
            "confidence must be in [0.0, 1.0]",
        )
        _require(
            self.repair_kind in REPAIR_KINDS,
            f"repair_kind must be one of {sorted(REPAIR_KINDS)}",
        )


class RepairProposal(VeraModel):
    id: str
    run_ref: Ref
    drift_report_ref: Ref
    field_repairs: list[FieldRepair] = Field(default_factory=list)
    replay_refs: list[Ref] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.run_ref.strip()), "run_ref must be non-blank")
        _require(
            bool(self.drift_report_ref.strip()),
            "drift_report_ref must be non-blank",
        )
        _require(
            len(self.field_repairs) >= 1,
            "field_repairs must contain ≥ 1 entry",
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


__all__ = ["REPAIR_KINDS", "FieldRepair", "RepairProposal"]
