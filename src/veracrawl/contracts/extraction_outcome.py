"""``ExtractionOutcome`` — per-page extraction result for s8 drift detection.

Records, for one fetched page, which proposed fields the extractor
hit vs missed. The s8 drift detector aggregates many outcomes into
per-field missing rates; the s8 repair port consumes the resulting
``DriftReport``.

See ``docs/plans/general-purpose-crawler-agentification/
s8-drift-repair-ports.md``.
"""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class ExtractionOutcome(VeraModel):
    id: str
    run_ref: Ref
    page_canonical_url: str
    field_outcomes: dict[str, bool]
    replay_refs: list[Ref] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.run_ref.strip()), "run_ref must be non-blank")
        _require(
            bool(self.page_canonical_url.strip()),
            "page_canonical_url must be non-blank",
        )
        _require(
            len(self.field_outcomes) >= 1,
            "field_outcomes must contain ≥ 1 entry",
        )
        for name in self.field_outcomes:
            _require(
                bool(name.strip()),
                "field_outcomes keys must be non-blank",
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


__all__ = ["ExtractionOutcome"]
