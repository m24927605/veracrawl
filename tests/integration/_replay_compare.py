"""Compare helpers for s13 replay-invariant tests.

Strips inherently-wall-clock fields (``started_at``-class) from the
runner's ``dict`` run report before comparison so the narrowed
replay-invariant scope (graph events + plan_decision_* +
replay_consumer_ref) can be byte-compared without first having to
land the full ``_now()``-removal slice.
"""

from __future__ import annotations

import json
from typing import Any

# Fields whose values are inherently wall-clock and are explicitly
# OUT of the s13 replay-invariant scope per R2 reservation.
_WALL_CLOCK_FIELDS = frozenset({
    "started_at",
    "ended_at",
    "wall_clock_started_at",
    "wall_clock_ended_at",
    "frontier_events",  # carries occurred_at strings from wall clock
})


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    """Strip wall-clock fields so the remaining keys are replay-stable."""

    return {k: v for k, v in report.items() if k not in _WALL_CLOCK_FIELDS}


def canonical_json(report: dict[str, Any]) -> str:
    """Sort keys + serialize so reports can be byte-compared."""

    return json.dumps(normalize_report(report), sort_keys=True)


__all__ = ["canonical_json", "normalize_report"]
