"""``ReplayBundle`` — canned non-determinism for s11 replay consumer.

Captures every external observation that needs to be reproduced
byte-for-byte during a replay run:

* ``clock_trace`` — every UTC datetime the recorded run observed
  (ISO 8601, ``+00:00`` suffix mandatory).
* ``model_response_refs`` — request_id → raw_response_ref.
* ``seed_refs`` — RNG seed name → integer.
* ``fetch_outcome_refs`` — composite key (url + host) →
  fetch_outcome_ref.

The producer (s12) assembles this from the runner's run-report-
equivalent state; the consumer (s11 adapter) reads it back through
``ReplayConsumerPort``. s13 wires the live byte-identical replay.

See ``docs/plans/general-purpose-crawler-agentification/
s11-replay-consumer-port.md``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _parse_iso_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"clock_trace entry {value!r} is not ISO 8601",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(
            f"clock_trace entry {value!r} must be UTC (offset +00:00)",
        )
    return parsed


class ReplayBundle(VeraModel):
    id: str
    run_ref: Ref
    recorded_at: datetime
    clock_trace: list[str] = Field(default_factory=list)
    model_response_refs: dict[str, Ref] = Field(default_factory=dict)
    seed_refs: dict[str, int] = Field(default_factory=dict)
    fetch_outcome_refs: dict[str, Ref] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.run_ref.strip()), "run_ref must be non-blank")
        _require(
            self.recorded_at.tzinfo is not None
            and self.recorded_at.utcoffset() == UTC.utcoffset(self.recorded_at),
            "recorded_at must be UTC",
        )
        _require(
            len(self.clock_trace) >= 1,
            "clock_trace must contain ≥ 1 entry",
        )
        for entry in self.clock_trace:
            _parse_iso_utc(entry)  # raises ValueError on bad shape
        for key, ref in self.model_response_refs.items():
            _require(
                bool(key.strip()),
                "model_response_refs keys must be non-blank",
            )
            _require(
                bool(ref.strip()),
                f"model_response_refs[{key!r}] must be non-blank",
            )
        for name, seed in self.seed_refs.items():
            _require(
                bool(name.strip()),
                "seed_refs keys must be non-blank",
            )
            _require(seed >= 0, f"seed_refs[{name!r}] must be ≥ 0")
        for key, ref in self.fetch_outcome_refs.items():
            _require(
                bool(key.strip()),
                "fetch_outcome_refs keys must be non-blank",
            )
            _require(
                bool(ref.strip()),
                f"fetch_outcome_refs[{key!r}] must be non-blank",
            )


__all__ = ["ReplayBundle"]
