"""Same-slice replay consumer for the s6 ``utc_clock`` source.

See ``docs/plans/general-purpose-crawler-agentification/
s6-runner-wires-graph-observation.md``. Pairs with the runner's
``clock_trace`` producer to close the AGENTS.md
"wire-consumer-in-same-slice" rule for new non-determinism.

Stdlib only — the import-boundary test forbids any veracrawl
runtime dependency.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ReplayingUtcClock:
    def __init__(self, *, utc_clock_ref: str, canned: list[datetime]) -> None:
        if not utc_clock_ref or not utc_clock_ref.strip():
            raise ValueError("utc_clock_ref must be non-blank")
        if not canned:
            raise ValueError("canned must not be empty")
        self._utc_clock_ref = utc_clock_ref
        self._canned = list(canned)
        self._cursor = 0

    @property
    def utc_clock_ref(self) -> str:
        return self._utc_clock_ref

    def __call__(self) -> datetime:
        if self._cursor >= len(self._canned):
            raise ValueError("ReplayingUtcClock exhausted")
        value = self._canned[self._cursor]
        self._cursor += 1
        return value


def replaying_utc_clock_from_run_report(
    run_report: dict[str, Any], utc_clock_ref: str,
) -> ReplayingUtcClock:
    if run_report.get("utc_clock_ref") != utc_clock_ref:
        raise ValueError(
            "replaying_utc_clock_from_run_report: utc_clock_ref must match "
            "run_report['utc_clock_ref']",
        )
    trace = run_report.get("clock_trace")
    if not trace:
        raise ValueError(
            "replaying_utc_clock_from_run_report: run_report['clock_trace'] missing or empty",
        )
    canned = [datetime.fromisoformat(s) for s in trace]
    return ReplayingUtcClock(utc_clock_ref=utc_clock_ref, canned=canned)
