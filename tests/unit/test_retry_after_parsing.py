"""Unit tests for the AIMD-feedback ``Retry-After`` parser."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from veracrawl.external_crawl.runner import _parse_retry_after


def _now() -> datetime:
    return datetime.now(tz=UTC)


def test_none_for_missing_header() -> None:
    assert _parse_retry_after(None) is None


def test_none_for_whitespace() -> None:
    assert _parse_retry_after("   ") is None


def test_seconds_integer() -> None:
    assert _parse_retry_after("30") == 30.0


def test_seconds_float() -> None:
    # RFC 7231 specifies integer seconds, but some servers emit fractional.
    # Accept the float so we don't drop them.
    assert _parse_retry_after("0.4") == pytest.approx(0.4)


def test_seconds_negative_returns_none() -> None:
    # A negative integer-seconds value is a malformed directive; treat
    # it as missing so the limiter falls back to its default cooldown.
    assert _parse_retry_after("-5") is None


def test_http_date_returns_seconds_until() -> None:
    # Build an HTTP-date 90 seconds in the future and check the parser
    # returns a value in [80, 100] (small slack for clock advance
    # between formatting and parsing).
    future = _now() + timedelta(seconds=90)
    http_date = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    parsed = _parse_retry_after(http_date)
    assert parsed is not None
    assert 80 <= parsed <= 100, f"expected ~90s, got {parsed}"


def test_http_date_in_past_returns_none() -> None:
    past = _now() - timedelta(seconds=120)
    http_date = past.strftime("%a, %d %b %Y %H:%M:%S GMT")
    # A past date means "retry immediately"; surface as None (no
    # cooldown) rather than 0 (which the limiter might treat as "wait
    # forever" via inf in some edge cases).
    assert _parse_retry_after(http_date) is None


def test_malformed_string_returns_none() -> None:
    assert _parse_retry_after("not a duration") is None


@pytest.mark.parametrize(
    "value",
    [
        "Wed, 21 Oct 2099 07:28:00 GMT",  # explicit future
        "Sun, 06 Nov 2099 08:49:37 GMT",
    ],
)
def test_known_future_http_dates_return_positive_seconds(value: str) -> None:
    parsed = _parse_retry_after(value)
    assert parsed is not None
    assert parsed > 0
