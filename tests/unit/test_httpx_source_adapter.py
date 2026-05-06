"""Tests for the httpx-backed StdlibHttpSourceAdapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    NetworkAdapterError,
    NetworkAdapterTimeoutError,
    StdlibHttpSourceAdapter,
    _parse_retry_after,
)
from veracrawl.contracts.enums import AdapterType, NetworkFailureType
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec


def _make_request(
    *,
    url: str = "https://example.test/path",
    timeout_ms: int = 30000,
) -> NetworkRequest:
    return NetworkRequest(
        id="network-request:test-001",
        run_ref="run:test",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:test:request",
        policy_decision_refs=["policy:test:network"],
        egress_policy_ref="policy:test:egress",
        private_network_policy_ref="policy:test:private",
        robots_policy_ref="policy:test:robots",
        rate_budget_ref="budget:test:rate",
        size_budget_bytes=1_000_000,
        timeout_ms=timeout_ms,
        idempotency_key="idem:test:network",
    )


def _command() -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:test-001",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref="https://example.test/path",
        policy_snapshot_ref="policy:test:network",
        deterministic_clock_ref="clock:test",
        randomness_seed_ref="random:test",
    )


def _build_adapter(
    *,
    handler: Any,
    config: HttpClientConfig | None = None,
    sleep_calls: list[float] | None = None,
    request: NetworkRequest | None = None,
) -> StdlibHttpSourceAdapter:
    transport = httpx.MockTransport(handler)
    sleep_log = sleep_calls if sleep_calls is not None else []

    def fake_sleep(seconds: float) -> None:
        sleep_log.append(seconds)

    return StdlibHttpSourceAdapter(
        request or _make_request(),
        config=config,
        transport=transport,
        sleep_fn=fake_sleep,
        jitter_fn=lambda: 0.0,
    )


# Module hygiene.


def test_module_does_not_use_urllib_for_transport() -> None:
    """urllib.request / urllib.error must be gone (transport layer).
    urllib.parse is stdlib URL helpers and is fine to keep using."""
    import veracrawl.adapters.network.stdlib_http as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "import urllib.request" not in content
    assert "import urllib.error" not in content
    assert "from urllib.request" not in content
    assert "from urllib.error" not in content


def test_default_user_agent_is_not_legacy_fixture_ua() -> None:
    config = HttpClientConfig()
    assert "VeraCrawl-local-fixture" not in config.user_agent
    assert "VeraCrawl-real-benchmark" not in config.user_agent


def test_default_user_agent_is_real_chrome() -> None:
    config = HttpClientConfig()
    assert "Chrome/" in config.user_agent
    assert "Mozilla/5.0" in config.user_agent
    assert "VeraCrawl" not in config.user_agent


# Backwards compat.


def test_single_arg_constructor_still_works() -> None:
    adapter = StdlibHttpSourceAdapter(_make_request())
    assert adapter.request.id == "network-request:test-001"


def test_legacy_value_error_handler_still_catches() -> None:
    """Existing acquisition layer ``except ValueError`` matches the new
    NetworkAdapterError because it inherits ValueError."""

    err = NetworkAdapterError(NetworkFailureType.NETWORK_TIMEOUT, "x")
    assert isinstance(err, ValueError)


# Happy path.


def test_successful_get_records_response_and_artifact() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(request.headers)
        return httpx.Response(200, text="<html>ok</html>", headers={"content-type": "text/html"})

    adapter = _build_adapter(handler=handler)
    result = adapter.execute(_command())
    assert result.status.value == "succeeded"
    assert adapter.last_result is not None
    assert adapter.last_result.body_text == "<html>ok</html>"
    assert adapter.last_result.response.status_code == 200
    # UA injected from config
    assert captured_headers["user-agent"].startswith("Mozilla/5.0")


# Retry on 429 / 5xx.


def test_retry_on_429_with_retry_after_seconds() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(429, text="", headers={"retry-after": "3"})
        return httpx.Response(200, text="ok", headers={"content-type": "text/plain"})

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    adapter.execute(_command())
    assert state["calls"] == 2
    assert sleep_log == [3.0]


def test_retry_on_5xx_with_exponential_backoff() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] < 3:
            return httpx.Response(503, text="")
        return httpx.Response(200, text="ok", headers={"content-type": "text/plain"})

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    adapter.execute(_command())
    # Two backoff sleeps with jitter=0: attempt 1 sleeps 1s, attempt 2 sleeps 2s.
    assert sleep_log == [1.0, 2.0]


def test_retry_after_capped_at_60s() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(429, text="", headers={"retry-after": "3600"})
        return httpx.Response(200, text="ok", headers={"content-type": "text/plain"})

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    adapter.execute(_command())
    assert sleep_log == [60.0]


def test_retry_exhaustion_raises_retry_exhausted() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="")

    adapter = _build_adapter(handler=handler, config=HttpClientConfig(max_attempts=3))
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.RETRY_EXHAUSTED


def test_fatal_4xx_does_not_retry_and_returns_response() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        return httpx.Response(403, text="forbidden", headers={"content-type": "text/plain"})

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    adapter.execute(_command())
    assert state["calls"] == 1
    assert sleep_log == []
    assert adapter.last_result is not None
    assert adapter.last_result.response.status_code == 403


# Per-hop redirect SSRF.


def test_redirect_protocol_downgrade_blocked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.scheme == "https":
            return httpx.Response(302, headers={"location": "http://example.test/path"})
        return httpx.Response(200, text="should-not-reach")

    adapter = _build_adapter(handler=handler)
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.REDIRECT_DENIED
    assert "downgrade" in exc_info.value.detail


def test_redirect_to_private_network_blocked_when_opt_in() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://127.0.0.1/admin"})

    config = HttpClientConfig(allow_private_network=False)
    adapter = _build_adapter(handler=handler, config=config)
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.PRIVATE_NETWORK_DENIED


def test_redirect_to_private_network_allowed_by_default() -> None:
    """Default config is backwards-compatible: localhost-based fixture
    tests need allow_private_network=True (the legacy behavior). Production
    callers must opt in to the strict mode via HttpClientConfig."""
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(302, headers={"location": "https://127.0.0.1/admin"})
        return httpx.Response(200, text="ok", headers={"content-type": "text/plain"})

    adapter = _build_adapter(handler=handler)
    adapter.execute(_command())
    assert state["calls"] == 2  # redirect followed


def test_redirect_off_allowlist_blocked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "example.test" in str(request.url):
            return httpx.Response(302, headers={"location": "https://attacker.test/x"})
        return httpx.Response(200, text="reached-attacker")

    config = HttpClientConfig(egress_allowlist=frozenset({"https://example.test"}))
    adapter = _build_adapter(handler=handler, config=config)
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.EGRESS_DENIED


def test_redirect_loop_caps_at_max_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Always redirect to a new URL, never resolve.
        n = int(str(request.url).rsplit("/", 1)[-1] or "0") + 1
        return httpx.Response(302, headers={"location": f"https://example.test/{n}"})

    config = HttpClientConfig(max_redirects=3)
    adapter = _build_adapter(
        handler=handler,
        config=config,
        request=_make_request(url="https://example.test/0"),
    )
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.REDIRECT_DENIED


def test_unsupported_redirect_scheme_blocked() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "ftp://example.test/file"})

    adapter = _build_adapter(handler=handler)
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.REDIRECT_DENIED


# Transport timeout.


def test_connect_timeout_classified_as_network_timeout() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated")

    adapter = _build_adapter(handler=handler, config=HttpClientConfig(max_attempts=1))
    with pytest.raises(NetworkAdapterError) as exc_info:
        adapter.execute(_command())
    assert exc_info.value.failure_type is NetworkFailureType.NETWORK_TIMEOUT


def test_network_adapter_timeout_error_backwards_compat() -> None:
    err = NetworkAdapterTimeoutError()
    assert isinstance(err, NetworkAdapterError)
    assert err.failure_type is NetworkFailureType.NETWORK_TIMEOUT


# Retry-After parser.


def test_parse_retry_after_seconds_and_http_date() -> None:
    assert _parse_retry_after("5") == 5.0
    when = datetime.now(UTC) + timedelta(seconds=10)
    raw = when.strftime("%a, %d %b %Y %H:%M:%S GMT")
    parsed = _parse_retry_after(raw)
    assert parsed is not None
    assert 5.0 <= parsed <= 15.0
    assert _parse_retry_after("not a date") is None
    assert _parse_retry_after(None) is None
