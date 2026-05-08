"""Unit tests for ``InMemoryCookieJar``.

design.md §4 Phase 1 step 1.5: per-run / per-origin cookie store.
Behaviors:
* Set-Cookie acceptance + replay on subsequent request to same origin
* per-run isolation: cookie set under run:a not sent under run:b
* per-origin isolation: cookie set on a.test not sent to b.test
* expiry handling: Max-Age + Expires
* Path matching (RFC 6265 §5.4)
* Secure attribute respected (https only)
* clear_run drops cookies
* Default-port normalization (80 / 443)
"""

from __future__ import annotations

from veracrawl.adapters.network.in_memory_cookie_jar import InMemoryCookieJar


def test_round_trip_set_cookie_then_replay() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Path=/",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/p")
    assert cookies == {"session": "abc"}


def test_per_run_isolation() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:a",
        url="https://example.test/",
        set_cookie_value="session=secret-a",
    )
    cookies_a = jar.cookies_for(run_ref="run:a", url="https://example.test/")
    cookies_b = jar.cookies_for(run_ref="run:b", url="https://example.test/")
    assert cookies_a == {"session": "secret-a"}
    assert cookies_b == {}


def test_per_origin_isolation() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://a.test/",
        set_cookie_value="session=secret-a",
    )
    a = jar.cookies_for(run_ref="run:r", url="https://a.test/")
    b = jar.cookies_for(run_ref="run:r", url="https://b.test/")
    assert a == {"session": "secret-a"}
    assert b == {}


def test_scheme_difference_is_different_origin() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=https-only",
    )
    https_cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    http_cookies = jar.cookies_for(run_ref="run:r", url="http://example.test/")
    assert https_cookies == {"session": "https-only"}
    assert http_cookies == {}


def test_secure_cookie_from_http_response_ignored() -> None:
    """Iter-2 critical: RFC 6265bis — Set-Cookie with Secure must
    be ignored when received over an insecure (non-HTTPS) channel.
    Otherwise an HTTP response can plant credentials the jar
    later trusts on HTTPS requests."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="http://example.test/",
        set_cookie_value="session=secret; Secure",
    )
    cookies_http = jar.cookies_for(run_ref="run:r", url="http://example.test/")
    assert cookies_http == {}
    snapshot = jar.cookies_in_jar(run_ref="run:r")
    assert snapshot.cookies == []


def test_oversized_cookie_value_dropped() -> None:
    """Iter-2 important #4: per-cookie value cap drops oversized
    Set-Cookie at acceptance time."""

    jar = InMemoryCookieJar(max_cookie_value_bytes=10)
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=" + "X" * 100,
    )
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {}


def test_per_bucket_cookie_count_cap() -> None:
    """Iter-2 important #4: per-(run, origin) cookie-count cap
    evicts oldest in insertion order."""

    jar = InMemoryCookieJar(max_cookies_per_bucket=2)
    for i in range(4):
        jar.accept_set_cookie(
            run_ref="run:r",
            url="https://example.test/",
            set_cookie_value=f"c{i}=v{i}",
        )
    snapshot = jar.cookies_in_jar(run_ref="run:r")
    names = sorted(c.name for c in snapshot.cookies)
    # Only the last 2 survive (c2 + c3).
    assert names == ["c2", "c3"]


def test_jar_init_validation() -> None:
    import pytest

    with pytest.raises(ValueError):
        InMemoryCookieJar(max_cookies_per_bucket=0)
    with pytest.raises(ValueError):
        InMemoryCookieJar(max_cookie_value_bytes=0)


def test_secure_attribute_blocks_http() -> None:
    """Codex iter-3: ``Secure`` cookie set over HTTPS must NOT ship on
    a subsequent HTTP request to the same host (different origin
    anyway in our exact-origin-scope, but verify the Secure
    request-side check too)."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Secure",
    )
    https_cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert https_cookies == {"session": "abc"}
    # Direct HTTP request — different origin (exact-origin scope),
    # so jar returns nothing. Even if origins were merged, the
    # Secure attribute on the request-side check would block.
    http_cookies = jar.cookies_for(run_ref="run:r", url="http://example.test/")
    assert http_cookies == {}


def test_max_age_zero_clears_cookie_immediately() -> None:
    fake_time = [1_000_000.0]

    def clock() -> float:
        return fake_time[0]

    jar = InMemoryCookieJar(clock_fn=clock)
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Max-Age=0",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {}


def test_expires_attribute_future_keeps_cookie() -> None:
    """Codex iter-5 important: Expires attribute coverage."""

    fake_time = [1_000_000.0]

    def clock() -> float:
        return fake_time[0]

    jar = InMemoryCookieJar(clock_fn=clock)
    # 2099 — far future relative to the fake clock at epoch 1M.
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Expires=Wed, 21 Oct 2099 07:28:00 GMT",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {"session": "abc"}


def test_expires_attribute_past_clears_cookie() -> None:
    fake_time = [4_000_000_000.0]  # ~2096

    def clock() -> float:
        return fake_time[0]

    jar = InMemoryCookieJar(clock_fn=clock)
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Expires=Wed, 21 Oct 1990 07:28:00 GMT",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {}


def test_expires_invalid_falls_back_to_session() -> None:
    """Malformed Expires → cookie treated as session (no expiry)."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Expires=NOT_A_DATE",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {"session": "abc"}


def test_max_age_zero_deletes_existing_cookie() -> None:
    """Codex iter-5 important: an existing cookie should be removed
    when a later Set-Cookie for the same (name, path) carries
    Max-Age=0 (the spec deletion mechanism)."""

    fake_time = [1_000_000.0]

    def clock() -> float:
        return fake_time[0]

    jar = InMemoryCookieJar(clock_fn=clock)
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=v1; Path=/",
    )
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {"session": "v1"}
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=v1; Path=/; Max-Age=0",
    )
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {}


def test_max_age_positive_then_expires() -> None:
    fake_time = [1_000_000.0]

    def clock() -> float:
        return fake_time[0]

    jar = InMemoryCookieJar(clock_fn=clock)
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Max-Age=10",
    )
    # Within window.
    fake_time[0] = 1_000_005.0
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {"session": "abc"}
    # After window.
    fake_time[0] = 1_000_011.0
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {}


def test_default_path_is_directory_per_rfc_6265() -> None:
    """Iter-1 important #2: cookie set by ``/admin/login`` without
    a Path attribute defaults to the *directory* ``/admin``, not
    the request path. The cookie should match
    ``/admin/dashboard``."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/admin/login",
        set_cookie_value="session=abc",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/admin/dashboard")
    assert cookies == {"session": "abc"}


def test_default_path_for_root_request_is_root() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/anywhere")
    assert cookies == {"session": "abc"}


def test_default_path_for_single_segment_request_is_root() -> None:
    """``/login`` has a single ``/`` (the leading one) so default
    path falls back to ``/``."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/login",
        set_cookie_value="session=abc",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/dashboard")
    assert cookies == {"session": "abc"}


def test_invalid_path_attribute_falls_back_to_default() -> None:
    """Iter-1 important #3: ``Path=admin`` (no leading ``/``) is
    invalid and must fall back to the default-path."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/admin/login",
        set_cookie_value="session=abc; Path=admin",  # no leading /
    )
    # Default-path is ``/admin`` (request directory).
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/admin/dashboard")
    assert cookies == {"session": "abc"}
    # Outside the default-path scope, no cookie.
    outside = jar.cookies_for(run_ref="run:r", url="https://example.test/public")
    assert outside == {}


def test_empty_path_attribute_falls_back_to_default() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/admin/login",
        set_cookie_value="session=abc; Path=",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/admin/dashboard")
    assert cookies == {"session": "abc"}


def test_path_matching_root_cookie_sent_everywhere() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Path=/",
    )
    deep = jar.cookies_for(run_ref="run:r", url="https://example.test/a/b/c")
    assert deep == {"session": "abc"}


def test_path_matching_scoped_cookie() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/admin/",
        set_cookie_value="csrf=tok; Path=/admin",
    )
    inside = jar.cookies_for(run_ref="run:r", url="https://example.test/admin/users")
    outside = jar.cookies_for(run_ref="run:r", url="https://example.test/public/x")
    assert inside == {"csrf": "tok"}
    assert outside == {}


def test_replace_cookie_same_name_path() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=v1; Path=/",
    )
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=v2; Path=/",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {"session": "v2"}


def test_clear_run_drops_only_run_cookies() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:a",
        url="https://example.test/",
        set_cookie_value="session=A",
    )
    jar.accept_set_cookie(
        run_ref="run:b",
        url="https://example.test/",
        set_cookie_value="session=B",
    )
    jar.clear_run(run_ref="run:a")
    a = jar.cookies_for(run_ref="run:a", url="https://example.test/")
    b = jar.cookies_for(run_ref="run:b", url="https://example.test/")
    assert a == {}
    assert b == {"session": "B"}


def test_default_port_normalization() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",  # default :443
        set_cookie_value="session=abc",
    )
    explicit = jar.cookies_for(
        run_ref="run:r",
        url="https://example.test:443/",
    )
    assert explicit == {"session": "abc"}


def test_non_default_port_is_distinct_origin() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test:8443/",
        set_cookie_value="session=secret",
    )
    custom_port = jar.cookies_for(run_ref="run:r", url="https://example.test:8443/")
    default_port = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert custom_port == {"session": "secret"}
    assert default_port == {}


def test_malformed_set_cookie_logged_and_dropped() -> None:
    jar = InMemoryCookieJar()
    # http.cookies.SimpleCookie.load is fairly forgiving but
    # unparseable values should not crash the jar.
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="\x00garbage",
    )
    cookies = jar.cookies_for(run_ref="run:r", url="https://example.test/")
    assert cookies == {}


def test_cookies_in_jar_returns_snapshot_for_run() -> None:
    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="a=1",
    )
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://other.test/",
        set_cookie_value="b=2",
    )
    snapshot = jar.cookies_in_jar(run_ref="run:r")
    names = {c.name for c in snapshot.cookies}
    assert names == {"a", "b"}


def test_cookies_in_jar_default_redacts_values() -> None:
    """Codex iter-4 important: default snapshot redacts cookie
    values so observability surfaces don't leak credentials."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=SECRET_VALUE",
    )
    snapshot = jar.cookies_in_jar(run_ref="run:r")
    assert all(c.value == "<redacted>" for c in snapshot.cookies)


def test_cookies_in_jar_include_values_opt_in() -> None:
    """Tests / debug paths can opt in to raw values."""

    jar = InMemoryCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=RAW_VALUE",
    )
    snapshot = jar.cookies_in_jar(run_ref="run:r", include_values=True)
    values = {c.value for c in snapshot.cookies}
    assert "RAW_VALUE" in values


def test_no_cookie_for_invalid_url() -> None:
    jar = InMemoryCookieJar()
    assert jar.cookies_for(run_ref="run:r", url="ftp://example.test/") == {}
