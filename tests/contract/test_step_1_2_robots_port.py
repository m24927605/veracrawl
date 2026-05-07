"""Contract tests for Phase 1 step 1.2 — ``RobotsPort``.

Step 1.2 introduces a hexagonal port for ``robots.txt`` enforcement
that the Phase 1 cooperative HTTP / browser paths consult before each
fetch and on every cross-origin redirect target. The default port
implementation is a no-op so existing tests keep passing without
configuration; the production default is ``UrllibRobotsParser``
(tested in ``test_step_1_2_urllib_robots_parser.py``).

The port deliberately exposes an ``evaluate`` method that returns a
combined :class:`RobotsAdvice` payload — ``is_allowed`` decides whether
the URL may be fetched at all, and ``crawl_delay`` / ``request_rate``
are the floor inputs Phase 1 step 1.3 ``RateLimiterPort`` will consume
(``floor = strictest of Retry-After / crawl_delay / request_rate``,
per design.md §4 Phase 1). Returning a single struct prevents callers
from forgetting one of the three signals; an unparsed crawl_delay /
request_rate is communicated as ``None``, never silently dropped.
"""

from __future__ import annotations

from veracrawl.ports.robots import (
    NoopRobotsPort,
    RobotsAdvice,
    RobotsPort,
)


def test_robots_advice_minimal_default_allows() -> None:
    advice = RobotsAdvice(is_allowed=True)
    assert advice.is_allowed is True
    assert advice.crawl_delay is None
    assert advice.request_rate is None


def test_robots_advice_carries_crawl_delay_and_rate() -> None:
    advice = RobotsAdvice(
        is_allowed=True,
        crawl_delay=2.0,
        request_rate=(1, 5),
    )
    assert advice.crawl_delay == 2.0
    assert advice.request_rate == (1, 5)


def test_robots_advice_disallow_carries_reason() -> None:
    advice = RobotsAdvice(
        is_allowed=False,
        disallow_reason="Disallow: /admin",
    )
    assert advice.is_allowed is False
    assert advice.disallow_reason == "Disallow: /admin"


def test_robots_advice_is_immutable() -> None:
    advice = RobotsAdvice(is_allowed=True)
    try:
        advice.is_allowed = False  # type: ignore[misc]
    except (AttributeError, Exception):  # noqa: BLE001
        return
    raise AssertionError("RobotsAdvice must be immutable / frozen")


def test_noop_robots_port_allows_every_url() -> None:
    port: RobotsPort = NoopRobotsPort()
    advice = port.evaluate("https://example.com/", user_agent="VeraCrawl/1")
    assert advice.is_allowed is True
    assert advice.crawl_delay is None
    assert advice.request_rate is None


def test_noop_robots_port_allows_arbitrary_user_agent() -> None:
    port: RobotsPort = NoopRobotsPort()
    advice_a = port.evaluate("https://example.com/", user_agent="*")
    advice_b = port.evaluate("https://example.com/", user_agent="GoogleBot")
    assert advice_a.is_allowed is True
    assert advice_b.is_allowed is True


def test_robots_port_protocol_satisfied_by_noop() -> None:
    """Static-style assertion that ``NoopRobotsPort`` implements ``RobotsPort``.

    The conformance check uses ``isinstance`` against a runtime-checkable
    Protocol — we want the default impl to be drop-in for any caller
    typed against the port (the design contract).
    """

    port = NoopRobotsPort()
    assert isinstance(port, RobotsPort)
