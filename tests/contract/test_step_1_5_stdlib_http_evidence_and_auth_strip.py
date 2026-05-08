"""Contract tests for Phase 1 step 1.5 — per-attempt evidence,
cross-redirect Authorization strip, conditional fetch, cookie jar
wiring in ``StdlibHttpSourceAdapter``.

design.md §4 Phase 1 step 1.5 acceptance criteria:
* Cross-redirect Authorization stripping: original request has
  ``Authorization: Bearer x``; redirect to different origin records
  hop in evidence with header **stripped**.
* Conditional-fetch: second fetch with valid ETag yields 304 and
  reuses prior body artifact_ref.
* Per-attempt ``NetworkAttemptEvidence`` populated on
  ``NetworkClientResult.attempt_evidences``.

Boundary acceptance: existing tests must keep passing without
configuration. Defaults are :class:`NoopConditionalCache` and
:class:`NoopCookieJar`.
"""

from __future__ import annotations

import httpx
import pytest

from veracrawl.adapters.network.in_memory_conditional_cache import (
    InMemoryConditionalCache,
)
from veracrawl.adapters.network.in_memory_cookie_jar import InMemoryCookieJar
from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    StdlibHttpSourceAdapter,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec


def _make_request(url: str = "https://a.test/p/1") -> NetworkRequest:
    return NetworkRequest(
        id="network-request:step-1-5",
        run_ref="run:fixture",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:step-1-5:request",
        policy_decision_refs=["policy:fixture:default"],
        egress_policy_ref="policy:fixture:egress",
        private_network_policy_ref="policy:fixture:private-network",
        robots_policy_ref="policy:fixture:robots",
        rate_budget_ref="rate:fixture:default",
        size_budget_bytes=1_000_000,
        timeout_ms=10_000,
        idempotency_key="idem:step-1-5",
    )


def _make_command() -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:step-1-5",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref="https://a.test/p/1",
        policy_snapshot_ref="policy:fixture:default",
        deterministic_clock_ref="clock:fixture",
        randomness_seed_ref="random:fixture",
    )


def _ok_transport(body: str = "<html>ok</html>", **headers: str) -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        h = {"content-type": "text/html"}
        h.update(headers)
        return httpx.Response(200, content=body.encode("utf-8"), headers=h)

    return httpx.MockTransport(_handler)


# -- Per-attempt evidence -------------------------------------------------


def test_attempt_evidence_populated_on_successful_fetch() -> None:
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    assert len(result.attempt_evidences) == 1
    ev = result.attempt_evidences[0]
    assert ev.request_method == "GET"
    assert ev.request_url == "https://a.test/p/1"
    assert ev.response_status == 200
    assert ev.attempt_number == 1
    assert ev.failure_class is None


def test_attempt_evidence_populated_per_redirect_hop() -> None:
    """Each redirect hop is a separate HTTP attempt → its own evidence."""

    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://a.test/p/1":
            return httpx.Response(
                301,
                headers={"location": "https://a.test/p/2", "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>final</html>", headers={"content-type": "text/html"}
        )

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(),
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    assert len(result.attempt_evidences) == 2  # initial + redirect


def test_attempt_evidence_redirect_hop_count_increments() -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://a.test/p/1":
            return httpx.Response(
                302,
                headers={"location": "https://a.test/p/2", "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(),
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    # First evidence: redirect_hop_count=0; second: 1.
    assert result.attempt_evidences[0].redirect_hop_count == 0
    assert result.attempt_evidences[1].redirect_hop_count == 1


def test_attempt_evidence_redacts_authorization_header() -> None:
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(extra_headers={"Authorization": "Bearer SECRET_77"}),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    ev = result.attempt_evidences[0]
    auth_value = ev.request_headers_redacted.get("Authorization")
    assert auth_value == "[REDACTED]"
    assert "SECRET_77" not in str(ev.request_headers_redacted)


# -- Cross-redirect authorization strip ---------------------------------


def test_authorization_stripped_on_cross_origin_redirect() -> None:
    """Acceptance: original request has Authorization: Bearer x; redirect
    to different origin records hop in evidence with header stripped."""

    captured_headers: list[dict[str, str]] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        url = str(request.url)
        if url == "https://a.test/p/1":
            return httpx.Response(
                301,
                headers={"location": "https://b.test/q", "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    adapter = StdlibHttpSourceAdapter(
        _make_request("https://a.test/p/1"),
        config=HttpClientConfig(extra_headers={"Authorization": "Bearer XYZ_TOKEN"}),
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    # First request to a.test carries Authorization.
    assert captured_headers[0].get("authorization") == "Bearer XYZ_TOKEN"
    # Cross-origin redirect to b.test: Authorization stripped.
    assert "authorization" not in captured_headers[1]
    # Evidence for the cross-origin hop also has the header redacted /
    # absent.
    result = adapter.last_result
    assert result is not None
    cross_hop_ev = result.attempt_evidences[1]
    assert "Authorization" not in cross_hop_ev.request_headers_redacted


def test_authorization_kept_on_same_origin_redirect() -> None:
    captured_headers: list[dict[str, str]] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        url = str(request.url)
        if url == "https://a.test/p/1":
            return httpx.Response(
                302,
                headers={"location": "https://a.test/p/2", "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    adapter = StdlibHttpSourceAdapter(
        _make_request("https://a.test/p/1"),
        config=HttpClientConfig(extra_headers={"Authorization": "Bearer KEEP_ME"}),
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    # Both requests still carry Authorization (same-origin redirect).
    assert captured_headers[0].get("authorization") == "Bearer KEEP_ME"
    assert captured_headers[1].get("authorization") == "Bearer KEEP_ME"


def test_authorization_stripped_on_scheme_change() -> None:
    """https → http redirect (cross-origin) strips Authorization. Note:
    the existing protocol_downgrade check would reject this; use
    http → https redirect instead which is allowed and IS cross-origin."""

    captured_headers: list[dict[str, str]] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        url = str(request.url)
        if url == "http://a.test/p/1":
            return httpx.Response(
                301,
                headers={"location": "https://a.test/p/2", "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    adapter = StdlibHttpSourceAdapter(
        _make_request("http://a.test/p/1"),
        config=HttpClientConfig(
            extra_headers={"Authorization": "Bearer SCHEMECHANGE"},
            allow_private_network=True,
        ),
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    assert captured_headers[0].get("authorization") == "Bearer SCHEMECHANGE"
    assert "authorization" not in captured_headers[1]


# -- Conditional fetch (304 short-circuit) ------------------------------


def test_conditional_fetch_caches_etag_and_replays_if_none_match() -> None:
    cache = InMemoryConditionalCache()
    captured_headers: list[dict[str, str]] = []
    request_count: list[int] = [0]

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        request_count[0] += 1
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304, headers={"etag": '"v1"', "content-type": "text/html"})
        return httpx.Response(
            200,
            content=b"<html>cached-body</html>",
            headers={
                "etag": '"v1"',
                "content-type": "text/html",
            },
        )

    config = HttpClientConfig(conditional_cache=cache, run_ref="run:cond")
    # First fetch: no cache → 200 with ETag.
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    )
    adapter.execute(_make_command())
    assert "if-none-match" not in captured_headers[0]
    first_body = adapter.last_result.body_text  # type: ignore[union-attr]
    assert "cached-body" in first_body

    # Second fetch with same adapter → If-None-Match attached → 304 →
    # short-circuit returns cached body.
    adapter2 = StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    )
    adapter2.execute(_make_command())
    assert captured_headers[1].get("if-none-match") == '"v1"'
    assert request_count[0] == 2
    second_body = adapter2.last_result.body_text  # type: ignore[union-attr]
    assert "cached-body" in second_body


def test_conditional_fetch_uses_last_modified_when_no_etag() -> None:
    cache = InMemoryConditionalCache()
    captured_headers: list[dict[str, str]] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        return httpx.Response(
            200,
            content=b"<html>x</html>",
            headers={
                "last-modified": "Wed, 21 Oct 2026 07:28:00 GMT",
                "content-type": "text/html",
            },
        )

    config = HttpClientConfig(conditional_cache=cache, run_ref="run:cond2")
    StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    ).execute(_make_command())
    StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    ).execute(_make_command())
    assert captured_headers[1].get("if-modified-since") == "Wed, 21 Oct 2026 07:28:00 GMT"


def test_304_with_no_cached_body_raises_adapter_failure() -> None:
    """Server returns 304 but we have nothing in the cache → fail closed
    (cannot synthesize a body from thin air)."""

    cache = InMemoryConditionalCache()

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(304, headers={"content-type": "text/plain"})

    from veracrawl.adapters.network.stdlib_http import AdapterFailureError

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(conditional_cache=cache, run_ref="run:cond3"),
        transport=httpx.MockTransport(_handler),
    )
    with pytest.raises(AdapterFailureError):
        adapter.execute(_make_command())


# -- Cookie jar wiring --------------------------------------------------


def test_cookie_jar_replays_set_cookie_on_subsequent_request() -> None:
    jar = InMemoryCookieJar()
    captured_headers: list[dict[str, str]] = []
    flip = [False]

    def _handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        if not flip[0]:
            flip[0] = True
            return httpx.Response(
                200,
                content=b"<html>first</html>",
                headers={
                    "set-cookie": "session=abc; Path=/",
                    "content-type": "text/html",
                },
            )
        return httpx.Response(
            200, content=b"<html>second</html>", headers={"content-type": "text/html"}
        )

    config = HttpClientConfig(cookie_jar=jar, run_ref="run:jar")
    StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    ).execute(_make_command())
    StdlibHttpSourceAdapter(
        _make_request(),
        config=config,
        transport=httpx.MockTransport(_handler),
    ).execute(_make_command())
    # First request: no Cookie header.
    assert "cookie" not in captured_headers[0]
    # Second: jar replays the session cookie.
    assert captured_headers[1].get("cookie") == "session=abc"


def test_cookie_jar_isolated_across_runs() -> None:
    jar = InMemoryCookieJar()

    def _set_cookie_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"<html>x</html>",
            headers={"set-cookie": "session=abc", "content-type": "text/html"},
        )

    StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(cookie_jar=jar, run_ref="run:a"),
        transport=httpx.MockTransport(_set_cookie_handler),
    ).execute(_make_command())

    captured_headers: list[dict[str, str]] = []

    def _capture_handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        return httpx.Response(200, content=b"<html>x</html>", headers={"content-type": "text/html"})

    StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(cookie_jar=jar, run_ref="run:b"),
        transport=httpx.MockTransport(_capture_handler),
    ).execute(_make_command())

    # run:b should NOT see run:a's cookies.
    assert "cookie" not in captured_headers[0]


# -- Boundary acceptance -----------------------------------------------


def test_default_config_uses_noop_cache_and_jar() -> None:
    config = HttpClientConfig()
    from veracrawl.ports.conditional_cache import NoopConditionalCache
    from veracrawl.ports.cookie_jar import NoopCookieJar

    assert isinstance(config.conditional_cache, NoopConditionalCache)
    assert isinstance(config.cookie_jar, NoopCookieJar)


def test_existing_call_sites_unaffected_by_step_1_5_defaults() -> None:
    """A no-config adapter still completes a fetch with a populated
    NetworkClientResult and at least one attempt evidence."""

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    assert result.body_text == "<html>ok</html>"
    assert len(result.attempt_evidences) == 1
