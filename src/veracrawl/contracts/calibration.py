"""Phase 4 step 4.7 — calibrated-confidence record contract.

A ``CalibratedScore`` is the result of running a raw LLM
self-reported confidence through the calibration layer. Each
``LLMFieldConfidence`` will reference one (Phase 5 ships the
wiring; Phase 4 step 4.7 ships the scoring contract).

Boundary invariants:

* ``value`` is in ``[0.0, 1.0]`` (calibrated probability).
* ``raw_value`` is in ``[0.0, 1.0]``.
* Both must be finite (NaN / Inf would slip past the bounds
  check and silently bypass downstream confidence
  thresholds).
"""

from __future__ import annotations

import math

from pydantic import model_validator

from veracrawl.contracts.common import Ref, TimestampedModel


def _ensure_non_blank(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-blank identifier")


def _ensure_finite_unit_interval(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0.0, 1.0]")


class CalibratedScore(TimestampedModel):
    """One calibrated confidence value with provenance."""

    id: str
    raw_value: float
    value: float
    calibrator_id: str
    fit_artifact_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_score(self) -> CalibratedScore:
        _ensure_non_blank("calibrated score id", self.id)
        _ensure_non_blank("calibrator_id", self.calibrator_id)
        _ensure_finite_unit_interval("raw_value", self.raw_value)
        _ensure_finite_unit_interval("value", self.value)
        if self.fit_artifact_ref is not None and not self.fit_artifact_ref.strip():
            raise ValueError(
                "fit_artifact_ref must be non-blank when present"
            )
        return self


__all__ = ["CalibratedScore"]
