"""Phase 4 step 4.7 — confidence-calibration port.

The schema runtime (Phase 4 step 4.6) calls
``CalibrationPort.calibrate`` with the LLM's raw self-reported
per-field confidence; the port returns a
``CalibratedScore``. Phase 5's recovery layer dispatches on
``CalibratedScore.value`` for abstention thresholds, so the
calibration layer determines when "the model said 0.9 but
historically that is only 0.6 accurate" gets surfaced
honestly.

Phase 4 step 4.7 ships:

* :class:`IdentityCalibrator` — pass-through. Default for
  Phase 4 because the gold corpus + fit artifact land in
  Phase 6 step 6.5; a no-op calibrator lets all of Phase 4 /
  5 run without waiting for the corpus.
* :class:`PlattCalibrator` — shell that loads a fitted
  artifact (logistic-regression coefficients) and applies
  ``1 / (1 + exp(-(a * raw + b)))``. Phase 4 ships the apply
  path; Phase 6 step 6.5 ships the fit path + the actual
  artifact.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.calibration import CalibratedScore


@runtime_checkable
class CalibrationPort(Protocol):
    """Translate a raw LLM confidence into a calibrated score."""

    def calibrate(
        self,
        raw_score: float,
        *,
        model_name: str,
        field_name: str,
    ) -> CalibratedScore:
        """Return a ``CalibratedScore`` for the raw value.

        ``model_name`` and ``field_name`` are pinned on the
        returned record so the recovery layer can dispatch on
        per-(model, field) calibration history. Implementations
        must raise ``ValueError`` for ``raw_score`` outside
        ``[0.0, 1.0]`` or non-finite — adapters are responsible
        for surfacing typed errors that downstream code can
        catch without inspecting message strings.
        """

        ...


__all__ = ["CalibrationPort"]
