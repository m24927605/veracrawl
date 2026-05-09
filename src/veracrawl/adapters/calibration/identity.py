"""Phase 4 step 4.7 — identity (pass-through) calibrator."""

from __future__ import annotations

import math
import uuid

from veracrawl.contracts.calibration import CalibratedScore


class IdentityCalibrator:
    """Pass-through calibrator. ``value == raw_value``.

    The Phase 4 default. Lets all Phase 4 / 5 flows run
    without waiting for the gold corpus + fit artifact that
    Phase 6 step 6.5 ships. Production deployments will swap
    this for :class:`PlattCalibrator` once the artifact lands.
    """

    calibrator_id = "identity"

    def calibrate(
        self,
        raw_score: float,
        *,
        model_name: str,
        field_name: str,
    ) -> CalibratedScore:
        if not math.isfinite(raw_score):
            raise ValueError("raw_score must be a finite number")
        if not 0.0 <= raw_score <= 1.0:
            raise ValueError("raw_score must be in [0.0, 1.0]")
        if not model_name or not model_name.strip():
            raise ValueError("model_name must be non-blank")
        if not field_name or not field_name.strip():
            raise ValueError("field_name must be non-blank")
        return CalibratedScore(
            id=f"calibrated-score:{uuid.uuid4().hex}",
            raw_value=raw_score,
            value=raw_score,
            calibrator_id=self.calibrator_id,
            fit_artifact_ref=None,
        )


__all__ = ["IdentityCalibrator"]
