"""Unit tests for ``ReplayingUtcClock`` (s6 tests 20, 20a).

See ``docs/plans/general-purpose-crawler-agentification/
s6-runner-wires-graph-observation.md``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from veracrawl.adapters.clocks.replaying_utc_clock import (
    ReplayingUtcClock,
    replaying_utc_clock_from_run_report,
)

_T0 = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
_T1 = datetime(2026, 5, 14, 12, 0, 1, tzinfo=UTC)
_T2 = datetime(2026, 5, 14, 12, 0, 2, tzinfo=UTC)


# Test 20
def test_replaying_utc_clock_returns_canned_datetimes_in_order() -> None:
    clock = ReplayingUtcClock(utc_clock_ref="utc-clock:fixture:1", canned=[_T0, _T1, _T2])
    assert clock() == _T0
    assert clock() == _T1
    assert clock() == _T2
    with pytest.raises(ValueError, match="ReplayingUtcClock exhausted"):
        clock()


# Test 20a
def test_replaying_utc_clock_rejects_blank_ref_and_empty_canned() -> None:
    with pytest.raises(ValueError, match="utc_clock_ref"):
        ReplayingUtcClock(utc_clock_ref="", canned=[_T0])
    with pytest.raises(ValueError, match="canned"):
        ReplayingUtcClock(utc_clock_ref="utc-clock:fixture:1", canned=[])


# Helper tests — replaying_utc_clock_from_run_report
def test_helper_round_trips_clock_trace() -> None:
    report = {
        "utc_clock_ref": "utc-clock:fixture:rt",
        "clock_trace": [_T0.isoformat(), _T1.isoformat(), _T2.isoformat()],
    }
    clock = replaying_utc_clock_from_run_report(report, "utc-clock:fixture:rt")
    assert clock() == _T0
    assert clock() == _T1
    assert clock() == _T2
    assert clock.utc_clock_ref == "utc-clock:fixture:rt"


def test_helper_rejects_mismatched_ref() -> None:
    report = {
        "utc_clock_ref": "utc-clock:fixture:a",
        "clock_trace": [_T0.isoformat()],
    }
    with pytest.raises(ValueError, match="utc_clock_ref must match"):
        replaying_utc_clock_from_run_report(report, "utc-clock:fixture:b")


def test_helper_rejects_missing_or_empty_clock_trace() -> None:
    report_missing = {"utc_clock_ref": "utc-clock:fixture:m"}
    with pytest.raises(ValueError, match="clock_trace"):
        replaying_utc_clock_from_run_report(report_missing, "utc-clock:fixture:m")
    report_none = {"utc_clock_ref": "utc-clock:fixture:m", "clock_trace": None}
    with pytest.raises(ValueError, match="clock_trace"):
        replaying_utc_clock_from_run_report(report_none, "utc-clock:fixture:m")
    report_empty = {"utc_clock_ref": "utc-clock:fixture:m", "clock_trace": []}
    with pytest.raises(ValueError, match="clock_trace"):
        replaying_utc_clock_from_run_report(report_empty, "utc-clock:fixture:m")
