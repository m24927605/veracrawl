"""Phase 4 step 4.7 — calibration scaffolding contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veracrawl.adapters.calibration.identity import IdentityCalibrator
from veracrawl.adapters.calibration.platt import (
    PlattArtifactError,
    PlattCalibrator,
)
from veracrawl.contracts.calibration import CalibratedScore
from veracrawl.ports.calibration import CalibrationPort


def _write_artifact(
    path: Path, *, coefficients: dict[str, dict[str, float]]
) -> None:
    path.write_text(
        json.dumps({"coefficients": coefficients}), encoding="utf-8"
    )


# --- CalibratedScore validators --------------------------------------------


def test_calibrated_score_round_trip() -> None:
    score = CalibratedScore(
        id="calibrated-score:abc",
        raw_value=0.7,
        value=0.6,
        calibrator_id="platt",
        fit_artifact_ref="artifact:platt:v1",
    )
    assert score.value == 0.6


@pytest.mark.parametrize("bad", [-0.01, 1.01, float("nan"), float("inf")])
def test_calibrated_score_rejects_out_of_range_value(bad: float) -> None:
    with pytest.raises(ValueError):
        CalibratedScore(
            id="calibrated-score:abc",
            raw_value=0.5,
            value=bad,
            calibrator_id="identity",
        )


@pytest.mark.parametrize("bad", [-0.01, 1.01, float("nan"), float("inf")])
def test_calibrated_score_rejects_out_of_range_raw_value(bad: float) -> None:
    with pytest.raises(ValueError):
        CalibratedScore(
            id="calibrated-score:abc",
            raw_value=bad,
            value=0.5,
            calibrator_id="identity",
        )


def test_calibrated_score_rejects_blank_calibrator_id() -> None:
    with pytest.raises(ValueError):
        CalibratedScore(
            id="calibrated-score:abc",
            raw_value=0.5,
            value=0.5,
            calibrator_id="   ",
        )


def test_calibrated_score_rejects_blank_artifact_ref_when_present() -> None:
    with pytest.raises(ValueError):
        CalibratedScore(
            id="calibrated-score:abc",
            raw_value=0.5,
            value=0.5,
            calibrator_id="platt",
            fit_artifact_ref="   ",
        )


# --- IdentityCalibrator ----------------------------------------------------


def test_identity_calibrator_pass_through() -> None:
    calibrator = IdentityCalibrator()
    score = calibrator.calibrate(0.7, model_name="gpt-4o", field_name="price")
    assert score.value == 0.7
    assert score.raw_value == 0.7
    assert score.calibrator_id == "identity"
    assert score.fit_artifact_ref is None


def test_identity_calibrator_rejects_out_of_range() -> None:
    calibrator = IdentityCalibrator()
    with pytest.raises(ValueError):
        calibrator.calibrate(1.5, model_name="m", field_name="f")


def test_identity_calibrator_rejects_nan() -> None:
    calibrator = IdentityCalibrator()
    with pytest.raises(ValueError):
        calibrator.calibrate(float("nan"), model_name="m", field_name="f")


def test_identity_calibrator_runtime_checkable() -> None:
    assert isinstance(IdentityCalibrator(), CalibrationPort)


# --- PlattCalibrator -------------------------------------------------------


def test_platt_calibrator_applies_logistic(tmp_path: Path) -> None:
    """With (a=1.0, b=0.0), logistic(0.5) = 1 / (1 + e^-0.5) ≈ 0.622."""

    artifact = tmp_path / "platt.json"
    _write_artifact(
        artifact,
        coefficients={"gpt-4o::price": {"a": 1.0, "b": 0.0}},
    )
    calibrator = PlattCalibrator(
        fit_artifact_ref="artifact:platt:v1",
        artifact_path=artifact,
    )
    score = calibrator.calibrate(0.5, model_name="gpt-4o", field_name="price")
    assert 0.62 < score.value < 0.63
    assert score.raw_value == 0.5
    assert score.calibrator_id == "platt"


def test_platt_calibrator_handles_extreme_logit_clamp(tmp_path: Path) -> None:
    """Very large positive ``a`` should saturate to 1.0
    without overflowing math.exp."""

    artifact = tmp_path / "platt.json"
    _write_artifact(
        artifact,
        coefficients={"m::f": {"a": 1000.0, "b": 0.0}},
    )
    calibrator = PlattCalibrator(
        fit_artifact_ref="artifact:platt:v1",
        artifact_path=artifact,
    )
    score = calibrator.calibrate(0.9, model_name="m", field_name="f")
    assert score.value == 1.0


def test_platt_calibrator_handles_extreme_negative_logit(tmp_path: Path) -> None:
    artifact = tmp_path / "platt.json"
    _write_artifact(
        artifact,
        coefficients={"m::f": {"a": -1000.0, "b": 0.0}},
    )
    calibrator = PlattCalibrator(
        fit_artifact_ref="artifact:platt:v1",
        artifact_path=artifact,
    )
    score = calibrator.calibrate(0.9, model_name="m", field_name="f")
    assert score.value == 0.0


def test_platt_calibrator_missing_artifact_raises(tmp_path: Path) -> None:
    with pytest.raises(PlattArtifactError, match="does not exist"):
        PlattCalibrator(
            fit_artifact_ref="artifact:platt:v1",
            artifact_path=tmp_path / "missing.json",
        )


def test_platt_calibrator_invalid_json_raises(tmp_path: Path) -> None:
    artifact = tmp_path / "broken.json"
    artifact.write_text("not valid json", encoding="utf-8")
    with pytest.raises(PlattArtifactError, match="JSON is invalid"):
        PlattCalibrator(
            fit_artifact_ref="artifact:platt:v1",
            artifact_path=artifact,
        )


def test_platt_calibrator_missing_coefficients_raises(tmp_path: Path) -> None:
    artifact = tmp_path / "empty.json"
    artifact.write_text(json.dumps({"coefficients": {}}), encoding="utf-8")
    with pytest.raises(PlattArtifactError, match="contains no coefficients"):
        PlattCalibrator(
            fit_artifact_ref="artifact:platt:v1",
            artifact_path=artifact,
        )


def test_platt_calibrator_missing_field_for_pair_raises(tmp_path: Path) -> None:
    artifact = tmp_path / "platt.json"
    _write_artifact(
        artifact,
        coefficients={"m1::f1": {"a": 1.0, "b": 0.0}},
    )
    calibrator = PlattCalibrator(
        fit_artifact_ref="artifact:platt:v1",
        artifact_path=artifact,
    )
    with pytest.raises(PlattArtifactError, match="no Platt coefficients fitted"):
        calibrator.calibrate(0.5, model_name="m2", field_name="f1")


def test_platt_calibrator_blank_artifact_ref_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fit_artifact_ref"):
        PlattCalibrator(
            fit_artifact_ref="   ",
            artifact_path=tmp_path / "platt.json",
        )


def test_platt_calibrator_runtime_checkable(tmp_path: Path) -> None:
    artifact = tmp_path / "platt.json"
    _write_artifact(
        artifact,
        coefficients={"m::f": {"a": 1.0, "b": 0.0}},
    )
    calibrator = PlattCalibrator(
        fit_artifact_ref="artifact:platt:v1",
        artifact_path=artifact,
    )
    assert isinstance(calibrator, CalibrationPort)


def test_platt_calibrator_malformed_coefficient_key_raises(tmp_path: Path) -> None:
    artifact = tmp_path / "platt.json"
    artifact.write_text(
        json.dumps({"coefficients": {"no_separator_here": {"a": 1, "b": 0}}}),
        encoding="utf-8",
    )
    with pytest.raises(PlattArtifactError, match="model.*field"):
        PlattCalibrator(
            fit_artifact_ref="artifact:platt:v1",
            artifact_path=artifact,
        )


def test_platt_calibrator_non_finite_coefficient_raises(tmp_path: Path) -> None:
    artifact = tmp_path / "platt.json"
    artifact.write_text(
        json.dumps(
            {"coefficients": {"m::f": {"a": float("inf"), "b": 0}}}
        ),
        encoding="utf-8",
    )
    with pytest.raises(PlattArtifactError, match="finite"):
        PlattCalibrator(
            fit_artifact_ref="artifact:platt:v1",
            artifact_path=artifact,
        )
