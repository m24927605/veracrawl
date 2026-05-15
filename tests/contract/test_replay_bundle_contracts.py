"""Contract tests for s11 ``ReplayBundle``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from veracrawl.contracts.replay_bundle import ReplayBundle

_T = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def _bundle(**overrides: object) -> ReplayBundle:
    payload: dict[str, object] = {
        "id": "bundle:run-1:1",
        "run_ref": "run:1",
        "recorded_at": _T,
        "clock_trace": ["2026-05-15T12:00:00+00:00"],
        "model_response_refs": {"req:1": "raw:1"},
        "seed_refs": {"dispatch": 42},
        "fetch_outcome_refs": {"https://a.example/1": "fetch:1"},
    }
    payload.update(overrides)
    return ReplayBundle(**payload)  # type: ignore[arg-type]


def test_replay_bundle_rejects_blank_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="id"):
        _bundle(id=" ")


def test_replay_bundle_rejects_blank_run_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="run_ref"):
        _bundle(run_ref=" ")


def test_replay_bundle_rejects_naive_recorded_at() -> None:
    with pytest.raises((ValidationError, ValueError), match="recorded_at"):
        _bundle(recorded_at=datetime(2026, 5, 15, 12, 0))


def test_replay_bundle_rejects_aware_non_utc_recorded_at() -> None:
    with pytest.raises((ValidationError, ValueError), match="recorded_at"):
        _bundle(recorded_at=datetime(
            2026, 5, 15, 12, 0, tzinfo=timezone(timedelta(hours=8)),
        ))


def test_replay_bundle_rejects_non_iso_clock_trace_entry() -> None:
    with pytest.raises((ValidationError, ValueError), match="clock_trace"):
        _bundle(clock_trace=["not-iso"])


def test_replay_bundle_rejects_empty_clock_trace() -> None:
    with pytest.raises((ValidationError, ValueError), match="clock_trace"):
        _bundle(clock_trace=[])


def test_replay_bundle_rejects_blank_model_response_ref_value() -> None:
    with pytest.raises((ValidationError, ValueError), match="model_response_refs"):
        _bundle(model_response_refs={"req:1": " "})


def test_replay_bundle_rejects_negative_seed_value() -> None:
    with pytest.raises((ValidationError, ValueError), match="seed_refs"):
        _bundle(seed_refs={"dispatch": -1})


def test_replay_bundle_canonical_json_is_deterministic() -> None:
    assert _bundle().canonical_json() == _bundle().canonical_json()


def test_replay_bundle_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ReplayBundle(  # type: ignore[call-arg]
            id="b:1", run_ref="run:1", recorded_at=_T,
            clock_trace=["2026-05-15T12:00:00+00:00"],
            model_response_refs={}, seed_refs={}, fetch_outcome_refs={},
            unknown_field="boom",
        )


def test_replay_bundle_rejects_clock_trace_with_aware_non_utc() -> None:
    with pytest.raises((ValidationError, ValueError), match="clock_trace"):
        _bundle(clock_trace=["2026-05-15T12:00:00+08:00"])
