"""Phase 4 step 4.7 — Platt-scaling calibrator (apply path).

Phase 4 ships the apply path: given a fitted ``(a, b)``
artifact, applies ``calibrated = 1 / (1 + exp(-(a * raw + b)))``
to translate raw LLM confidence into a calibrated probability.

Phase 6 step 6.5 owns the fit path: training the ``(a, b)``
coefficients on the gold corpus.

Until the artifact lands, ``PlattCalibrator`` constructed
without an artifact ref raises at construction so callers
get a clear "fit not yet available" signal instead of a
silent zero-output.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path

from veracrawl.contracts.calibration import CalibratedScore
from veracrawl.contracts.common import Ref


class PlattArtifactError(ValueError):
    """Raised when the Platt artifact is missing, malformed, or
    the requested ``(model_name, field_name)`` pair has no
    fitted coefficients."""


class PlattCalibrator:
    """Platt-scaling calibrator (apply path only — Phase 4)."""

    calibrator_id = "platt"

    def __init__(self, *, fit_artifact_ref: Ref, artifact_path: Path | str) -> None:
        if not fit_artifact_ref or not fit_artifact_ref.strip():
            raise ValueError("fit_artifact_ref must be non-blank")
        resolved = Path(artifact_path).resolve(strict=False)
        if not resolved.exists():
            raise PlattArtifactError(
                f"Platt fit artifact does not exist: {resolved!r}"
            )
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PlattArtifactError("Platt fit artifact JSON is invalid") from exc
        if not isinstance(payload, dict):
            raise PlattArtifactError(
                "Platt fit artifact must be a JSON object"
            )
        coefficients = payload.get("coefficients")
        if not isinstance(coefficients, dict):
            raise PlattArtifactError(
                "Platt fit artifact missing 'coefficients' object"
            )
        # Validate every entry up front so a typo'd ref
        # surfaces at load time, not first-use.
        validated: dict[tuple[str, str], tuple[float, float]] = {}
        for key, entry in coefficients.items():
            if "::" not in key:
                raise PlattArtifactError(
                    "coefficient keys must be '<model>::<field>'"
                )
            model_name, _, field_name = key.partition("::")
            if not isinstance(entry, dict):
                raise PlattArtifactError(
                    f"coefficient entry for {key!r} must be an object"
                )
            a = entry.get("a")
            b = entry.get("b")
            if not isinstance(a, (int, float)) or isinstance(a, bool):
                raise PlattArtifactError(
                    f"coefficient 'a' for {key!r} must be a number"
                )
            if not isinstance(b, (int, float)) or isinstance(b, bool):
                raise PlattArtifactError(
                    f"coefficient 'b' for {key!r} must be a number"
                )
            if not (math.isfinite(a) and math.isfinite(b)):
                raise PlattArtifactError(
                    f"coefficients for {key!r} must be finite"
                )
            validated[(model_name, field_name)] = (float(a), float(b))
        if not validated:
            raise PlattArtifactError(
                "Platt fit artifact contains no coefficients"
            )
        self._fit_artifact_ref = fit_artifact_ref
        self._coefficients = validated

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
        coefficients = self._coefficients.get((model_name, field_name))
        if coefficients is None:
            raise PlattArtifactError(
                f"no Platt coefficients fitted for "
                f"({model_name!r}, {field_name!r}) — Phase 6 step 6.5 "
                f"corpus authoring is responsible"
            )
        a, b = coefficients
        # Logistic: 1 / (1 + exp(-(a * raw + b)))
        # Clamp the logit to avoid overflow on extreme inputs.
        logit = a * raw_score + b
        # math.exp can overflow for large negative arguments
        # producing 0 (which is fine), but large positive
        # arguments produce inf; clamp logit to a safe range.
        if logit > 50.0:
            calibrated = 1.0
        elif logit < -50.0:
            calibrated = 0.0
        else:
            calibrated = 1.0 / (1.0 + math.exp(-logit))
        return CalibratedScore(
            id=f"calibrated-score:{uuid.uuid4().hex}",
            raw_value=raw_score,
            value=calibrated,
            calibrator_id=self.calibrator_id,
            fit_artifact_ref=self._fit_artifact_ref,
        )


__all__ = ["PlattCalibrator", "PlattArtifactError"]
