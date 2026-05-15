"""``AnchorFrequencyDriftDetector`` — deterministic s8.b fixture adapter.

Aggregates ``ExtractionOutcome.field_outcomes`` over a corpus; emits a
``DriftReport`` with per-field missing rates and the set of fields
above the threshold. Pure function — no clock, no RNG.

See ``docs/plans/general-purpose-crawler-agentification/
s8-drift-repair-ports.md`` (s8.b scope).
"""

from __future__ import annotations

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.schema_proposal import SchemaProposal


class AnchorFrequencyDriftDetector:
    """``DriftDetectionPort`` impl using anchor-success aggregation."""

    def __init__(self, *, drift_threshold: float = 0.30) -> None:
        if not 0.0 < drift_threshold < 1.0:
            raise ValueError("drift_threshold must be in (0.0, 1.0)")
        self._drift_threshold = drift_threshold

    def detect(
        self,
        *,
        proposal: SchemaProposal,
        extraction_outcomes: list[ExtractionOutcome],
        run_ref: Ref,
    ) -> DriftReport:
        if not extraction_outcomes:
            raise ValueError("extraction_outcomes must be non-empty")
        proposed_names = [f.name for f in proposal.proposed_fields]
        totals: dict[str, int] = {n: 0 for n in proposed_names}
        misses: dict[str, int] = {n: 0 for n in proposed_names}
        for outcome in extraction_outcomes:
            for name in proposed_names:
                if name in outcome.field_outcomes:
                    totals[name] += 1
                    if not outcome.field_outcomes[name]:
                        misses[name] += 1
        rates: dict[str, float] = {}
        for name in proposed_names:
            denom = totals[name]
            rates[name] = (misses[name] / denom) if denom > 0 else 1.0
        drifted = [n for n in proposed_names if rates[n] > self._drift_threshold]
        digest = stable_hash({
            "proposal": proposal.proposal_ref,
            "rates": rates,
            "threshold": self._drift_threshold,
        })
        return DriftReport(
            id=f"drift-report:{run_ref}:{digest}",
            run_ref=run_ref,
            proposal_ref=proposal.proposal_ref,
            pages_evaluated=len(extraction_outcomes),
            field_missing_rates=rates,
            drifted_fields=drifted,
            drift_threshold=self._drift_threshold,
            replay_refs=[
                run_ref,
                proposal.proposal_ref,
                "adapter:anchor-frequency-drift:v1",
            ],
        )


__all__ = ["AnchorFrequencyDriftDetector"]
