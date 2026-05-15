"""``DriftReport`` — per-field missing-rate aggregation for s8.

Produced by the ``DriftDetectionPort`` over a list of
``ExtractionOutcome``s. A field is "drifted" when its missing rate
exceeds ``drift_threshold`` (default 0.30, configurable per call).

See ``docs/plans/general-purpose-crawler-agentification/
s8-drift-repair-ports.md``.
"""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class DriftReport(VeraModel):
    id: str
    run_ref: Ref
    proposal_ref: Ref
    pages_evaluated: int
    field_missing_rates: dict[str, float]
    drifted_fields: list[str] = Field(default_factory=list)
    drift_threshold: float = 0.30
    replay_refs: list[Ref] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.run_ref.strip()), "run_ref must be non-blank")
        _require(
            bool(self.proposal_ref.strip()),
            "proposal_ref must be non-blank",
        )
        _require(
            self.pages_evaluated >= 1,
            "pages_evaluated must be ≥ 1",
        )
        _require(
            0.0 < self.drift_threshold < 1.0,
            "drift_threshold must be in (0.0, 1.0)",
        )
        for name, rate in self.field_missing_rates.items():
            _require(
                bool(name.strip()),
                "field_missing_rates keys must be non-blank",
            )
            _require(
                0.0 <= rate <= 1.0,
                f"field_missing_rates[{name!r}] must be in [0.0, 1.0]",
            )
        known = set(self.field_missing_rates.keys())
        for drifted in self.drifted_fields:
            _require(
                drifted in known,
                f"drifted_fields contains {drifted!r} "
                f"absent from field_missing_rates",
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


__all__ = ["DriftReport"]
